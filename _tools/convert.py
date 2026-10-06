"""Convert the Squarespace JSON export in _data/ into clean HTML fragments + an image manifest.

Output: _data/clean.json  [{kind, url, title, date, categories, tags, html, images, thumb, text}]
        _data/media.json  {asset_id: source_url}
"""
import json, re, html as H
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"
ID_RE = re.compile(r"/(\d{13}-[A-Z0-9]{20})/([^/?#]+)")
media = {}


def local_img(url):
    """Map a squarespace-cdn image URL to /media/<id>.<ext>; record it for download."""
    if not url:
        return None
    m = ID_RE.search(url)
    if not m:
        return None
    aid, name = m.groups()
    media[aid] = re.sub(r"\?.*", "", url).replace("/content/v1/", "/content/")
    return f"/media/{aid}"


def img_src(tag):
    return tag.get("data-src") or tag.get("data-image") or tag.get("src")


ALLOWED = {"a": ["href", "title"], "img": ["src", "alt"], "iframe": ["src", "allowfullscreen", "allow"],
           "td": ["colspan", "rowspan"], "th": ["colspan", "rowspan"]}


def scrub(node):
    """Strip squarespace classes/styles/data attributes from a subtree."""
    for t in node.find_all(True):
        keep = ALLOWED.get(t.name, [])
        for a in list(t.attrs):
            if a not in keep:
                del t.attrs[a]
        if t.name == "a" and t.get("href", "").startswith("/s/"):
            t.attrs.pop("href")  # links to deleted Squarespace file uploads
            t.name = "span"
    for t in node.find_all(["script", "style", "noscript", "xml", "meta", "link"]):
        t.decompose()
    for c in node.find_all(string=lambda x: isinstance(x, Comment)):
        c.extract()
    for t in node.find_all(["span", "div"]):  # unwrap empty formatting wrappers
        if not t.attrs:
            t.unwrap()
    return node


def clean_src(src):
    """Drop Squarespace-added embed params and repair the query string."""
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    if src.startswith("//"):
        src = "https:" + src
    if "?" not in src and "&" in src:
        src = src.replace("&", "?", 1)
    u = urlsplit(src)
    q = [(k, v) for k, v in parse_qsl(u.query) if k not in ("wmode", "enablejsapi", "api")]
    return urlunsplit((u.scheme or "https", u.netloc, u.path, urlencode(q), ""))


def video_html(block):
    w = block.select_one("[data-html]")
    raw = H.unescape(w["data-html"]) if w else ""
    m = re.search(r'src="([^"]+)"', raw)
    if not m:
        return ""
    src = m.group(1).replace("&amp;", "&")
    if src.startswith("//"):
        src = "https:" + src
    src = clean_src(src)
    return f'<div class="video"><iframe src="{H.escape(src)}" loading="lazy" allowfullscreen allow="fullscreen; picture-in-picture"></iframe></div>'


def figure(src, caption=""):
    s = local_img(src)
    if not s:
        return ""
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return f'<figure><img src="{s}" alt="" loading="lazy">{cap}</figure>'


