#!/usr/bin/env python3
"""Create teaser images from paper PDFs you already have on disk.

    python scripts/images_from_local_pdfs.py ~/papers/*.pdf
    python scripts/images_from_local_pdfs.py --force paper.pdf   # overwrite existing image

Each PDF is matched to an entry in _data/publications.yml by the DOI in its file name
(ACM names files like 3491102.3517728.pdf) or, failing that, by the title on its first pages.
"""
import argparse
import re
import sys

import fitz  # PyMuPDF

import pubdata as pd


def match(pubs, path):
    m = re.search(r"(\d{7}\.\d{7}|\d{7})", path.name)
    if m:
        for p in pubs:
            if (p.get("doi") or "").endswith(m.group(1)):
                return p
    doc = fitz.open(path)
    text = " ".join(doc[i].get_text() for i in range(min(3, len(doc))))
    best, score = None, 0.0
    for p in pubs:
        t = pd.norm(p.get("title", ""))
        if t and t in pd.norm(text):
            return p
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    from pathlib import Path
    pubs = pd.load()
    for f in map(Path, args.pdfs):
        p = match(pubs, f)
        if not p:
            print(f"no match: {f.name}")
            continue
        if p.get("image") and not args.force:
            print(f"has image: {p['key']}")
            continue
        out = pd.IMG_DIR / f"{p['key']}.jpg"
        pd.extract_teaser(str(f), out)
        p["image"] = f"/assets/papers/{out.name}"
        print(f"{f.name} -> {out.name}  ({p['title'][:60]})")
    pd.save(pubs)


if __name__ == "__main__":
    sys.exit(main())
