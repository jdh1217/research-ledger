"""Stages 4-5 — file into Zotero (write) and pull reading material out (read).

Read-only subcommands (no API key needed; they use the local Zotero API):

    python -m ledger.zot collections              list every collection and key
    python -m ledger.zot find --doi 10.1000/x     locate an item
    python -m ledger.zot annotations <itemKey>    export your highlights
    python -m ledger.zot pdf  <itemKey>           print the PDF path on disk
    python -m ledger.zot text <itemKey> [--pages 1-12] [-o out.txt]

Write subcommands (need the Zotero Web API key in config.json):

    python -m ledger.zot create --doi 10.1000/x --collection passivity
                                --bibkey author2020topic [--dry-run]
    python -m ledger.zot attach <itemKey> path/to.pdf     link, do not upload
    python -m ledger.zot pin    <itemKey> --bibkey author2020topic

Citation-key discipline — the foundation of the whole toolkit:

Pick your own semantic keys and pin them. Write the key into the item Extra field
as ``Citation Key: yourkey``; Better BibTeX treats a pinned key as final and never
recomputes it. Do NOT let a bibliography exporter overwrite the .bib your
manuscript compiles against: an auto-generated key scheme will silently rename
entries and break every citation you have already written.

citekey 纪律是整套工具的地基：自己定语义键并 pin 进 Zotero 条目的 Extra 字段
（写成 ``Citation Key: yourkey``），Better BibTeX 会视为最终值、永不重算。
绝不要让导出器覆盖稿件所用的 .bib——自动生成的键会静默改名，
把你已经写好的每一处引用都弄坏。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import common as C

CITEKEY_LINE = "Citation Key: {}"


def _zot(cfg: dict):
    from pyzotero import zotero

    key = (cfg["zotero"].get("api_key") or "").strip()
    if not key or key.startswith("PUT_YOUR"):
        raise SystemExit(
            "zotero.api_key in config.json is still a placeholder.\n"
            "Create one at https://www.zotero.org/settings/keys with "
            "'Allow library access' and 'Allow write access'.\n"
            "config.json is gitignored, so the key stays local.")
    return zotero.Zotero(cfg["zotero"]["library_id"],
                         cfg["zotero"]["library_type"], key)


def _collection(cfg: dict, alias_or_key: str) -> tuple[str, str]:
    cols = C.load_collections(cfg).get("collections") or {}
    if alias_or_key in cols:
        e = cols[alias_or_key]
        return e["key"], e["path"]
    for e in cols.values():
        if e["key"] == alias_or_key:
            return e["key"], e["path"]
    listing = "\n  ".join(f"{a:<18} {e['path']}" for a, e in cols.items())
    raise SystemExit(f"Unknown collection alias: {alias_or_key}\n"
                     f"Available:\n  {listing}")


# ------------------------------------------------------------------ read

def cmd_collections(cfg, a):
    import requests

    base = cfg["zotero"]["local_api"].rstrip("/")
    lib = cfg["zotero"]["library_id"]
    data = requests.get(f"{base}/users/{lib}/collections",
                        params={"limit": 200}, timeout=30).json()
    byk = {c["key"]: c["data"] for c in data}

    def path(k):
        parts = []
        while k:
            parts.append(byk[k]["name"])
            k = byk[k].get("parentCollection") or None
        return "/".join(reversed(parts))

    known = {e["key"]: alias for alias, e
             in (C.load_collections(cfg).get("collections") or {}).items()}
    for c in sorted(data, key=lambda c: path(c["key"])):
        k = c["key"]
        print(f"{k}  {known.get(k, '-'):<18} {path(k)}  "
              f"({c['meta'].get('numItems', 0)})")


def cmd_find(cfg, a):
    idx = C.zotero_index(cfg)
    it = idx["by_doi"].get(C.norm_doi(a.doi)) if a.doi else None
    if a.bibkey:
        it = idx["by_citekey"].get(a.bibkey) or it
    if not it:
        print("Not found.")
        return
    d = it["data"]
    print(f"key      : {it['key']}")
    print(f"title    : {d.get('title', '')}")
    print(f"itemType : {d.get('itemType', '')}")
    print(f"DOI      : {d.get('DOI', '')}")
    extra = (d.get("extra") or "").strip()
    print(f"extra    : {extra or '(empty - no pinned citation key)'}")


def cmd_annotations(cfg, a):
    anns = C.zotero_annotations(cfg, a.item)
    if not anns:
        print("No annotations on this item.")
        return
    print(f"## Annotation evidence ({len(anns)})\n")
    for x in sorted(anns, key=lambda x: str(x.get("annotationPageLabel") or "")):
        page = x.get("annotationPageLabel") or "?"
        kind = x.get("annotationType", "")
        text = (x.get("annotationText") or "").strip().replace("\n", " ")
        note = (x.get("annotationComment") or "").strip().replace("\n", " ")
        if text:
            print(f"- **p.{page}** ({kind}) > {text}")
        if note:
            print(f"  - comment: {note}")


def cmd_pdf(cfg, a):
    p = C.zotero_pdf_path(cfg, a.item)
    print(p if p else "No PDF attachment found.")


def cmd_text(cfg, a):
    """Extract text with PyMuPDF.

    This is the only place the AGPL-licensed dependency is touched; swap the
    import if that licence does not suit your use.
    """
    import fitz

    p = C.zotero_pdf_path(cfg, a.item)
    if not p:
        raise SystemExit("No PDF attachment found.")
    doc = fitz.open(p)
    lo, hi = 0, doc.page_count - 1
    if a.pages:
        parts = a.pages.split("-")
        lo, hi = int(parts[0]) - 1, int(parts[-1]) - 1
    lo, hi = max(0, lo), min(hi, doc.page_count - 1)
    text = "".join(f"\n===== p.{i + 1} =====\n" + doc[i].get_text()
                   for i in range(lo, hi + 1))
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"{doc.page_count} pages; extracted p.{lo + 1}-{hi + 1}, "
              f"{len(text)} chars -> {a.out}")
    else:
        print(text)


# ------------------------------------------------------------------ write

def cmd_create(cfg, a):
    """Fetch metadata by DOI, create the item in a named collection, pin the key."""
    from . import discover

    doi = C.norm_doi(a.doi)
    if not doi:
        raise SystemExit(f"Could not parse a DOI from: {a.doi}")

    try:
        idx = C.zotero_index(cfg)
    except Exception:
        idx = {"by_doi": {}}
    if doi in idx["by_doi"] and not a.force:
        it = idx["by_doi"][doi]
        raise SystemExit(
            f"That DOI is already in the library: {it['key']}\n"
            f"  {it['data'].get('title', '')}\n"
            f"To add a pinned key instead: "
            f"python -m ledger.zot pin {it['key']} --bibkey {a.bibkey}\n"
            f"To create a duplicate anyway, pass --force.")

    rows = discover.merge([discover.s2_doi(cfg, doi),
                           discover.crossref_search(cfg, doi, 3)])
    rec = next((r for r in rows if r["doi"] == doi), None)
    if not rec:
        raise SystemExit("No source returned metadata for that DOI. Check it.")

    ckey, cpath = _collection(cfg, a.collection)
    itype = a.item_type or discover.guess_item_type(rec["venue"])

    # A dry run must not require an API key, so connect only when writing.
    z = None if a.dry_run else _zot(cfg)
    tmpl = z.item_template(itype) if z else {"itemType": itype}
    tmpl["title"] = rec["title"]
    tmpl["creators"] = [
        {"creatorType": "author",
         "firstName": " ".join(n.split()[:-1]), "lastName": n.split()[-1]}
        for n in rec["authors"] if n.strip()
    ]
    tmpl["date"] = str(rec["year"] or "")
    tmpl["DOI"] = doi
    if itype == "journalArticle":
        tmpl["publicationTitle"] = rec["venue"]
    else:
        tmpl["proceedingsTitle"] = rec["venue"]
    if a.bibkey:
        tmpl["extra"] = CITEKEY_LINE.format(a.bibkey)
    tmpl["tags"] = [{"tag": t} for t in (a.tags or [f"{cfg['project']}/to-read"])]
    tmpl["collections"] = [ckey]

    if a.dry_run:
        print("--dry-run, nothing written. Would create:")
        for k in ("itemType", "title", "date", "DOI", "extra", "collections",
                  "tags"):
            print(f"  {k:<16} {tmpl.get(k)}")
        print(f"  collection       {cpath}")
        print(f"  open-access PDF  {rec['oa_pdf'] or 'none (closed access)'}")
        return

    resp = z.create_items([tmpl])
    ok = resp.get("successful") or {}
    if not ok:
        raise SystemExit(f"Creation failed: {resp}")
    new = list(ok.values())[0]
    print(f"Created {new['key']}  {rec['title'][:60]}")
    print(f"  collection  {cpath}")
    print(f"  citekey     {a.bibkey or '(not pinned)'}")
    print(f"  OA PDF      {rec['oa_pdf'] or 'none - closed access'}")


def cmd_attach(cfg, a):
    """Attach a local PDF.

    Default mode is ``linked_file``: Zotero stores only a path, the file stays on
    your disk, nothing is uploaded, and your storage quota is untouched. The
    trade-off is that the link breaks if the file moves; the linked-attachment
    base directory in config.json mitigates that.

    Pass ``--copy`` for an imported (uploaded) attachment, which does consume
    quota.
    """
    pdf = Path(a.pdf).resolve()
    if not pdf.exists():
        raise SystemExit(f"No such file: {pdf}")

    base = (cfg["zotero"].get("linked_base") or "").strip()
    stored = str(pdf)
    if not a.copy and base:
        try:
            stored = "attachments:" + pdf.relative_to(Path(base)).as_posix()
        except ValueError:
            print(f"  ! {pdf} is outside the linked base directory {base}; "
                  f"storing an absolute path, which is less portable.")

    att = {
        "itemType": "attachment",
        "parentItem": a.item,
        "linkMode": "imported_file" if a.copy else "linked_file",
        "title": a.title or pdf.name,
        "accessDate": "",
        "url": "",
        "note": "",
        "tags": [],
        "contentType": "application/pdf",
        "charset": "",
        "path": stored,
    }
    if a.dry_run:
        print("--dry-run, nothing written. Would attach:")
        for k in ("linkMode", "title", "path", "parentItem"):
            print(f"  {k:<12} {att[k]}")
        return

    resp = _zot(cfg).create_items([att])
    ok = resp.get("successful") or {}
    if not ok:
        raise SystemExit(
            f"Attachment failed: {resp}\n"
            "If the API rejects linkMode, add the file from the Zotero desktop "
            "app instead: right-click the item, Add Attachment, "
            "Attach Link to File.")
    mode = "copy" if a.copy else "link"
    print(f"Attached {list(ok.values())[0]['key']} ({mode}) -> {stored}")


def cmd_pin(cfg, a):
    """Write a pinned citation key into an existing item, leaving all else alone."""
    z = _zot(cfg)
    d = z.item(a.item)["data"]
    lines = [ln for ln in (d.get("extra") or "").splitlines()
             if not ln.lower().startswith("citation key")]
    lines.insert(0, CITEKEY_LINE.format(a.bibkey))
    d["extra"] = "\n".join(lines).strip()
    if a.dry_run:
        print(f"--dry-run. Extra of {a.item} would become:\n{d['extra']}")
        return
    z.update_item(d)
    print(f"{a.item} -> Citation Key: {a.bibkey}")


def main(argv=None) -> None:
    C.utf8_stdout()
    ap = argparse.ArgumentParser(
        prog="python -m ledger.zot",
        description="File items into Zotero and pull reading material out")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("collections", help="list every collection and its key")

    p = sub.add_parser("find", help="locate an item by DOI or pinned key")
    p.add_argument("--doi")
    p.add_argument("--bibkey")

    p = sub.add_parser("annotations", help="export annotations as Markdown")
    p.add_argument("item")

    p = sub.add_parser("pdf", help="print the PDF path on disk")
    p.add_argument("item")

    p = sub.add_parser("text", help="extract PDF text")
    p.add_argument("item")
    p.add_argument("--pages", help="e.g. 1-12")
    p.add_argument("-o", "--out")

    p = sub.add_parser("create", help="create an item in a named collection")
    p.add_argument("--doi", required=True)
    p.add_argument("--collection", required=True,
                   help="alias from collections.yaml")
    p.add_argument("--bibkey", help="semantic citation key to pin into Extra")
    p.add_argument("--item-type",
                   help="journalArticle or conferencePaper; guessed from venue")
    p.add_argument("--tags", nargs="*")
    p.add_argument("--force", action="store_true",
                   help="create even if the DOI is already present")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("attach", help="attach a local PDF as a linked file")
    p.add_argument("item", help="parent item key")
    p.add_argument("pdf")
    p.add_argument("--title")
    p.add_argument("--copy", action="store_true",
                   help="import a copy instead of linking (consumes quota)")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("pin", help="write a pinned citation key")
    p.add_argument("item")
    p.add_argument("--bibkey", required=True)
    p.add_argument("--dry-run", action="store_true")

    a = ap.parse_args(argv)
    cfg = C.load_config(a.config)
    {
        "collections": cmd_collections, "find": cmd_find,
        "annotations": cmd_annotations, "pdf": cmd_pdf, "text": cmd_text,
        "create": cmd_create, "attach": cmd_attach, "pin": cmd_pin,
    }[a.cmd](cfg, a)


if __name__ == "__main__":
    main()