def convert_body(body):
    soup = BeautifulSoup(body or "", "html.parser")
    out, images = [], []
    blocks = soup.select(".sqs-block")
    if not blocks:
        frag = scrub(soup)
        for im in frag.find_all("img"):
            s = local_img(im.get("src"))
            if s:
                im["src"] = s; im["loading"] = "lazy"; images.append(s)
            else:
                im.decompose()
        return str(frag), images
    for b in blocks:
        cls = b.get("class", [])
        content = b.select_one(".sqs-block-content") or b
        if "sqs-block-video" in cls or "video-block" in cls or "embed-block" in cls or "sqs-block-embed" in cls:
            v = video_html(b)
            if v:
                out.append(v)
            continue
        if "gallery-block" in cls or "sqs-block-gallery" in cls:
            imgs = [im for im in b.find_all("img") if im.find_parent("noscript") is None]
            figs, seen = [], set()
            for im in imgs:
                s = local_img(img_src(im))
                if s and s not in seen:
                    seen.add(s)
                    figs.append(f'<a href="{s}"><img src="{s}" alt="" loading="lazy"></a>'); images.append(s)
            if len(figs) == 1:
                out.append(figs[0].replace("<a ", '<figure><a ', 1).replace("</a>", "</a></figure>"))
            elif figs:
                out.append('<div class="gallery">' + "".join(figs) + "</div>")
            continue
        if "image-block" in cls or "sqs-block-image" in cls:
            im = next((i for i in b.find_all("img") if i.find_parent("noscript") is None), None) or b.find("img")
            cap_el = b.select_one(".image-caption")
            cap = "".join(str(c) for c in scrub(cap_el).contents).strip() if cap_el else ""
            f = figure(img_src(im) if im else None, cap)
            if f:
                out.append(f); images.append(local_img(img_src(im)))
            continue
        if "sqs-block-code" in cls or "code-block" in cls:
            if content.find("iframe"):
                src = clean_src(content.find("iframe").get("src", ""))
                out.append(f'<div class="video"><iframe src="{H.escape(src)}" loading="lazy" allowfullscreen></iframe></div>')
            else:
                out.append("<pre><code>" + H.escape(content.get_text()) + "</code></pre>")
            continue
        # html / text and anything else: keep cleaned markup
        frag = scrub(content)
        for im in frag.find_all("img"):
            s = local_img(img_src(im))
            if s:
                im.attrs = {"src": s, "alt": "", "loading": "lazy"}; images.append(s)
            else:
                im.decompose()
        inner = "".join(str(c) for c in frag.contents).strip()
        if inner:
            out.append(inner)
    return "\n".join(out), images


def text_of(html_s):
    return re.sub(r"\s+", " ", BeautifulSoup(html_s, "html.parser").get_text(" ")).strip()


def main():
    posts = json.loads((DATA / "posts.json").read_text())
    pages = [dict(pg, kind="page") for pg in json.loads((DATA / "pages.json").read_text())]
    pages += [dict(pg, kind="project") for pg in json.loads((DATA / "projects.json").read_text())]
    clean = []
    for p in posts:
        html_s, imgs = convert_body(p["body"])
        thumb = local_img(p.get("assetUrl")) or (imgs[0] if imgs else None)
        d = datetime.fromtimestamp(p["publishOn"] / 1000, tz=timezone.utc)
        clean.append({"kind": "post", "url": p["fullUrl"], "title": p["title"].strip(),
                      "date": d.strftime("%Y-%m-%d"), "categories": p.get("categories") or [],
                      "tags": p.get("tags") or [], "html": html_s, "thumb": thumb,
                      "text": text_of(html_s)[:4000]})
    for pg in pages:
        if not pg.get("title"):
            continue
        parts, imgs = [], []
        if pg.get("mainContent"):
            h, i = convert_body(pg["mainContent"]); parts.append(h); imgs += i
        for it in pg.get("items") or []:
            h, i = convert_body(it.get("body") or "")
            s = local_img(it.get("assetUrl"))
            if s and s not in i:
                h = f'<figure><img src="{s}" alt="" loading="lazy"></figure>' + h; i.insert(0, s)
            t = (it.get("title") or "").strip()
            parts.append((f"<h3>{H.escape(t)}</h3>" if t else "") + h); imgs += i
        html_s = "\n".join(parts)
        clean.append({"kind": pg["kind"], "url": pg["url"], "title": pg["title"].strip(), "date": "",
                      "categories": [], "tags": [], "html": html_s,
                      "thumb": imgs[0] if imgs else None, "text": text_of(html_s)[:4000]})
    (DATA / "clean.json").write_text(json.dumps(clean, indent=1))
    (DATA / "media.json").write_text(json.dumps(media, indent=1))
    print(len(clean), "entries,", len(media), "images referenced")


if __name__ == "__main__":
    main()
