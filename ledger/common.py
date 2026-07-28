"""Shared layer: configuration, registry parsing, identifier normalisation.

共享层：配置加载、登记册解析、标识归一。

The registry declares three tiers (cited / candidates / library) plus an
optional note vault. Nothing about their internal format is hard-coded here —
see ``examples/registry.example.yaml``. This module is read-only: it never
writes to any registry.

登记册声明三层（cited / candidates / library）与可选笔记库。它们的内部格式
不在此硬编码，见 ``examples/registry.example.yaml``。本模块只读，
绝不写入任何登记册。
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

# Repository root = parent of the package directory.
ROOT = Path(__file__).resolve().parents[1]

DEFAULT_KEY_PATTERN = r"`([a-zA-Z][a-zA-Z0-9]*\d{4}[a-zA-Z0-9]*)`"


def utf8_stdout() -> None:
    """Windows consoles default to a legacy code page; CJK and Greek letters in
    output would raise UnicodeEncodeError without this."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else ROOT / "config.json"
    if not p.exists():
        raise SystemExit(
            f"Missing {p}\n"
            f"Copy config.example.json to config.json and fill in your Zotero "
            f"API key.\n"
            f"未找到配置。请把 config.example.json 复制为 config.json 并填入 "
            f"Zotero API key。"
        )
    cfg = json.loads(p.read_text(encoding="utf-8"))
    cfg["_root"] = ROOT
    return cfg


def _resolve(base: Path, raw: str) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else (base / p)


def load_yaml(path: Path) -> dict:
    import yaml

    if not path.exists():
        raise SystemExit(
            f"Missing {path.name}\n"
            f"Copy the matching template from examples/ and edit it.\n"
            f"未找到该文件。请从 examples/ 复制对应模板后修改。"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_registry(cfg: dict) -> dict:
    return load_yaml(_resolve(ROOT, cfg.get("registry", "registry.yaml")))


def load_collections(cfg: dict) -> dict:
    return load_yaml(_resolve(ROOT, cfg.get("collections", "collections.yaml")))


def out_dir(cfg: dict, which: str) -> Path:
    d = _resolve(ROOT, cfg.get("paths", {}).get(which, which))
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------
# Identifier normalisation
# --------------------------------------------------------------------------

_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+")


def norm_doi(raw) -> str | None:
    """Strip any https://doi.org/ prefix and trailing punctuation; lowercase.
    DOIs are case-insensitive, so lowercasing is safe and makes them comparable.
    """
    if not raw:
        return None
    s = urllib.parse.unquote(str(raw).strip())
    m = _DOI_RE.search(s)
    return m.group(0).rstrip(".,;)]").lower() if m else None


_GREEK = (("π", "pi"), ("μ", "mu"), ("α", "alpha"),
          ("β", "beta"), ("θ", "theta"), ("τ", "tau"),
          ("δ", "delta"), ("ω", "omega"), ("λ", "lambda"))


def norm_title(s: str | None) -> str:
    """Normalise a title for cross-registry matching: strip LaTeX math, transcribe
    Greek letters, drop everything that is not alphanumeric.

    Titles are written inconsistently across a bib file, a notes table and a
    metadata API. Plain string comparison silently misses matches — in practice
    one paper was repeatedly reported as new because its title appeared once
    with a LaTeX-escaped Greek letter and once with the letter itself.
    """
    if not s:
        return ""
    t = s.lower()
    t = re.sub(r"\$?\\+([a-z]+)\$?", r"\1", t)
    for g, a in _GREEK:
        t = t.replace(g, a)
    return re.sub(r"[^a-z0-9]+", "", t)


def titles_match(a: str, b: str, ratio: float = 0.75) -> bool:
    """Compare two normalised titles.

    Containment counts only when the lengths are comparable. Without the ratio
    guard a short title is swallowed by a longer one that happens to contain it —
    a generic title like "series elastic actuators" would otherwise match any
    paper whose title embeds that phrase, producing a false hit.
    """
    if not a or not b:
        return False
    if a == b:
        return True
    lo, hi = sorted((a, b), key=len)
    return len(lo) / len(hi) >= ratio and lo in hi


# --------------------------------------------------------------------------
# Tier parsers
# --------------------------------------------------------------------------

_BIB_ENTRY_RE = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)


