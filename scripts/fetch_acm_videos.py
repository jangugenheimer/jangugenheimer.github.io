#!/usr/bin/env python3
"""Find the videos that ACM publishes with each paper and add them to _data/publications.yml.

    python scripts/fetch_acm_videos.py              # link videos (no download)
    python scripts/fetch_acm_videos.py --download   # also store copies in assets/videos/ (max. 90 MB each)
    python scripts/fetch_acm_videos.py --browser    # use a headless browser if ACM blocks plain requests

For every paper with an ACM DOI (10.1145/...) without a video yet, the script opens
https://dl.acm.org/doi/<doi>, reads the "Supplemental Material" section and collects .mp4 files.
ACM usually has two: a short preview video and the full video/talk. The script stores
  video:        link to the full video (shown as a "Video" button)
  video_embed:  local copy in assets/videos (with --download); the site's player prefers it
With --download the files are copied into the repository, which avoids hotlinking from ACM.
GitHub refuses files over 100 MB, so larger videos stay as links.
"""
import argparse
import re
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

import pubdata as pd

ACM = "https://dl.acm.org"
MAX_MB = 90


def page_html(doi: str, browser: bool) -> str | None:
    url = f"{ACM}/doi/{doi}"
    if browser:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(user_agent=pd.HEADERS["User-Agent"])
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(3000)
            html = pg.content()
            b.close()
            return html
    r = requests.get(url, headers=pd.HEADERS, timeout=30)
    if r.status_code != 200 or "Just a moment" in r.text[:2000]:
        print(f"  ACM blocked the request (HTTP {r.status_code}); try --browser")
        return None
    return r.text


def find_videos(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    for tag in soup.find_all(["a", "source", "video"]):
        for attr in ("href", "src", "data-src"):
            v = tag.get(attr)
            if v and re.search(r"\.(mp4|mov|webm)(\?|$)", v, re.I):
                urls.add(urljoin(ACM, v))
    for v in re.findall(r'["\'](/doi/suppl/[^"\']+\.(?:mp4|mov|webm))["\']', html, re.I):
        urls.add(urljoin(ACM, v))
    # newer ACM pages: /action/downloadSupplement?doi=...&file=....mp4
    for v in re.findall(r'["\'](/action/downloadSupplement\?[^"\']+?\.(?:mp4|mov|webm)[^"\']*)["\']', html, re.I):
        urls.add(urljoin(ACM, v.replace("&amp;", "&")))
    # file names often contain spaces
    return sorted(quote(u, safe=":/?&=%") for u in urls)


def pick(urls: list[str]) -> tuple[str | None, str | None]:
    """Return (full video, preview video)."""
    # older ACM names: pn2164p.mp4 = preview, pn2164-file3.mp4 = video figure, p4021-gugenheimer.mp4 = talk
    preview = [u for u in urls if re.search(r"preview|teaser|short|30s|pv\.mp4$|/[a-z]*\d+p\.mp4$", u, re.I)]
    # prefer the video figure over the (long) talk recording
    full = sorted((u for u in urls if u not in preview),
                  key=lambda u: bool(re.search(r"talk|presentation|session|/p\d+-[a-z]+\.mp4$", u, re.I)))
    main = (full or preview or [None])[0]
    return main, (preview[0] if preview else main)


def download(url: str, key: str, suffix: str) -> str | None:
    pd.VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    out = pd.VIDEO_DIR / f"{key}{suffix}.mp4"
    with requests.get(url, headers=pd.HEADERS, stream=True, timeout=120) as r:
        if not r.ok:
            return None
        size = int(r.headers.get("content-length", 0))
        if size > MAX_MB * 1e6:
            print(f"  {size/1e6:.0f} MB is too large for GitHub, keeping the link")
            return None
        with open(out, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return f"/assets/videos/{out.name}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--all", action="store_true", help="also re-check papers that already have a video")
    args = ap.parse_args()

    pubs = pd.load()
    for p in pubs:
        doi = p.get("doi", "")
        if not doi.startswith("10.1145/") or (p.get("video") and not args.all):
            continue
        print(f"video: {p['title'][:70]}")
        html = page_html(doi, args.browser)
        if not html:
            continue
        main_url, preview_url = pick(find_videos(html))
        if not main_url:
            print("  no video")
            continue
        p["video"] = main_url
        p["video_embed"] = preview_url
        if args.download:
            local = download(main_url, p["key"], "")
            if local:
                p["video_embed"] = local
        print(f"  found {main_url}")
    pd.save(pubs)


if __name__ == "__main__":
    main()
