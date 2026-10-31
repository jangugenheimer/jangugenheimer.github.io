"""Shared helpers for the publication scripts.

The single source of truth for the website is _data/publications.yml.
Every script reads it, adds what it can find, and writes it back.
Entries you edit by hand are never overwritten: scripts only fill empty fields.
"""
from __future__ import annotations

import io
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data" / "publications.yml"
IMG_DIR = ROOT / "assets" / "papers"
VIDEO_DIR = ROOT / "assets" / "videos"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

# Field order in the YAML file (purely cosmetic).
FIELDS = ["key", "title", "authors", "venue", "year", "award", "doi", "pdf",
          "image", "video", "video_embed", "project", "featured", "scholar_url", "citations"]


# ---------------------------------------------------------------- YAML I/O
def load() -> list[dict]:
    if not DATA.exists():
        return []
    return yaml.safe_load(DATA.read_text(encoding="utf-8")) or []


def save(pubs: list[dict]) -> None:
    pubs = sorted(pubs, key=lambda p: (-int(p.get("year") or 0), p.get("title", "")))
    ordered = []
    for p in pubs:
        q = {k: p[k] for k in FIELDS if p.get(k) not in (None, "", [])}
        q.update({k: v for k, v in p.items() if k not in FIELDS and v not in (None, "")})
        ordered.append(q)
    DATA.write_text(
        "# Generated and maintained by scripts/*.py. Hand edits are kept;\n"
        "# scripts only fill empty fields. Set `featured: true` to show a paper on the home page.\n"
        + yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- matching
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def find(pubs: list[dict], title: str, threshold: float = 0.9) -> dict | None:
    best, score = None, 0.0
    for p in pubs:
        s = similar(p.get("title", ""), title)
        if s > score:
            best, score = p, s
    return best if score >= threshold else None


def make_key(authors: str, year, title: str) -> str:
    first = norm((authors or "x").split(",")[0].split(" and ")[0]).split()
    last = first[-1] if first else "x"
    word = next((w for w in norm(title).split() if len(w) > 3), "paper")
    return f"{last}{year}{word}"


# ---------------------------------------------------------------- DOI lookup
def crossref_doi(title: str, year=None) -> str | None:
    """Find the DOI of a paper by its title (Crossref, free, no key)."""
    try:
        r = requests.get("https://api.crossref.org/works",
                         params={"query.bibliographic": title, "rows": 5},
                         headers={"User-Agent": "gugenheimer.com publication updater"}, timeout=20)
        for item in r.json()["message"]["items"]:
            t = (item.get("title") or [""])[0]
            if similar(t, title) > 0.92:
                return item["DOI"].lower()
    except Exception as e:  # network problems are not fatal
        print(f"  crossref failed: {e}")
    return None


# ---------------------------------------------------------------- PDF lookup
def candidate_pdf_urls(pub: dict) -> list[str]:
    urls = []
    if pub.get("pdf", "").startswith("http"):
        urls.append(pub["pdf"])
    doi = pub.get("doi")
    if doi:
        if doi.startswith("10.1145/"):
            urls.append(f"https://dl.acm.org/doi/pdf/{doi}")  # ACM DL is open access since 2026
        try:
            r = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
                             params={"fields": "openAccessPdf"}, timeout=20)
            oa = (r.json() or {}).get("openAccessPdf") or {}
            if oa.get("url"):
                urls.append(oa["url"])
        except Exception:
            pass
        urls += openalex_pdfs(doi)
    arxiv = arxiv_pdf(pub.get("title", ""))
    if arxiv:
        urls.append(arxiv)
    return urls


def openalex_pdfs(doi: str) -> list[str]:
    """Open copies listed by OpenAlex, e.g. in university repositories (ACM itself is skipped)."""
    try:
        r = requests.get(f"https://api.openalex.org/works/doi:{doi}", timeout=20)
        locs = r.json().get("locations") or []
        return [l["pdf_url"] for l in locs if l.get("pdf_url") and "dl.acm.org" not in l["pdf_url"]]
    except Exception:
        return []


