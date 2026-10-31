#!/usr/bin/env python3
"""Import publications from BibTeX files (e.g. the .bib files of your CV) into _data/publications.yml.

    python scripts/import_bibtex.py janC_2026.bib janJ_2026.bib

Useful as a complete starting point, because Scholar only returns what it has indexed.
Existing entries (matched by title) are kept; only empty fields are filled.
"""
import re
import sys

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

import pubdata as pd

AWARD = re.compile(r"(best paper[^,;}]*|honou?rable mention[^,;}]*)", re.I)


def clean(s: str) -> str:
    s = re.sub(r"\\textbf\{?([^}]*)\}?", r"\1", s or "")
    s = re.sub(r"[{}]", "", s).replace("\\&", "&").replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


def authors(s: str) -> str:
    names = []
    for a in clean(s).split(" and "):
        a = a.strip()
        if "," in a:
            last, first = [x.strip() for x in a.split(",", 1)]
            a = f"{first} {last}"
        names.append(a)
    return ", ".join(names)


def venue(e: dict) -> str:
    v = e.get("series") or e.get("journal") or e.get("booktitle") or ""
    return clean(v)


def main(files: list[str]) -> None:
    pubs = pd.load()
    for f in files:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        with open(f, encoding="utf-8") as fh:
            db = bibtexparser.load(fh, parser=parser)
        for e in db.entries:
            title = clean(e.get("title", ""))
            if not title:
                continue
            entry = {
                "title": title,
                "authors": authors(e.get("author", "")),
                "venue": venue(e),
                "year": int(re.sub(r"\D", "", e.get("year", "0"))[:4] or 0) or None,
                "doi": clean(e.get("doi", "")).lower() or None,
            }
            entry["venue"], award = pd.short_venue(entry["venue"], entry["year"])
            m = AWARD.search(" ".join(e.get(k, "") for k in ("note", "award", "keywords")))
            if award or m:
                entry["award"] = award or clean(m.group(1)).title()
            p = pd.find(pubs, title)
            if p is None:
                entry["key"] = pd.make_key(entry["authors"], entry["year"], title)
                pubs.append({k: v for k, v in entry.items() if v})
            else:
                for k, v in entry.items():
                    if v and not p.get(k):
                        p[k] = v
    pd.save(pubs)
    print(f"saved {len(pubs)} publications")


if __name__ == "__main__":
    main(sys.argv[1:])
