#!/usr/bin/env python3
"""Download Figure 1 images from ACM full-text pages and use them as teaser images.

    python scripts/fetch_acm_figures.py _source_data/acm_figure_urls.json
    python scripts/fetch_acm_figures.py _source_data/acm_figure_urls.json --replace   # also replace existing images

The JSON file maps DOI -> image URL (copied from the paper's full-text page on dl.acm.org).
ACM blocks an IP address for a while after many fast requests, so this waits between downloads.
"""
import argparse
import io
import json
import time

import requests
from PIL import Image

import pubdata as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("urls")
    ap.add_argument("--replace", action="store_true", help="also replace images that already exist")
    args = ap.parse_args()

    figures = json.load(open(args.urls, encoding="utf-8"))
    pubs = pd.load()
    for p in pubs:
        url = figures.get(p.get("doi"))
        if not url or (p.get("image") and not args.replace):
            continue
        r = requests.get(url, headers=pd.HEADERS, timeout=30)
        if not r.ok or not r.headers.get("content-type", "").startswith("image"):
            print(f"{p['key']}: HTTP {r.status_code}, stopping (ACM may be blocking this IP; try again later)")
            break
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        if img.width > 640:
            img = img.resize((640, int(img.height * 640 / img.width)), Image.LANCZOS)
        out = pd.IMG_DIR / f"{p['key']}.jpg"
        img.save(out, "JPEG", quality=85)
        p["image"] = f"/assets/papers/{out.name}"
        print(f"{p['key']}: {img.size}")
        time.sleep(5)
    pd.save(pubs)


if __name__ == "__main__":
    main()