def _section(text: str, heading: str | None) -> str:
    """Return the body of the Markdown section whose heading contains *heading*.

    Matches any heading level and stops at the next heading of the same or a
    shallower level. Returns the whole document when *heading* is falsy.
    """
    if not heading:
        return text
    m = re.search(rf"^(#{{1,6}})\s*.*{re.escape(heading)}.*$", text,
                  re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    level = len(m.group(1))
    rest = text[m.end():]
    nxt = re.search(rf"^#{{1,{level}}}\s", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def parse_bibtex(path: Path) -> dict[str, dict]:
    """-> {key: {entrytype, doi}}.

    Deliberately not a full BibTeX parser: only entry keys and DOIs are needed,
    and a regex tolerates the formatting variety real .bib files contain.
    """
    if not path.exists():
        return {}
    txt = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, dict] = {}
    for m in _BIB_ENTRY_RE.finditer(txt):
        nxt = _BIB_ENTRY_RE.search(txt, m.end())
        body = txt[m.end(): nxt.start() if nxt else len(txt)]
        doi = re.search(r"doi\s*=\s*[{\"]([^}\"]+)", body, re.IGNORECASE)
        out[m.group(2)] = {
            "entrytype": m.group(1).lower(),
            "doi": norm_doi(doi.group(1)) if doi else None,
        }
    return out


def parse_markdown_table(path: Path, key_column: int = 2,
                         heading: str | None = None,
                         columns: dict | None = None) -> dict[str, dict]:
    """Read a pipe table and take *key_column* (1-based) as the identifier."""
    if not path.exists():
        return {}
    body = _section(path.read_text(encoding="utf-8", errors="replace"), heading)
    labels = {int(k): v for k, v in (columns or {}).items()}
    out: dict[str, dict] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < key_column:
            continue
        key = cells[key_column - 1].strip("`").strip()
        # Skip header and separator rows.
        if not key or set(key) <= set("-: ") or key.lower() in ("bibkey", "key"):
            continue
        if not re.match(r"^[A-Za-z][A-Za-z0-9_.:-]*$", key):
            continue
        out[key] = {labels[i]: cells[i - 1] for i in labels if i <= len(cells)}
    return out


def parse_inline_keys(path: Path, heading: str | None = None,
                      pattern: str | None = None) -> set[str]:
    """Collect identifiers matching *pattern* from a Markdown file or section."""
    if not path.exists():
        return set()
    body = _section(path.read_text(encoding="utf-8", errors="replace"), heading)
    return set(re.findall(pattern or DEFAULT_KEY_PATTERN, body))


def load_tier(reg: dict, name: str) -> tuple[dict[str, dict], str]:
    """Parse one declared tier. -> (entries, human-readable source description).

    An undeclared tier yields an empty mapping rather than raising, so a registry
    that keeps no candidate pool still reconciles cleanly.
    """
    spec = (reg.get("tiers") or {}).get(name)
    if not spec:
        return {}, "(not declared)"
    path = _resolve(ROOT, spec["path"])
    kind = spec.get("type", "bibtex")
    if kind == "bibtex":
        return parse_bibtex(path), f"{path.name} (bibtex)"
    if kind == "markdown_table":
        return (parse_markdown_table(path, int(spec.get("key_column", 2)),
                                     spec.get("section"), spec.get("columns")),
                f"{path.name} (markdown table)")
    if kind == "markdown_inline_keys":
        keys = parse_inline_keys(path, spec.get("section"),
                                 spec.get("key_pattern"))
        return {k: {} for k in keys}, f"{path.name} (inline keys)"
    raise SystemExit(f"Unknown tier type for '{name}': {kind}")


def load_aliases(reg: dict) -> dict[str, str]:
    """manuscript-side key -> library-side key."""
    return dict(reg.get("aliases") or {})


# --------------------------------------------------------------------------
# Note vault
# --------------------------------------------------------------------------

def vault_notes(reg: dict) -> dict[str, dict]:
    """-> {bibkey: {path, title, doi, zotero_key, ...}} from note frontmatter."""
    raw = (reg.get("vault") or {}).get("sources_dir")
    if not raw:
        return {}
    d = _resolve(ROOT, raw)
    if not d.exists():
        return {}
    out: dict[str, dict] = {}
    for p in sorted(d.glob("*.md")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        fm = re.match(r"^---\r?\n(.*?)\r?\n---", txt, re.DOTALL)
        meta: dict[str, str] = {}
        if fm:
            for line in fm.group(1).splitlines():
                kv = re.match(r'^(\w+)\s*:\s*"?([^"\n]*?)"?\s*$', line)
                if kv:
                    meta[kv.group(1)] = kv.group(2).strip()
        meta.setdefault("bibkey", p.stem)
        meta["path"] = str(p)
        out[meta["bibkey"]] = meta
    return out


# --------------------------------------------------------------------------
# Zotero: read via the local API (no key needed), write via the Web API
# --------------------------------------------------------------------------

_CITEKEY_RE = re.compile(r"^\s*Citation Key\s*:\s*(\S+)",
                         re.MULTILINE | re.IGNORECASE)


def _zot_local(cfg: dict) -> tuple[str, str]:
    return cfg["zotero"]["local_api"].rstrip("/"), cfg["zotero"]["library_id"]


def zotero_items(cfg: dict, page: int = 100) -> list[dict]:
    """All top-level items (attachments, notes and annotations excluded)."""
    import requests

    base, lib = _zot_local(cfg)
    out, start = [], 0
    while True:
        r = requests.get(f"{base}/users/{lib}/items/top",
                         params={"limit": page, "start": start}, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page:
            break
        start += page
    return out


def zotero_index(cfg: dict) -> dict:
    """-> {by_citekey, by_doi, all}.

    ``by_citekey`` is keyed on the pinned Better BibTeX citation key found in an
    item's Extra field. That pin is what ties a Zotero item to the identifier
    your manuscript actually uses.
    """
    items = zotero_items(cfg)
    by_ck, by_doi = {}, {}
    for it in items:
        d = it.get("data", {})
        m = _CITEKEY_RE.search(d.get("extra") or "")
        if m:
            by_ck[m.group(1)] = it
        doi = norm_doi(d.get("DOI")) or norm_doi(d.get("url"))
        if doi:
            by_doi.setdefault(doi, it)
    return {"by_citekey": by_ck, "by_doi": by_doi, "all": items}


def zotero_children(cfg: dict, key: str) -> list[dict]:
    import requests

    base, lib = _zot_local(cfg)
    r = requests.get(f"{base}/users/{lib}/items/{key}/children", timeout=30)
    return r.json() if r.ok else []


def zotero_annotations(cfg: dict, parent_key: str) -> list[dict]:
    """Highlights, underlines and notes you made in the Zotero PDF reader.

    This is the one channel that carries *your* reading judgement into the
    pipeline, rather than a model's guess at what matters.
    """
    anns = []
    for k in zotero_children(cfg, parent_key):
        d = k.get("data", {})
        if d.get("itemType") == "annotation":
            anns.append(d)
        elif d.get("itemType") == "attachment":
            anns += [c["data"] for c in zotero_children(cfg, d["key"])
                     if c.get("data", {}).get("itemType") == "annotation"]
    return anns


def zotero_pdf_path(cfg: dict, parent_key: str) -> Path | None:
    """Locate an item's PDF on disk (stored attachment or linked file)."""
    storage = Path(cfg["zotero"]["data_dir"]) / "storage"
    for k in zotero_children(cfg, parent_key):
        d = k.get("data", {})
        if d.get("itemType") != "attachment":
            continue
        raw = d.get("path") or ""
        if raw.startswith("attachments:"):
            cand = Path(cfg["zotero"].get("linked_base", "")) / raw.split(":", 1)[1]
            if cand.exists():
                return cand
        elif raw:
            cand = Path(raw)
            if cand.is_absolute() and cand.exists():
                return cand
        folder = storage / d["key"]
        if folder.is_dir():
            pdfs = list(folder.glob("*.pdf"))
            if pdfs:
                return pdfs[0]
    return None


# --------------------------------------------------------------------------
# HTTP with backoff
# --------------------------------------------------------------------------

def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             tries: int = 4, timeout: int = 30):
    """GET with exponential backoff.

    The anonymous Semantic Scholar quota returns 429 intermittently; backing off
    is required rather than hammering. 404 is a real answer, not an error.
    """
    import requests

    delay, last = 1.0, None
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, headers=headers or {},
                             timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(delay)
                delay *= 2
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = repr(e)
            time.sleep(delay)
            delay *= 2
    print(f"  ! giving up on {url} ({last})", file=sys.stderr)
    return None
