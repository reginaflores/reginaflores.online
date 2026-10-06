"""Build the static archive site from _data/clean.json into the repo root.

Old Squarespace paths are kept (/blog/2016/5/3/slug, /blog/category/Thesis+2, /sss ...)
so the old domain can later redirect path-for-path.
"""
import json, re, shutil, html as H
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
from topics import derive, LEGACY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"
SITE = "https://reginaflores.online"
NAME = "Regina Flores Mir"
INTRO = ("A working notebook of design and technology projects, 2014–2016: "
         "Parsons MFA studio work, research, prototypes and experiments in creative code, "
         "bio design, data and physical computing, plus earlier projects from science and finance.")
SKIP_PAGES = {"/projects", "/about"}  # empty index page; /about is rebuilt below at /aboutme
CURRENT = "https://reginafloresmir.ai"
ABOUT = """
<section class="about">
  <p class="crumb"><a href="/">Archive</a> / About</p>
  <h1 class="quote"><span>I love science.</span> <span>I love data.</span> <span>I love coding.</span></h1>
  <p class="quote-sub">I live at the intersection of design and technology.</p>
  <div class="about-body">
    <figure class="portrait"><img src="{photo}" alt="Regina Flores Mir"></figure>
    <div class="content">
      <p>This archive collects the work I made and documented between 2014 and 2016, most of it during my MFA in Design and Technology at Parsons: studio projects, research, prototypes and experiments in creative code, bio design, data and physical computing.</p>
      <p>I began my career as a research analyst in astrophysics. At NASA Ames Research Center I worked on SOFIA, an airborne infrared observatory aboard a Boeing 747. I also studied the Cosmic Microwave Background at the National Radio Astronomy Observatory, and star formation in extragalactic molecular clouds at the National Astronomy and Ionosphere Center.</p>
      <p>I then spent more than five years on Wall Street bridging quants and sales, first at Goldman Sachs in Equity Prime Brokerage and later at JP Morgan on the Foreign Exchange, Rates and Commodities desk. In 2012 I joined the Cue Group, a consultancy and insight lab, as Director of Analytics.</p>
      <p>I hold a B.A. in Physics from Barnard College of Columbia University, an M.A. in Statistics from Columbia University, and an MFA in Design and Technology from Parsons.</p>
    </div>
  </div>
  <a class="current" href="{current}"><span class="label">Current work</span><span class="url">reginafloresmir.ai</span><span class="arrow">→</span></a>
</section>"""

files = json.loads((DATA / "media_files.json").read_text())
entries = json.loads((DATA / "clean.json").read_text())


def media_path(p):
    aid = p.rsplit("/", 1)[-1]
    f = files.get(aid)
    return f"/media/{f}" if f else None


def fix_media(html_s):
    def rep(m):
        p = media_path(m.group(1))
        return p or "/media/missing.svg"
    return re.sub(r'(/media/\d{13}-[A-Z0-9]{20})', rep, html_s)


def thumb(p):
    """600px thumbnail for listing cards."""
    src = media_path(p) if p else None
    if not src:
        return None
    name = Path(src).name
    out = ROOT / "media/thumb" / (Path(name).stem + ".jpg")
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(ROOT / src.lstrip("/"))
        im.seek(0)
        im = im.convert("RGB"); im.thumbnail((640, 640))
        im.save(out, quality=78, optimize=True, progressive=True)
    return "/media/thumb/" + out.name


def slug_path(url):
    return ROOT / url.strip("/") / "index.html"


def fmt_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y") if d else ""


def cat_url(c):
    return "/blog/category/" + c.replace(" ", "+")


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower().replace("&", "and")).strip("-")


def tag_url(t):
    return "/tags/" + slugify(t)


CSS_V = "9"


def page(title, body, desc=INTRO, url="/", og_img=None, kind="website"):
    t = f"{H.escape(title)} — {NAME} Archive" if title else f"{NAME} — Archive"
    img = f'<meta property="og:image" content="{SITE}{og_img}">' if og_img else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{H.escape(desc[:300])}">
<link rel="canonical" href="{SITE}{url if url.endswith('/') else url + '/'}">
<meta property="og:type" content="{kind}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{H.escape(desc[:300])}">
<meta property="og:url" content="{SITE}{url}">
{img}
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Flex:opsz,wdth,wght@8..144,25..151,300..1000&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={CSS_V}">
</head>
<body>
<header class="site"><div class="bar">
  <a class="brand" href="/"><span class="name">{NAME}</span><span class="sub">Archive</span></a>
  <nav><a href="/#topics">Topics</a><a href="/#projects">Projects</a><a href="/aboutme/">About</a></nav>
