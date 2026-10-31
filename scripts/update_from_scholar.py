#!/usr/bin/env python3
"""Pull the most recent publications from Google Scholar into _data/publications.yml
and pick a representative image (the teaser figure) for each paper.

    python scripts/update_from_scholar.py               # newest 20 papers from Scholar
    python scripts/update_from_scholar.py --limit 50
    python scripts/update_from_scholar.py --images-only  # only (re)try missing images
    python scripts/update_from_scholar.py --force-images # recompute all images

How it works
  1. Scholar (via the `scholarly` package) gives title, authors, venue, year, citations.
     Google Scholar blocks automated access from time to time. If that happens, run the
     script again later, or from your laptop instead of GitHub Actions, or set
     SCHOLAR_PROXY=free to let scholarly use free proxies.
  2. Crossref finds the DOI from the title.
  3. The PDF comes from the ACM Digital Library (open access) or Semantic Scholar.
  4. scripts/pubdata.extract_teaser() crops "Figure 1" (the teaser) and stores it in
     assets/papers/<key>.jpg.
Existing entries and anything you edited by hand are kept; only empty fields are filled.
"""
import argparse
import os
import re

import pubdata as pd

SCHOLAR_ID = "DkjBHDUAAAAJ"
# Scholar also lists preprints, workshop proposals, demos and posters; these are not added.
SKIP_VENUE = re.compile(r"arxiv|preprint|companion|extended abstracts|adjunct|workshop|"
                        r"doctoral|poster|demo|ssrn|research ?gate", re.I)


def fetch_scholar(limit: int) -> list[dict]:
    from scholarly import scholarly, ProxyGenerator

    if os.environ.get("SCHOLAR_PROXY") == "free":
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)

    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"], sortby="year")
    out, seen = [], set()
    for pub in author["publications"][:limit]:
        pub = scholarly.fill(pub)
        bib = pub.get("bib", {})
        authors = bib.get("author", "").replace(" and ", ", ")
        year = int(bib.get("pub_year") or 0) or None
        raw_venue = bib.get("conference") or bib.get("journal") or bib.get("citation", "")
        if not raw_venue or SKIP_VENUE.search(raw_venue) or pd.norm(bib.get("title", "")) in seen:
            print(f"skip: {bib.get('title', '')[:70]} ({raw_venue[:50] or 'no venue'})")
            continue
        seen.add(pd.norm(bib.get("title", "")))
        venue, _ = pd.short_venue(raw_venue, year)
        out.append({
            "title": bib.get("title", "").strip(),
            "authors": authors,
            "venue": venue,
            "year": int(bib.get("pub_year") or 0) or None,
            "citations": pub.get("num_citations"),
            "scholar_url": pub.get("pub_url"),
        })
    return out


def add_images(pubs: list[dict], force: bool = False) -> None:
    for p in pubs:
        if p.get("image") and not force:
            continue
        if not p.get("doi") and not p.get("pdf"):
            continue
        print(f"image: {p['title'][:70]}")
        pdf = pd.download_pdf(p)
        if not pdf:
            print("  no open PDF found, skipped")
            continue
        out = pd.IMG_DIR / f"{p['key']}.jpg"
        try:
            pd.extract_teaser(pdf, out)
            p["image"] = f"/assets/papers/{out.name}"
        except Exception as e:
            print(f"  image extraction failed: {e}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="number of most recent Scholar entries")
    ap.add_argument("--images-only", action="store_true")
    ap.add_argument("--force-images", action="store_true")
    args = ap.parse_args()

    pubs = pd.load()
    if not args.images_only:
        for s in fetch_scholar(args.limit):
            if not s["title"]:
                continue
            p = pd.find(pubs, s["title"])
            if p is None:
                p = {k: v for k, v in s.items() if v}
                p["key"] = pd.make_key(s["authors"], s["year"], s["title"])
                pubs.append(p)
                print(f"new: {s['title']}")
            else:  # only fill gaps, keep hand edits
                for k, v in s.items():
                    if v and not p.get(k):
                        p[k] = v
                if s.get("citations"):
                    p["citations"] = s["citations"]
            if not p.get("doi"):
                doi = pd.crossref_doi(p["title"], p.get("year"))
                if doi:
                    p["doi"] = doi
    add_images(pubs, force=args.force_images)
    pd.save(pubs)
    print(f"saved {len(pubs)} publications to {pd.DATA}")


if __name__ == "__main__":
    main()
