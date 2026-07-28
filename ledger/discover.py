"""Stage 1 — discovery. Metadata search and citation-graph traversal.

    python -m ledger.discover search "flexible link vibration suppression" --limit 20
    python -m ledger.discover refs-of  10.1000/example --keep-order
    python -m ledger.discover cited-by 10.1000/example
    python -m ledger.discover doi      10.1000/example

Three sources are merged and de-duplicated by DOI: Semantic Scholar, OpenAlex and
Crossref.

Why not Google Scholar: it has no public API and blocks automated access. What it
uniquely offers — citation counts and a "cited by" graph — is fully covered by
Semantic Scholar and OpenAlex, both of which have documented APIs.

为什么不爬 Google Scholar：无公开 API 且强反爬。它独有的引用数排序与 cited-by
由 Semantic Scholar 与 OpenAlex 完整覆盖，且两者都有正式 API。

Output lands in runs/ as a reviewable table. Feed the .json to stage 2.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re

from . import common as C

S2 = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = ("title,year,externalIds,venue,authors,citationCount,"
             "openAccessPdf,abstract,publicationTypes")
OA = "https://api.openalex.org/works"
CR = "https://api.crossref.org/works"

CONF_WORDS = ("conf", "proc", "icra", "iros", "symposium", "humanoids", "workshop")


def _s2_headers(cfg: dict) -> dict:
    k = (cfg.get("semantic_scholar_api_key") or "").strip()
    return {"x-api-key": k} if k else {}


def _mail(cfg: dict) -> str:
    return cfg.get("contact_email", "")


def _rec(doi=None, title="", year=None, authors=None, venue="", citations=None,
         oa_pdf=None, abstract="", source="") -> dict:
    return {
        "doi": C.norm_doi(doi),
        "title": (title or "").strip(),
        "year": year,
        "authors": authors or [],
        "venue": (venue or "").strip(),
        "citations": citations,
        "oa_pdf": oa_pdf,
        "abstract": (abstract or "")[:600],
        "sources": [source] if source else [],
    }


# ---------------------------------------------------------------- sources

def from_s2(paper: dict, source: str = "S2") -> dict:
    ext = paper.get("externalIds") or {}
    return _rec(
        doi=ext.get("DOI"), title=paper.get("title"), year=paper.get("year"),
        authors=[a.get("name", "") for a in (paper.get("authors") or [])],
        venue=paper.get("venue"), citations=paper.get("citationCount"),
        oa_pdf=(paper.get("openAccessPdf") or {}).get("url"),
        abstract=paper.get("abstract") or "", source=source)


def s2_search(cfg, q, limit) -> list[dict]:
    d = C.get_json(f"{S2}/paper/search",
                   {"query": q, "limit": min(limit, 100), "fields": S2_FIELDS},
                   _s2_headers(cfg))
    return [from_s2(p) for p in (d or {}).get("data") or []]


def s2_refs(cfg, doi, limit=200) -> list[dict]:
    """Semantic Scholar references.

    Note: some publishers require S2 to elide the references field. The response
    is then {"data": null} rather than an empty list, so a None check is
    mandatory. Callers should fall back to Crossref.
    """
    d = C.get_json(f"{S2}/paper/DOI:{doi}/references",
                   {"limit": limit, "fields": S2_FIELDS}, _s2_headers(cfg))
    return [from_s2(r["citedPaper"], "S2-ref")
            for r in ((d or {}).get("data") or []) if r.get("citedPaper")]


def s2_cited_by(cfg, doi, limit=200) -> list[dict]:
    d = C.get_json(f"{S2}/paper/DOI:{doi}/citations",
                   {"limit": limit, "fields": S2_FIELDS}, _s2_headers(cfg))
    return [from_s2(r["citingPaper"], "S2-citedby")
            for r in ((d or {}).get("data") or []) if r.get("citingPaper")]


def s2_doi(cfg, doi) -> list[dict]:
    d = C.get_json(f"{S2}/paper/DOI:{doi}", {"fields": S2_FIELDS},
                   _s2_headers(cfg))
    return [from_s2(d)] if d else []


def _from_openalex(w: dict, source: str) -> dict:
    src = (w.get("primary_location") or {}).get("source") or {}
    return _rec(
        doi=w.get("doi"), title=w.get("display_name"),
        year=w.get("publication_year"),
        authors=[a["author"]["display_name"]
                 for a in (w.get("authorships") or []) if a.get("author")],
        venue=src.get("display_name", ""), citations=w.get("cited_by_count"),
        oa_pdf=(w.get("best_oa_location") or {}).get("pdf_url"), source=source)


def openalex_search(cfg, q, limit) -> list[dict]:
    d = C.get_json(OA, {"search": q, "per-page": min(limit, 50),
                        "mailto": _mail(cfg)})
    return [_from_openalex(w, "OpenAlex") for w in (d or {}).get("results") or []]


def crossref_search(cfg, q, limit) -> list[dict]:
    d = C.get_json(CR, {"query.bibliographic": q, "rows": min(limit, 50),
                        "mailto": _mail(cfg)})
    out = []
    for w in (d or {}).get("message", {}).get("items") or []:
        out.append(_rec(
            doi=w.get("DOI"), title=" ".join(w.get("title") or []),
            year=((w.get("issued") or {}).get("date-parts") or [[None]])[0][0],
            authors=[f"{a.get('given','')} {a.get('family','')}".strip()
                     for a in (w.get("author") or [])],
            venue=" ".join(w.get("container-title") or []),
            citations=w.get("is-referenced-by-count"), source="Crossref"))
    return out


def crossref_refs(cfg, doi) -> list[dict]:
    """Crossref reference list — the preferred source for refs-of.

    Its ``key`` field is shaped like ``ref19``, which preserves the reference
    numbering of the original article. That is the only way to answer "which
    paper is [19] in this article?" without opening the PDF. Neither Semantic
    Scholar nor OpenAlex exposes the numbering.

    Crossref 的 key 形如 ref19，保留了原文参考文献编号，是不开 PDF 就能回答
    「这篇的 [19] 是哪一篇」的唯一途径。S2 与 OpenAlex 都不给编号。
    """
    d = C.get_json(f"{CR}/{doi}", {"mailto": _mail(cfg)})
    out = []
    for x in (d or {}).get("message", {}).get("reference") or []:
        num = re.search(r"(\d+)\s*$", str(x.get("key", "")))
        r = _rec(doi=x.get("DOI"),
                 title=x.get("article-title") or x.get("volume-title") or "",
                 year=int(x["year"]) if str(x.get("year", "")).isdigit() else None,
                 authors=[x["author"]] if x.get("author") else [],
                 venue=x.get("journal-title") or "", source="Crossref-ref")
        r["ref_no"] = int(num.group(1)) if num else None
        r["unstructured"] = x.get("unstructured", "")
        out.append(r)
    out.sort(key=lambda r: (r["ref_no"] is None, r["ref_no"] or 0))
    return out


def openalex_refs(cfg, doi, limit=200) -> list[dict]:
    """OpenAlex referenced_works — second-line fallback. No numbering, but not
    subject to publisher elision."""
    w = C.get_json(f"{OA}/doi:{doi}", {"mailto": _mail(cfg)})
    ids = (w or {}).get("referenced_works") or []
    out = []
    for i in range(0, min(len(ids), limit), 50):
        chunk = "|".join(u.rsplit("/", 1)[-1] for u in ids[i:i + 50])
        d = C.get_json(OA, {"filter": f"openalex_id:{chunk}", "per-page": 50,
                            "mailto": _mail(cfg)})
        out += [_from_openalex(x, "OpenAlex-ref")
                for x in (d or {}).get("results") or []]
    return out


def enrich(cfg, rows: list[dict], batch: int = 40) -> list[dict]:
    """Crossref reference entries often carry only a DOI. Back-fill title, year,
    venue and citation count from OpenAlex in batches, preserving ref_no."""
    todo = [r for r in rows if r["doi"] and not r["title"]]
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        d = C.get_json(OA, {"filter": "doi:" + "|".join(r["doi"] for r in chunk),
                            "per-page": batch, "mailto": _mail(cfg)})
        found = {}
        for x in (d or {}).get("results") or []:
            k = C.norm_doi(x.get("doi"))
            if k:
                found[k] = x
        for r in chunk:
            x = found.get(r["doi"])
            if not x:
                continue
            filled = _from_openalex(x, "OpenAlex-enrich")
            for f in ("title", "year", "venue", "citations", "oa_pdf"):
                if not r.get(f):
                    r[f] = filled[f]
            if not r["authors"]:
                r["authors"] = filled["authors"]
            if "OpenAlex-enrich" not in r["sources"]:
                r["sources"].append("OpenAlex-enrich")
    return rows


# ---------------------------------------------------------------- merge

def merge(groups: list[list[dict]]) -> list[dict]:
    """De-duplicate by DOI; fall back to a lowercased title key when absent.
    First writer wins per field; later sources only fill gaps."""
    by_key: dict[str, dict] = {}
    for g in groups:
        for r in g:
            k = r["doi"] or ("t:" + r["title"].lower()[:120])
            if k in ("", "t:"):
                continue
            cur = by_key.get(k)
            if cur is None:
                by_key[k] = r
                continue
            for f in ("title", "venue", "abstract"):
                if not cur.get(f) and r.get(f):
                    cur[f] = r[f]
            for f in ("year", "citations", "oa_pdf", "doi"):
                if cur.get(f) in (None, "") and r.get(f) not in (None, ""):
                    cur[f] = r[f]
            if not cur["authors"] and r["authors"]:
                cur["authors"] = r["authors"]
            for s in r["sources"]:
                if s not in cur["sources"]:
                    cur["sources"].append(s)
    rows = list(by_key.values())
    rows.sort(key=lambda r: (-(r["citations"] or 0), -(r["year"] or 0)))
    return rows


def guess_item_type(venue: str) -> str:
    return ("conferencePaper"
            if any(w in (venue or "").lower() for w in CONF_WORDS)
            else "journalArticle")


# ---------------------------------------------------------------- output

def to_md(rows: list[dict], header: str) -> str:
    L = [f"# {header}", "",
         f"{len(rows)} records, sorted by citation count. "
         f"**Nothing has been filtered or selected.**", "",
         "Next: `python -m ledger.screen <this file>.json` to compare against "
         "your registries.", "",
         "| # | Year | First author | Title | Venue | Cites | OA | DOI | Source |",
         "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        tag = r.get("ref_no") or i
        a = (r["authors"][0] if r["authors"] else "")[:22]
        L.append(f"| {tag} | {r['year'] or ''} | {a} | "
                 f"{r['title'][:78].replace('|', '/')} | "
                 f"{r['venue'][:26].replace('|', '/')} | "
                 f"{r['citations'] if r['citations'] is not None else ''} | "
                 f"{'OA' if r['oa_pdf'] else ''} | `{r['doi'] or ''}` | "
                 f"{','.join(r['sources'])} |")
    return "\n".join(L) + "\n"


def save(cfg, rows, slug, header):
    runs = C.out_dir(cfg, "runs")
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = runs / f"candidates_{slug}_{ts}"
    stem.with_suffix(".json").write_text(
        json.dumps({"query": header, "generated": ts, "results": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    stem.with_suffix(".md").write_text(to_md(rows, header), encoding="utf-8")
    return stem


def main(argv=None) -> None:
    C.utf8_stdout()
    ap = argparse.ArgumentParser(
        prog="python -m ledger.discover",
        description="Discovery via Semantic Scholar + OpenAlex + Crossref")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("search", help="topic search across three sources")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--no-crossref", action="store_true")

    p = sub.add_parser("refs-of", help="list the references OF a DOI")
    p.add_argument("doi")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--keep-order", action="store_true",
                   help="Crossref only; keep the original reference numbering")

    p = sub.add_parser("cited-by", help="list papers citing a DOI")
    p.add_argument("doi")
    p.add_argument("--limit", type=int, default=100)

    p = sub.add_parser("doi", help="fetch one record")
    p.add_argument("doi")

    a = ap.parse_args(argv)
    cfg = C.load_config(a.config)

    if a.cmd == "search":
        groups = [s2_search(cfg, a.query, a.limit),
                  openalex_search(cfg, a.query, a.limit)]
        if not a.no_crossref:
            groups.append(crossref_search(cfg, a.query, a.limit))
        rows, slug, header = merge(groups), "search", f"Search: {a.query}"

    elif a.cmd == "refs-of":
        doi = C.norm_doi(a.doi) or a.doi
        cr = crossref_refs(cfg, doi)
        s2 = s2_refs(cfg, doi, a.limit)
        oa = openalex_refs(cfg, doi, a.limit) if not s2 else []
        if not s2 and not oa and cr:
            print("Note: Semantic Scholar returned no references for this DOI "
                  "(publisher elision is common); using Crossref instead.")
        rows = cr if a.keep_order else merge([cr, s2, oa])
        numbers = {r["doi"]: r.get("ref_no") for r in cr if r["doi"]}
        for r in rows:
            r.setdefault("ref_no", numbers.get(r["doi"]))
        enrich(cfg, rows)
        if any(r.get("ref_no") for r in rows):
            rows.sort(key=lambda r: (r.get("ref_no") is None, r.get("ref_no") or 0))
        slug, header = "refs", f"References of {doi}"

    elif a.cmd == "cited-by":
        doi = C.norm_doi(a.doi) or a.doi
        rows = merge([s2_cited_by(cfg, doi, a.limit)])
        slug, header = "citedby", f"Papers citing {doi}"

    else:
        doi = C.norm_doi(a.doi) or a.doi
        rows = merge([s2_doi(cfg, doi), crossref_search(cfg, doi, 3)])
        rows = [r for r in rows if r["doi"] == doi] or rows[:1]
        slug, header = "doi", f"Record for {doi}"

    if not rows:
        print("No results. Check the DOI, or the work may not be indexed.")
        return

    stem = save(cfg, rows, slug, header)
    print(f"{header}  ->  {len(rows)} records\n")
    for i, r in enumerate(rows[:25], 1):
        tag = f"[{r['ref_no']}]" if r.get("ref_no") else f"{i:>3}."
        a1 = (r["authors"][0] if r["authors"] else "?")[:20]
        title = (r["title"] or r.get("unstructured", ""))[:72]
        print(f"{tag:>5} [{r['year'] or '????'}] {a1:<20} {title}")
        print(f"      {r['venue'][:50]:<50} cites={r['citations']} "
              f"{'OA' if r['oa_pdf'] else '  '} {r['doi'] or ''}")
    if len(rows) > 25:
        print(f"  ... {len(rows) - 25} more in the .md")
    print(f"\n-> {stem}.json\n-> {stem}.md")


if __name__ == "__main__":
    main()