</div></header>
<main>
{body}
</main>
<footer class="site">
  <span>{NAME} · Archive of work, 2014–2016</span>
  <a href="{CURRENT}">Current work: reginafloresmir.ai →</a>
  <a href="#top" onclick="window.scrollTo(0,0);return false">Back to top ↑</a>
</footer>
</body>
</html>
"""


def card(e):
    th = thumb(e["thumb"])
    img = f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="noimg"></div>'
    when = datetime.strptime(e["date"], "%Y-%m-%d").strftime("%b %-d, %Y") if e["date"] else ""
    pill = f'<span class="pill">{when}</span>' if when else ""
    meta = ", ".join(e["categories"])
    return (f'<a class="card" href="{e["url"]}/" data-search="{H.escape((e["title"] + " " + " ".join(e["categories"] + e["tags"]) + " " + e["text"][:1500]).lower())}">'
            f'<div class="thumb">{img}{pill}</div><h3>{H.escape(e["title"])}</h3>' + (f'<p class="meta">{H.escape(meta)}</p>' if meta else "") + "</a>")


def listing(items, by_year=True):
    if not by_year:
        return '<div class="grid">' + "".join(card(e) for e in items) + "</div>"
    out, groups = [], defaultdict(list)
    for e in items:
        groups[e["date"][:4]].append(e)
    for y in sorted(groups, reverse=True):
        out.append(f'<section class="year" data-year="{y}"><h2 class="yr">{y} <span>{len(groups[y])}</span></h2>'
                   f'<div class="grid">{"".join(card(e) for e in groups[y])}</div></section>')
    return "".join(out)


def chips(names, fn, counts=None, cls="chip"):
    return "".join(f'<a class="{cls}" href="{fn(n)}/">{H.escape(n)}{f" <span>{counts[n]}</span>" if counts else ""}</a>' for n in names)


def write(path, s):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s)


def main():
    for d in ("blog", "tags"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    posts = sorted([e for e in entries if e["kind"] == "post"], key=lambda e: e["date"], reverse=True)
    pages = [e for e in entries if e["kind"] == "page" and e["url"] not in SKIP_PAGES and (e["text"] or e["thumb"])]
    for e in entries:
        e["html"] = fix_media(e["html"])
    # fine-grained tags derived from full post text (+ original Squarespace tags)
    for p in posts:
        p["full"] = re.sub(r"\s+", " ", BeautifulSoup(p["html"], "html.parser").get_text(" "))
    derived, tag_groups, _ = derive([dict(p, text=p["full"]) for p in posts])
    for p in posts:
        p["tags"] = derived[p["url"]]
    cats, tags = defaultdict(list), defaultdict(list)
    for p in posts:
        for c in p["categories"]:
            cats[c].append(p)
        for t in p["tags"]:
            tags[t].append(p)
    cat_names = sorted(cats, key=lambda c: (-len(cats[c]), c))
    tag_names = sorted(tags, key=str.lower)

    # post pages
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        nav = '<nav class="pn">' + (f'<a class="prev" href="{older["url"]}/"><span>← Older</span>{H.escape(older["title"])}</a>' if older else "<span></span>") + \
              (f'<a class="next" href="{newer["url"]}/"><span>Newer →</span>{H.escape(newer["title"])}</a>' if newer else "<span></span>") + "</nav>"
        meta = chips(p["categories"], cat_url, cls="chip cat") + chips(p["tags"], tag_url)
        body = (f'<article class="post"><p class="crumb"><a href="/">Archive</a> / {p["date"][:4]}</p>'
                f'<h1>{H.escape(p["title"])}</h1><p class="date">{fmt_date(p["date"])}</p>'
                f'<div class="chips">{meta}</div><div class="content">{p["html"]}</div></article>{nav}')
        og = media_path(p["thumb"]) if p["thumb"] else None
        write(slug_path(p["url"]), page(p["title"], body, p["text"][:200] or INTRO, p["url"], og, "article"))

    # project / other pages
    for pg in pages:
        if pg["url"] == "/aboutme":
            photo = "/assets/headshot.jpg"  # same headshot as reginafloresmir.ai
            write(slug_path(pg["url"]), page("About", ABOUT.format(photo=photo, current=CURRENT),
                  "I love science. I love data. I love coding. I live at the intersection of design and technology.", pg["url"]))
            continue
        body = (f'<article class="post"><p class="crumb"><a href="/">Archive</a> / Projects</p>'
                f'<h1>{H.escape(pg["title"])}</h1><div class="content">{pg["html"]}</div></article>')
        write(slug_path(pg["url"]), page(pg["title"], body, pg["text"][:200] or INTRO, pg["url"]))

    # category & tag pages
    for c in cat_names:
        body = (f'<section class="head"><p class="crumb"><a href="/">Archive</a> / Topic</p><h1>{H.escape(c)}</h1>'
                f'<p class="lede">{len(cats[c])} posts</p></section>{listing(cats[c])}')
        write(slug_path(cat_url(c)), page(c, body, f"Posts about {c} from {NAME}'s archive.", cat_url(c)))
    group_of = {t: g for g, ts in tag_groups.items() for t in ts}
    for t in tag_names:
        co = defaultdict(int)
        for p in tags[t]:
            for o in p["tags"]:
                if o != t:
                    co[o] += 1
        related = sorted(co, key=lambda o: (-co[o], o))[:14]
        rel = (f'<div class="related"><p class="label">Often appears with</p><div class="chips">'
               f'{chips(related, tag_url, co)}</div></div>') if related else ""
        body = (f'<section class="head"><p class="crumb"><a href="/">Archive</a> / {H.escape(group_of.get(t, "Tags"))}</p>'
                f'<h1>{H.escape(t)}</h1><p class="lede">{len(tags[t])} posts</p>{rel}</section>{listing(tags[t])}')
        write(slug_path(tag_url(t)), page(t, body, f"Posts about {t} from {NAME}'s archive.", tag_url(t)))
    # old Squarespace tag URLs point to their new tag pages
    for old, new in LEGACY.items():
        if new in tags:
            dest = tag_url(new) + "/"
            write(ROOT / "blog/tag" / old / "index.html",
                  f'<!doctype html><meta charset="utf-8"><title>Moved</title><link rel="canonical" href="{SITE}{dest}">'
                  f'<meta http-equiv="refresh" content="0; url={dest}"><a href="{dest}">{H.escape(new)}</a>')

    # home (also served at /blog/)
    years = sorted({p["date"][:4] for p in posts})
    proj = "".join(card(dict(pg, date="", categories=[])) for pg in pages if pg["url"] != "/aboutme")
    home = f"""
