"""Download Navaris Boats media + page snapshots into the repo.

Usage (from the repo root): python3 scripts/export_site.py .

Reads wix-data/media-manager.json (pulled with the Wix connector), re-downloads
every Media Manager original into media/, and re-snapshots every page listed in
the live sitemap into pages/, in English and in Croatian (under /hr).
"""
import datetime
import html
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

REPO = sys.argv[1]
SITE = "https://www.navarisboats.com"
MEDIA_BASE = "https://static.wixstatic.com/media/"


def curl(url, dest):
    subprocess.run(
        ["curl", "-sS", "--fail", "--retry", "3", "--max-time", "120", "-o", dest, url],
        check=True,
    )


def safe_name(name):
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return name or "file"


# ---------- media ----------
mm = json.load(open(os.path.join(REPO, "wix-data/media-manager.json")))
folder_names = {f["id"]: f["displayName"] for f in mm["folders"]}
media_index = []
used_paths = set()
for f in mm["files"]:
    folder = f.get("parentFolderId", "media-root")
    sub = "" if folder == "media-root" else safe_name(folder_names.get(folder, folder))
    base = safe_name(f["displayName"])
    rel = os.path.join("media", sub, base) if sub else os.path.join("media", base)
    if rel in used_paths:
        stem, ext = os.path.splitext(base)
        short_id = f["id"].split("_")[1][:8]
        rel = os.path.join(os.path.dirname(rel), f"{stem}__{short_id}{ext}")
    used_paths.add(rel)
    dest = os.path.join(REPO, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = MEDIA_BASE + f["id"]
    curl(url, dest)
    size = os.path.getsize(dest)
    ok = size == int(f["sizeInBytes"])
    media_index.append({"path": rel, "wixFileId": f["id"], "url": url, "bytes": size, "sizeMatchesWix": ok})
    print(("OK  " if ok else "SIZE MISMATCH ") + rel, size)

json.dump(media_index, open(os.path.join(REPO, "media/index.json"), "w"), indent=2)

# ---------- pages ----------
for name, path in [("sitemap.xml", "/sitemap.xml"), ("pages-sitemap.xml", "/pages-sitemap.xml"),
                   ("hr_hr-sitemap.xml", "/hr_hr-sitemap.xml"), ("hr_hr-pages-sitemap.xml", "/hr_hr-pages-sitemap.xml"),
                   ("robots.txt", "/robots.txt")]:
    curl(SITE + path, os.path.join(REPO, "pages", name))

sitemap = open(os.path.join(REPO, "pages/pages-sitemap.xml")).read()
page_urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)

BLOCK = {"p", "div", "section", "header", "footer", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "nav", "main", "article", "span"}
SKIP = {"script", "style", "noscript", "svg", "template", "head"}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.lines = []
        self.cur = []
        self.prefix = ""

    def flush(self):
        text = re.sub(r"\s+", " ", "".join(self.cur)).strip()
        if text:
            self.lines.append(self.prefix + text)
        self.cur = []
        self.prefix = ""

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        if tag in BLOCK:
            self.flush()
        if re.fullmatch(r"h[1-6]", tag):
            self.prefix = "#" * int(tag[1]) + " "
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.cur.append("")

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if tag in BLOCK:
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.cur.append(data)


referenced = {}
pages_index = []
TODAY = datetime.date.today().isoformat()
# the sitemap lists the English pages; each also exists in Croatian under /hr
targets = [(u, "en") for u in page_urls] + [(SITE + "/hr" + u.replace(SITE, ""), "hr") for u in page_urls]
for url, lang in targets:
    path = url.replace(SITE, "")
    if lang == "hr":
        path = path[len("/hr"):]
    slug = path.strip("/") or "home"
    sub = "hr/" if lang == "hr" else ""
    html_rel = f"pages/html/{sub}{slug}.html"
    os.makedirs(os.path.dirname(os.path.join(REPO, html_rel)), exist_ok=True)
    curl(url, os.path.join(REPO, html_rel))
    raw = open(os.path.join(REPO, html_rel), encoding="utf-8", errors="replace").read()

    title_m = re.search(r"<title>(.*?)</title>", raw, re.S)
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', raw)

    ex = TextExtractor()
    ex.feed(raw)
    ex.flush()
    lines = []
    for ln in ex.lines:
        if not lines or lines[-1] != ln:
            lines.append(ln)
    text_rel = f"pages/text/{sub}{slug}.md"
    os.makedirs(os.path.dirname(os.path.join(REPO, text_rel)), exist_ok=True)
    with open(os.path.join(REPO, text_rel), "w") as fh:
        fh.write(f"<!-- Text extracted from {url} on {TODAY} -->\n\n")
        fh.write("\n\n".join(lines) + "\n")

    for mid in set(re.findall(r"static\.wixstatic\.com/media/([0-9a-f]{6}_[0-9a-f]{32}(?:~mv2)?\.[a-z0-9]+)", raw)):
        referenced.setdefault(mid, []).append(sub + slug)

    pages_index.append({
        "url": url,
        "lang": lang,
        "slug": slug,
        "html": html_rel,
        "text": text_rel,
        "title": html.unescape(title_m.group(1).strip()) if title_m else None,
        "metaDescription": html.unescape(desc_m.group(1)) if desc_m else None,
        "htmlBytes": len(raw.encode()),
        "textLines": len(lines),
    })
    print("PAGE", url, "->", html_rel, len(raw), "chars,", len(lines), "text lines")

json.dump(pages_index, open(os.path.join(REPO, "pages/index.json"), "w"), indent=2)

in_mm = {f["id"] for f in mm["files"]}
refs = [
    {"wixFileId": k, "url": MEDIA_BASE + k, "usedOn": sorted(set(v)), "inMediaManager": k in in_mm}
    for k, v in sorted(referenced.items())
]
json.dump(refs, open(os.path.join(REPO, "pages/referenced-media.json"), "w"), indent=2)
print("referenced media:", len(refs), "| not in Media Manager:", sum(1 for r in refs if not r["inMediaManager"]))