def arxiv_pdf(title: str) -> str | None:
    """PDF link of the arXiv version of a paper, found by its title."""
    time.sleep(3)  # arXiv asks for at most one request every 3 seconds
    try:
        words = " AND ".join(f"ti:{w}" for w in [w for w in norm(title).split() if len(w) > 3][:8])
        r = requests.get("https://export.arxiv.org/api/query",
                         params={"search_query": words, "max_results": 5}, timeout=30)
        for entry in re.findall(r"<entry>(.*?)</entry>", r.text, re.S):
            t = re.search(r"<title>(.*?)</title>", entry, re.S).group(1)
            if similar(t, title) > 0.92:
                return re.search(r"<id>(.*?)</id>", entry).group(1).replace("/abs/", "/pdf/")
    except Exception as e:
        print(f"  arxiv failed: {e}")
    return None


def download_pdf(pub: dict) -> bytes | None:
    for url in candidate_pdf_urls(pub):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.ok and r.content[:4] == b"%PDF":
                return r.content
            print(f"  no PDF at {url} (HTTP {r.status_code})")
        except Exception as e:
            print(f"  download failed {url}: {e}")
    return None


# ---------------------------------------------------------------- teaser image
def extract_teaser(pdf: bytes | str | Path, out: Path, width: int = 640) -> bool:
    """Pick a representative image from a paper and save it as JPEG.

    Strategy (works well for ACM/IEEE papers, which almost always start with a teaser):
      1. Find the caption "Figure 1" on page 1 or 2 and crop the figure above it
         (works for vector graphics too, because the region is rendered).
      2. Otherwise take the largest embedded raster image on pages 1-2.
      3. Otherwise render the upper part of page 1.
    """
    import fitz  # PyMuPDF
    from PIL import Image

    doc = fitz.open(stream=pdf, filetype="pdf") if isinstance(pdf, (bytes, bytearray)) else fitz.open(pdf)
    clip, page = None, None
    # ACM DL PDFs start with a cover sheet ("Citation in BibTeX format", "Open Access Support"): skip it.
    cover = re.compile(r"Citation in BibTeX format|Open Access Support|Latest updates:|PDF Download|"
                       r"Author Accepted Manuscript|Deposited on:|Enlighten|Downloaded from|List of Figures|Table of Contents", re.I)
    pages = [i for i in range(min(10, len(doc))) if not cover.search(doc[i].get_text())][:8] or [0]

    # Try "Figure 1" first; if it is missing or unusable, take the first figure with a caption.
    # Some papers (surveys, workshop studies) have their first figure late, so the fallback scans every page.
    later = [i for i in range(len(doc)) if i not in pages and not cover.search(doc[i].get_text())]
    attempts = [(pno, r"1") for pno in pages] + [(pno, r"\d+") for pno in pages + later]
    for pno, num in attempts:
        pg = doc[pno]
        blocks = [b for b in pg.get_text("blocks") if b[6] == 0]
        caps = [b for b in blocks if re.match(rf"^\s*(Figure|Fig\.)\s*{num}\s*[\.:]", b[4])]
        if not caps:
            continue
        cap = caps[0]
        x0, x1 = (cap[0], cap[2]) if (cap[2] - cap[0]) > pg.rect.width * 0.55 else (cap[0] - 5, cap[2] + 5)
        # The figure sits between the last text block above the caption and the caption.
        colw = x1 - x0
        # Text above the figure: long, wide body text, or author/affiliation blocks (contain '@').
        # Labels inside the figure are short and narrow, so they are ignored.
        above = [b for b in blocks if b[3] <= cap[1] + 1 and b[2] > x0 and b[0] < x1 and b is not cap
                 and b[1] > pg.rect.height * 0.09
                 and ((len(b[4].strip()) > 80 and (b[2] - b[0]) > 0.8 * colw) or "@" in b[4])]
        top = max((b[3] for b in above), default=pg.rect.height * 0.08)
        imgs = [r for i in pg.get_images(full=True) for r in pg.get_image_rects(i)[:1]]
        imgs = [r for r in imgs if r.is_valid and r.y1 <= cap[1] + 2 and r.y0 >= top - 2
                and r.x1 > x0 and r.x0 < x1]
        if imgs:  # tighten the region to the raster images it contains
            top = min(r.y0 for r in imgs)
        if cap[1] - top > 60:
            clip = fitz.Rect(max(x0, 20), top + 2, min(max(x1, x0 + 200), pg.rect.width - 20), cap[1] - 2)
            page = pg
            break

    if clip is None:
        best = None
        for pno in pages:
            pg = doc[pno]
            for r in (r for i in pg.get_images(full=True) for r in pg.get_image_rects(i)[:1]):
                if r.is_valid and (best is None or r.get_area() > best[1].get_area()):
                    best = (pg, r)
        if best and best[1].get_area() > 0.05 * best[0].rect.get_area():
            page, clip = best

    if clip is None:
        page = doc[pages[0]]
        clip = fitz.Rect(0, page.rect.height * 0.15, page.rect.width, page.rect.height * 0.55)

    pix = page.get_pixmap(clip=clip, dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    if img.width > width:
        img = img.resize((width, int(img.height * width / img.width)), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=85)
    return True


# ---------------------------------------------------------------- venue names
_ACRONYMS = ["CHI", "UIST", "CSCW", "DIS", "MobileHCI", "ISMAR", "IEEE VR", "VRST", "SUI", "ITS", "ISS",
             "AutoUI", "AutomotiveUI", "MUM", "TEI", "IMWUT", "PerDis", "ETRA", "MuC", "TOCHI", "INTERACT"]
_JOURNALS = {"ACM Transactions on Computer-Human Interaction": "ACM TOCHI",
             "IEEE Transactions on Visualization and Computer Graphics": "IEEE TVCG",
             "Proc. ACM Hum.-Comput. Interact.": "PACM HCI",
             "Proceedings of the ACM on Human-Computer Interaction": "PACM HCI",
             "Virtual Reality and 3D User Interfaces (VR)": "IEEE VR",
             "ACM Trans. Comput.-Hum. Interact.": "ACM TOCHI",
             "Interactive, Mobile, Wearable and Ubiquitous Technologies": "IMWUT",
             "Mobile and Ubiquitous Multimedia": "MUM"}


def short_venue(venue: str, year=None) -> tuple[str, str | None]:
    """Turn long proceedings names into 'CHI 2020' and pull out an award note, if any."""
    v = venue or ""
    award = None
    m = re.search(r"\*([^*]*(Best|Honou?rable)[^*]*)\*", v)
    if m:
        award = m.group(1).strip()
    for long, short in _JOURNALS.items():
        if long.lower() in v.lower():
            return (f"{short} {year}" if year else short), award
    m = re.search(r"\(([A-Za-z ]+?)\s*'?(\d{2,4})", v)
    if m and m.group(1).strip() in _ACRONYMS:
        return f"{m.group(1).strip()} {year or m.group(2)}", award
    m = re.match(r"^([A-Za-z ]+?) '(\d{2})", v)  # e.g. "CHI '25"
    if m and m.group(1).strip() in _ACRONYMS:
        return f"{m.group(1).strip()} {year or '20' + m.group(2)}", award
    for a in _ACRONYMS:
        if re.search(rf"\b{re.escape(a)}\b", v):
            return f"{a} {year}" if year else a, award
    if "Mixed and Augmented Reality" in v:
        return f"ISMAR {year}" if year else "ISMAR", award
    if "Human Factors in Computing Systems" in v:
        return f"CHI {year}" if year else "CHI", award
    if "User Interface Software" in v:
        return f"UIST {year}" if year else "UIST", award
    if "Spatial User Interaction" in v:
        return f"SUI {year}" if year else "SUI", award
    return v, award