<section class="hero">
  <h1>Archive</h1>
  <p class="lede">{INTRO}</p>
</section>
<section class="tools" id="posts">
  <label class="search"><span class="sr">Search the archive</span>
    <input id="q" type="search" placeholder="Search {len(posts)} posts — try “bioplastic”, “openFrameworks”, “Terreform”" autocomplete="off">
  </label>
  <p id="count" class="meta" aria-live="polite"></p>
</section>
<div id="results">{listing(posts)}</div>
<section class="topics" id="topics">
  <h2>Topics</h2><div class="chips big">{chips(cat_names, cat_url, {c: len(cats[c]) for c in cat_names})}</div>
  <h2>Drill down</h2>
  <div class="taggroups">{"".join(f'<div class="tg"><h3>{H.escape(g)}</h3><div class="chips">{chips(sorted(ts, key=lambda t: -len(tags[t])), tag_url, {t: len(tags[t]) for t in ts})}</div></div>' for g, ts in tag_groups.items() if ts)}</div>
</section>
<section class="projects" id="projects">
  <h2>Projects &amp; pages</h2><div class="grid">{proj}</div>
</section>
<script>
(() => {{
  const q = document.getElementById('q'), count = document.getElementById('count');
  const cards = [...document.querySelectorAll('#results .card')];
  const run = () => {{
    const terms = q.value.toLowerCase().trim().split(/\\s+/).filter(Boolean);
    let n = 0;
    cards.forEach(c => {{ const hit = terms.every(t => c.dataset.search.includes(t)); c.hidden = !hit; if (hit) n++; }});
    document.querySelectorAll('#results .year').forEach(s => s.hidden = !s.querySelector('.card:not([hidden])'));
    count.textContent = terms.length ? `${{n}} matching post${{n === 1 ? '' : 's'}}` : '';
    const u = new URL(location); terms.length ? u.searchParams.set('q', q.value) : u.searchParams.delete('q');
    history.replaceState(null, '', u);
  }};
  q.addEventListener('input', run);
  const init = new URLSearchParams(location.search).get('q'); if (init) {{ q.value = init; run(); }}
}})();
</script>"""
    write(ROOT / "index.html", page("", home))
    write(ROOT / "blog/index.html", page("Posts", home, url="/blog"))

    # 404, sitemap, robots
    write(ROOT / "404.html", page("Not found", '<section class="head"><h1>Not found</h1><p class="lede">That page isn’t in the archive. <a href="/">Browse all posts</a> or search from the home page.</p></section>'))
    urls = ["/"] + [p["url"] + "/" for p in posts] + [pg["url"] + "/" for pg in pages] + [cat_url(c) + "/" for c in cat_names] + [tag_url(t) + "/" for t in tag_names]
    write(ROOT / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built {len(posts)} posts, {len(pages)} pages, {len(cat_names)} topics, {len(tag_names)} tags")


if __name__ == "__main__":
    main()
