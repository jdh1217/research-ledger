"""Stage 2 — screening. Compare candidates against what you already have.

    python -m ledger.screen runs/candidates_search_20260101-120000.json
    python -m ledger.screen <file>.json --only NEW
    python -m ledger.screen --doi 10.1000/example

Status, first match wins:

    IN_CITED    already in your citation set        -> nothing to do
    IN_LIBRARY  already in your reading library     -> read; not cited (fine)
    IN_VAULT    a note exists but no library entry  -> note ran ahead
    IN_ZOTERO   in the reference manager only       -> filed but not logged
    NEW         in none of the above                -> the only rows worth acquiring

Only NEW rows should proceed to acquisition. Everything else you already own in
some form, and re-downloading or re-reading it is waste.

只有 NEW 才值得进入取全文环节；其余你已经以某种形式拥有，重下重读是浪费。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import common as C

ORDER = ["IN_CITED", "IN_LIBRARY", "IN_VAULT", "IN_ZOTERO", "NEW"]


def build_index(cfg: dict, use_zotero: bool = True) -> dict:
    reg = C.load_registry(cfg)
    cited, _ = C.load_tier(reg, "cited")
    library, _ = C.load_tier(reg, "library")
    vault = C.vault_notes(reg)
    alias = C.load_aliases(reg)

    zot = {"by_citekey": {}, "by_doi": {}, "all": []}
    if use_zotero:
        try:
            zot = C.zotero_index(cfg)
        except Exception as e:
            print(f"  ! Zotero unreachable, skipping that dimension: {e!r}",
                  file=sys.stderr)

    return {
        "cited": cited,
        "library": library,
        "vault": vault,
        "alias": alias,
        "zot": zot,
        # DOI -> key, for each registry that records DOIs
        "cited_doi": {v["doi"]: k for k, v in cited.items() if v.get("doi")},
        "vault_doi": {C.norm_doi(v.get("doi")): k for k, v in vault.items()
                      if C.norm_doi(v.get("doi"))},
        "vault_title": {k: C.norm_title(v.get("title")) for k, v in vault.items()},
    }


def classify(rec: dict, idx: dict) -> tuple[str, str]:
    """-> (status, matched identifier).

    DOI is the primary join key. Reading libraries kept as Markdown tables
    usually have no DOI column, so a normalised-title comparison against the
    note vault serves as a fallback.
    """
    doi = C.norm_doi(rec.get("doi"))
    title = C.norm_title(rec.get("title"))

    def canon(k: str) -> str:
        return idx["alias"].get(k, k)

    if doi:
        if doi in idx["cited_doi"]:
            return "IN_CITED", idx["cited_doi"][doi]
        if doi in idx["vault_doi"]:
            k = idx["vault_doi"][doi]
            return (("IN_LIBRARY", canon(k)) if canon(k) in idx["library"]
                    else ("IN_VAULT", k))

    if len(title) > 20:
        for k, vt in idx["vault_title"].items():
            if not C.titles_match(title, vt):
                continue
            c = canon(k)
            if c in idx["cited"] or k in idx["cited"]:
                return "IN_CITED", k
            if c in idx["library"]:
                return "IN_LIBRARY", c
            return "IN_VAULT", k

    if doi and doi in idx["zot"]["by_doi"]:
        return "IN_ZOTERO", idx["zot"]["by_doi"][doi]["key"]

    return "NEW", ""


def main(argv=None) -> None:
    C.utf8_stdout()
    ap = argparse.ArgumentParser(
        prog="python -m ledger.screen",
        description="Screen candidates against your registries")
    ap.add_argument("candidates", nargs="?", help="a .json produced by discover")
    ap.add_argument("--doi", help="screen a single DOI instead of a file")
    ap.add_argument("--config")
    ap.add_argument("--only", choices=ORDER, help="show only this status")
    ap.add_argument("--no-zotero", action="store_true")
    ap.add_argument("-o", "--out", help="write the annotated results to a .json")
    a = ap.parse_args(argv)

    cfg = C.load_config(a.config)
    idx = build_index(cfg, use_zotero=not a.no_zotero)

    if a.candidates:
        data = json.loads(Path(a.candidates).read_text(encoding="utf-8"))
        rows = data.get("results", data) if isinstance(data, dict) else data
        header = (data.get("query", a.candidates) if isinstance(data, dict)
                  else a.candidates)
    elif a.doi:
        rows = [{"doi": a.doi, "title": "", "year": None, "authors": [],
                 "venue": ""}]
        header = f"Single DOI: {a.doi}"
    else:
        ap.error("give a candidates file or --doi")
        return

    counts = dict.fromkeys(ORDER, 0)
    for r in rows:
        st, hit = classify(r, idx)
        r["status"], r["status_hit"] = st, hit
        counts[st] += 1

    print(f"{header}  ->  {len(rows)} records")
    print("  " + "  ".join(f"{k}={counts[k]}" for k in ORDER))
    print()

    for r in (x for x in rows if not a.only or x["status"] == a.only):
        tag = f"[{r['ref_no']}]" if r.get("ref_no") else "   "
        hit = f" <- {r['status_hit']}" if r["status_hit"] else ""
        a1 = (r["authors"][0] if r.get("authors") else "?")[:18]
        print(f"{tag:>5} {r['status']:<11}{hit:<24} [{r.get('year') or '????'}] "
              f"{a1:<18} {(r.get('title') or '')[:54]}")

    if a.out:
        Path(a.out).write_text(
            json.dumps({"query": header, "results": rows},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n-> {a.out}")

    if counts["NEW"]:
        print(f"\n{counts['NEW']} record(s) are new. For acquisition:")
        print("  Open Access first — check the oa_pdf field on each record.")
        print("  Closed access — one paper at a time, with your own subscription.")
        print("  Never bulk-download from a publisher. See docs/ACQUISITION.md.")


if __name__ == "__main__":
    main()
