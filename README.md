# www.gugenheimer.com

A plain Jekyll site (Markdown and YAML). GitHub Pages builds it automatically, so there is no build step and nothing to install for publishing.

```
index.md               home: bio, research, selected publications
publications.md        all publications by year (generated from _data/publications.yml)
group.md, teaching.md  plain Markdown pages
_data/publications.yml publication list: maintained by the scripts, editable by hand
assets/papers/         teaser images (one per paper)
assets/videos/         optional local copies of paper videos
assets/cv.pdf          CV linked in the menu
scripts/               publication tools (see below)
CNAME                  www.gugenheimer.com
```

## Put it online (one time)

1. Create a GitHub repository (e.g. `gugenheimer.github.io` or `website`) and push this folder:
   `git init && git add . && git commit -m "Website" && git branch -M main && git remote add origin <repo-url> && git push -u origin main`
2. In the repository: **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)`**.
3. Under **Custom domain**, enter `www.gugenheimer.com` (the `CNAME` file already contains it), and later tick **Enforce HTTPS**.
4. At your domain provider (DNS):
   - `www` → **CNAME** → `<your-github-username>.github.io`
   - apex `gugenheimer.com` → **A** records `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (redirects to www)
   - Remove the old records that point to the current WordPress host.
5. DNS changes take from minutes to a few hours.

Local preview (optional): `bundle install && bundle exec jekyll serve` → http://localhost:4000

## Publications

Everything shown comes from `_data/publications.yml`. You can edit it by hand at any time:
`featured: true` puts a paper on the home page, `award:` adds a highlighted note, and `image:`, `pdf:`, `video:` and `project:` add links. The scripts **only fill empty fields**, so your edits stay.

```
pip install -r requirements.txt

# 1) newest papers from Google Scholar + DOI (Crossref) + teaser image from the PDF
python scripts/update_from_scholar.py            # newest 20
python scripts/update_from_scholar.py --limit 60 # more
python scripts/update_from_scholar.py --images-only

# 2) videos from the ACM Digital Library (preview + full video)
python scripts/fetch_acm_videos.py               # link the ACM videos
python scripts/fetch_acm_videos.py --download    # store copies in assets/videos (< 90 MB each)
python scripts/fetch_acm_videos.py --browser     # if ACM blocks plain requests (needs: pip install playwright && playwright install chromium)

# 3) other sources
python scripts/import_bibtex.py janC_2026.bib janJ_2026.bib   # import from your CV bib files
python scripts/images_from_local_pdfs.py ~/papers/*.pdf        # teaser images from PDFs you have
```

**Where the images come from:** a PDF from ACM DL, Semantic Scholar, OpenAlex (university repositories) or arXiv, cropped to Figure 1. ACM answers scripts with HTTP 403, and loading many ACM pages quickly gets your IP blocked for a while, so go slowly. Older papers use the thumbnails from the old WordPress site. For anything still missing, run `images_from_local_pdfs.py` on your own copies or drop an image into `assets/papers/<key>.jpg`.

**What is skipped from Scholar:** preprints, extended abstracts (workshops, LBWs, SIGs), companion/adjunct proceedings, demos, posters, entries without a venue, and duplicate titles.

**How the teaser image is chosen:** the script looks for the caption "Figure 1:" in the first pages (ACM's cover sheet is skipped) and crops the figure above it. If that fails, it uses the first other captioned figure, then the largest embedded image. If you don't like a result, put your own image in `assets/papers/<key>.jpg`. Or set `image:` to another file; then the script leaves it alone (`--force-images` recomputes all images).

**Videos:** a paper with a video on the ACM Digital Library gets a "Video" link that opens its ACM page in a new tab. Images are plain images.

**Automatic updates:** `.github/workflows/update-publications.yml` runs both scripts once a month (and on demand via *Actions → Update publications → Run workflow*) and commits new entries. The ACM video step needs `--browser` on your own computer, because ACM blocks plain requests. Google Scholar sometimes blocks GitHub's servers. Then nothing changes, and you can run the scripts on your own computer.
