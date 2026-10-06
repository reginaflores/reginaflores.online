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
from entities import find, PEOPLE, INSTITUTIONS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"
SITE = "https://reginaflores.online"
NAME = "Regina Flores Mir"
INTRO = ("Everything I have made, written and shared, in one place: from astrophysics and Wall Street "
         "to the Parsons MFA notebook, Holobiont Urbanism, Data Selfie and teaching. "
         "Projects, papers, press, videos and code, searchable by topic, person and place.")
SKIP_PAGES = {"/projects", "/about"}  # empty index page; /about is rebuilt below at /aboutme
CURRENT = "https://reginafloresmir.ai"
ABOUT = """
<section class="about">
  <p class="crumb"><a href="/">Archive</a> / About</p>
  <h1 class="quote"><span>Science</span> <span>Data</span> <span>Code</span></h1>
  <p class="quote-sub">I live at the intersection of design and technology.</p>
  <div class="about-body">
    <figure class="portrait"><img src="{photo}" alt="Regina Flores Mir"></figure>
    <div class="content">
      <p>This archive collects my work in one place. At its core is the notebook I kept during my MFA in Design and Technology at Parsons (2014–2016): studio projects, research, prototypes and experiments in creative code, bio design, data and physical computing. Around it are my earlier research papers, my projects, and the work out in the world since: publications, exhibitions, press, videos, code and teaching.</p>
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
    if p and p.startswith(("/media/covers/", "/media/vimeo/")):
        return p
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


def person_url(n):
    return "/people/" + slugify(n)


def inst_url(n):
    return "/places/" + slugify(n)


CSS_V = "13"


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
  <nav><a href="/#topics">Topics</a><a href="/#projects">Projects</a><a href="/papers/">Papers</a><a href="/elsewhere/">Elsewhere</a><a href="/aboutme/">About</a></nav>
</div></header>
<main>
{body}
</main>
<footer class="site">
  <span>{NAME} · Archive of work</span>
  <a href="{CURRENT}">Current work: reginafloresmir.ai →</a>
  <span class="credit">Design inspired by <a href="https://www.theshed.org">The Shed</a></span>
  <a href="#top" onclick="window.scrollTo(0,0);return false">Back to top ↑</a>
</footer>
</body>
</html>
"""


LINK_ORDER = ["Publications", "Exhibitions & awards", "Press", "Videos", "Code", "Teaching", "Project sites", "Influences & references"]


def card(e):
    th = thumb(e["thumb"])
    img = f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="noimg"></div>'
    when = datetime.strptime(e["date"], "%Y-%m-%d").strftime("%b %-d, %Y") if e.get("date") else ""
    if e.get("kind") == "doc":
        when = " · ".join(x for x in (e["doc_type"], e["year"]) if x)
    if e.get("kind") == "link":
        when = " · ".join(x for x in (e["section"].rstrip("s") if e["section"] in ("Videos",) else "", e["year"]) if x)
        if not th:
            img = f'<div class="textcard"><span>{H.escape(e["source"] or e["section"])}</span></div>'
        e = dict(e, context=e["source"])
    pill = f'<span class="pill">{when}</span>' if when else ""
    meta = ", ".join(e.get("categories") or []) or e.get("context", "")
    return (f'<a class="card" href="{e["url"]}/" data-key="{e["url"]}">'
            f'<div class="thumb">{img}{pill}</div><h3>{H.escape(e["title"])}</h3>' + (f'<p class="meta">{H.escape(meta)}</p>' if meta else "") + "</a>")


def listing(items, by_year=True):
    if not by_year:
        return '<div class="grid">' + "".join(card(e) for e in items) + "</div>"
    groups = defaultdict(list)
    for e in items:
        key = e["date"][:4] if e.get("kind") == "post" else ("Papers" if e.get("kind") == "doc" else e["section"] if e.get("kind") == "link" else "Projects")
        groups[key].append(e)
    order = sorted((k for k in groups if k.isdigit()), reverse=True) + [k for k in ["Projects", "Papers"] + LINK_ORDER if k in groups]
    out = []
    for k in order:
        label = "Papers &amp; presentations" if k == "Papers" else H.escape(k)
        out.append(f'<section class="year" data-group="{k}"><h2 class="yr">{label} <span>{len(groups[k])}</span></h2>'
                   f'<div class="grid">{"".join(card(e) for e in groups[k])}</div></section>')
    return "".join(out)


def chips(names, fn, counts=None, cls="chip"):
    return "".join(f'<a class="{cls}" href="{fn(n)}/">{H.escape(n)}{f" <span>{counts[n]}</span>" if counts else ""}</a>' for n in names)


def write(path, s):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s)


def main():
    for d in ("blog", "tags", "people", "places", "elsewhere"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    posts = sorted([e for e in entries if e["kind"] == "post"], key=lambda e: e["date"], reverse=True)
    pages = [e for e in entries if e["kind"] in ("page", "project") and e["url"] not in SKIP_PAGES and (e["text"] or e["thumb"])]
    projects = [e for e in pages if e["kind"] == "project"]
    others = [e for e in pages if e["kind"] == "page" and e["url"] != "/aboutme"]
    for e in entries:
        e["html"] = fix_media(e["html"])
    # fine-grained tags derived from full post text (+ original Squarespace tags)
    docs = sorted(json.loads((DATA / "papers.json").read_text()), key=lambda d: (d["year"] or "0000"), reverse=True)
    for d in docs:
        d.update(date="", categories=[], thumb=d["cover"], html="")
    links = json.loads((DATA / "elsewhere.json").read_text())
    links.sort(key=lambda l: l["sortdate"], reverse=True)
    links.sort(key=lambda l: LINK_ORDER.index(l["section"]))
    for l in links:
        l.update(categories=[], html="", thumb=l.get("thumb"))
    tagged = posts + projects + others + docs + links
    for p in tagged:
        p["full"] = p["text"] if p.get("kind") in ("doc", "link") else re.sub(r"\s+", " ", BeautifulSoup(p["html"], "html.parser").get_text(" "))
    derived, tag_groups, _ = derive([dict(p, text=p["full"]) for p in tagged])
    for p in tagged:
        p["tags"] = derived[p["url"]]
    ents = [dict(p, text=p["full"]) for p in tagged]
    ppl_hits, ppl_counts = find(ents, PEOPLE)
    inst_hits, inst_counts = find(ents, INSTITUTIONS)
    people, insts = defaultdict(list), defaultdict(list)
    for p in tagged:
        p["people"], p["insts"] = ppl_hits[p["url"]], inst_hits[p["url"]]
        for n in p["people"]:
            people[n].append(p)
        for n in p["insts"]:
            insts[n].append(p)
    cats, tags = defaultdict(list), defaultdict(list)
    for p in posts:
        for c in p["categories"]:
            cats[c].append(p)
    for p in tagged:
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
                f'<div class="chips">{meta}</div>' + (f'<div class="chips who">{chips(p["people"], person_url, cls="chip person")}{chips(p["insts"], inst_url, cls="chip place")}</div>' if p["people"] or p["insts"] else "") + f'<div class="content">{p["html"]}</div></article>{nav}')
        og = media_path(p["thumb"]) if p["thumb"] else None
        write(slug_path(p["url"]), page(p["title"], body, p["text"][:200] or INTRO, p["url"], og, "article"))

    # project / other pages
    for pg in pages:
        if pg["url"] == "/aboutme":
            photo = "/assets/headshot.jpg"  # same headshot as reginafloresmir.ai
            write(slug_path(pg["url"]), page("About", ABOUT.format(photo=photo, current=CURRENT),
                  "Science. Data. Code. I live at the intersection of design and technology.", pg["url"]))
            continue
        chipline = f'<div class="chips">{chips(pg.get("tags") or [], tag_url)}</div>' if pg.get("tags") else ""
        body = (f'<article class="post"><p class="crumb"><a href="/">Archive</a> / Projects</p>'
                f'<h1>{H.escape(pg["title"])}</h1>{chipline}' + (f'<div class="chips who">{chips(pg["people"], person_url, cls="chip person")}{chips(pg["insts"], inst_url, cls="chip place")}</div>' if pg["people"] or pg["insts"] else "") + f'<div class="content">{pg["html"]}</div></article>')
        write(slug_path(pg["url"]), page(pg["title"], body, pg["text"][:200] or INTRO, pg["url"]))

    # papers & presentations
    for d in docs:
        bits = [d["doc_type"], d["year"], d["context"]]
        meta = " · ".join(H.escape(b) for b in bits if b)
        withp = f'<p class="date">With {H.escape(d["collaborators"])}</p>' if d["collaborators"] else ""
        chipline = f'<div class="chips">{chips(d["tags"], tag_url)}</div>' if d["tags"] else ""
        body = (f'<article class="post doc"><p class="crumb"><a href="/">Archive</a> / <a href="/papers/">Papers</a><a href="/elsewhere/">Elsewhere</a></p>'
                f'<h1>{H.escape(d["title"])}</h1><p class="date">{meta}</p>{withp}{chipline}' + (f'<div class="chips who">{chips(d["people"], person_url, cls="chip person")}{chips(d["insts"], inst_url, cls="chip place")}</div>' if d["people"] or d["insts"] else "") +
                f'<p><a class="current small" href="{d["pdf"]}"><span class="label">Open PDF</span><span class="url">{d["pages"]} pages · {d["mb"]} MB</span><span class="arrow">↗</span></a></p>'
                f'<object class="pdf" data="{d["pdf"]}#view=FitH" type="application/pdf"><a href="{d["pdf"]}"><img src="{d["cover"]}" alt=""></a></object></article>')
        write(slug_path(d["url"]), page(d["title"], body, f'{d["doc_type"]} by {NAME}: {d["title"]}. {d["context"]}.', d["url"], d["cover"], "article"))
    write(ROOT / "papers/index.html", page("Papers & presentations",
          f'<section class="head"><p class="crumb"><a href="/">Archive</a> / Papers</p><h1>Papers &amp; presentations</h1>'
          f'<p class="lede">{len(docs)} papers, decks and lab reports, from physics and statistics to the Parsons MFA.</p></section>'
          f'<div class="grid">{"".join(card(d) for d in docs)}</div>', url="/papers"))

    # elsewhere: press, publications, exhibitions, videos, code, teaching
    for l in links:
        chipline = f'<div class="chips">{chips(l["tags"], tag_url)}</div>' if l["tags"] else ""
        wholine = (f'<div class="chips who">{chips(l["people"], person_url, cls="chip person")}{chips(l["insts"], inst_url, cls="chip place")}</div>' if l["people"] or l["insts"] else "")
        meta = " · ".join(H.escape(x) for x in (l["section"], l["source"], l["sortdate"]) if x)
        player = (f'<div class="video"><iframe src="https://player.vimeo.com/video/{l["vimeo_id"]}" loading="lazy" allow="fullscreen; picture-in-picture" allowfullscreen></iframe></div>') if l.get("vimeo_id") else ""
        note = '<p class="date">This page is no longer online; the link opens an archived copy.</p>' if l.get("dead") else ""
        go = "Watch on Vimeo" if l.get("vimeo_id") else "View on GitHub" if "github.com" in l["href"] else "Open"
        body = (f'<article class="post"><p class="crumb"><a href="/">Archive</a> / <a href="/elsewhere/">Elsewhere</a></p>'
                f'<h1>{H.escape(l["title"])}</h1><p class="date">{meta}</p>{chipline}{wholine}'
                f'<div class="content"><p>{H.escape(l["description"])}</p>{note}{player}</div>'
                f'<p><a class="current small" href="{H.escape(l["href"])}" rel="noopener"><span class="label">{go}</span><span class="url">{H.escape(l["source"] or "Link")}</span><span class="arrow">↗</span></a></p></article>')
        write(slug_path(l["url"]), page(l["title"], body, l["description"] or l["title"], l["url"], l.get("thumb")))
    write(ROOT / "elsewhere/index.html", page("Elsewhere",
          f'<section class="head"><p class="crumb"><a href="/">Archive</a> / Elsewhere</p><h1>Elsewhere</h1>'
          f'<p class="lede">The work out in the world: publications, exhibitions, press, videos, code and teaching.</p></section>{listing(links)}', url="/elsewhere"))

    # people & institutions
    for table, url_fn, label, coll in ((people, person_url, "People", "people"), (insts, inst_url, "Institutions &amp; places", "insts")):
        for n, items in table.items():
            co = defaultdict(int)
            for p in items:
                for o in p[coll]:
                    if o != n:
                        co[o] += 1
            related = sorted(co, key=lambda o: (-co[o], o))[:14]
            rel = (f'<div class="related"><p class="label">Appears alongside</p><div class="chips">{chips(related, url_fn, co)}</div></div>') if related else ""
            body = (f'<section class="head"><p class="crumb"><a href="/">Archive</a> / {label}</p><h1>{H.escape(n)}</h1>'
                    f'<p class="lede">Mentioned in {len(items)} {"entry" if len(items) == 1 else "entries"}</p>{rel}</section>{listing(items)}')
            write(slug_path(url_fn(n)), page(n, body, f"{n} in {NAME}'s archive of work.", url_fn(n)))
    ppl_names = sorted(people, key=lambda n: (-len(people[n]), n))
    inst_names = sorted(insts, key=lambda n: (-len(insts[n]), n))

    # search index: full text of everything, loaded on demand
    facets = ([{"n": c, "u": cat_url(c) + "/", "k": "Topic", "c": len(cats[c])} for c in cat_names] +
              [{"n": t, "u": tag_url(t) + "/", "k": "Tag", "c": len(tags[t])} for t in tag_names] +
              [{"n": n, "u": person_url(n) + "/", "k": "Person", "c": len(people[n])} for n in ppl_names] +
              [{"n": n, "u": inst_url(n) + "/", "k": "Place", "c": len(insts[n])} for n in inst_names])
    index = [{"u": p["url"], "t": (p["title"] + " " + " ".join((p.get("categories") or []) + p["tags"] + p["people"] + p["insts"]) + " " + p.get("context", "") + " " + p["full"][:12000]).lower()}
             for p in tagged]
    write(ROOT / "search.json", json.dumps({"facets": facets, "index": index}, ensure_ascii=False, separators=(",", ":")))

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
    proj = "".join(card(dict(pg, date="", categories=[])) for pg in projects)
    more = "".join(card(dict(pg, date="", categories=[])) for pg in others)
    home = f"""
<section class="hero">
  <h1>Archive</h1>
  <p class="lede">{INTRO}</p>
</section>
<section class="tools" id="posts">
  <label class="search"><span class="sr">Search the archive</span>
    <input id="q" type="search" placeholder="Search everything — try “bioplastic”, “openFrameworks”, “Terreform”" autocomplete="off">
  </label>
  <p class="hint">Searches the full text of every post, project and paper. Add words to narrow it down: <em>bees astoria</em>. Matching people, places and tags appear as shortcuts.</p>
  <div id="suggest" class="chips"></div>
  <p id="count" class="meta" aria-live="polite"></p>
</section>
<div id="results">{listing(posts)}
<section class="year" id="projects" data-group="Projects"><h2 class="yr">Projects <span>{len(projects)}</span></h2><div class="grid">{proj}</div></section>
<section class="year" id="papers" data-group="Papers"><h2 class="yr">Papers &amp; presentations <span>{len(docs)}</span></h2><div class="grid">{"".join(card(d) for d in docs)}</div></section>
<section class="year" data-group="Earlier"><h2 class="yr">Earlier work <span>{len(others)}</span></h2><div class="grid">{more}</div></section>
<div id="elsewhere">{listing(links)}</div>
</div>
<section class="topics" id="topics">
  <h2>Topics</h2><div class="chips big">{chips(cat_names, cat_url, {c: len(cats[c]) for c in cat_names})}</div>
  <h2>People</h2><div class="chips">{chips(ppl_names, person_url, {n: len(people[n]) for n in ppl_names}, cls="chip person")}</div>
  <h2>Institutions &amp; places</h2><div class="chips">{chips(inst_names, inst_url, {n: len(insts[n]) for n in inst_names}, cls="chip place")}</div>
  <h2>Tags</h2>
  <div class="taggroups">{"".join(f'<div class="tg"><h3>{H.escape(g)}</h3><div class="chips">{chips(sorted(ts, key=lambda t: -len(tags[t])), tag_url, {t: len(tags[t]) for t in ts})}</div></div>' for g, ts in tag_groups.items() if ts)}</div>
</section>
<script>
(() => {{
  const q = document.getElementById('q'), count = document.getElementById('count'), sug = document.getElementById('suggest');
  const cards = [...document.querySelectorAll('#results .card')];
  let data = null, loading = null;
  const load = () => loading ||= fetch('/search.json').then(r => r.json()).then(d => (data = d, d));
  const esc = s => s.replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
  const run = async () => {{
    const raw = q.value.trim(), terms = raw.toLowerCase().split(/\\s+/).filter(Boolean);
    const u = new URL(location); raw ? u.searchParams.set('q', raw) : u.searchParams.delete('q'); history.replaceState(null, '', u);
    if (!terms.length) {{ cards.forEach(c => c.hidden = false); document.querySelectorAll('#results .year').forEach(s => s.hidden = false); count.textContent = ''; sug.innerHTML = ''; return; }}
    await load();
    const hit = new Set(data.index.filter(e => terms.every(t => e.t.includes(t))).map(e => e.u));
    let n = 0; cards.forEach(c => {{ const h = hit.has(c.dataset.key); c.hidden = !h; if (h) n++; }});
    document.querySelectorAll('#results .year').forEach(s => s.hidden = !s.querySelector('.card:not([hidden])'));
    count.textContent = `${{n}} match${{n === 1 ? '' : 'es'}}`;
    const f = data.facets.filter(x => terms.every(t => x.n.toLowerCase().includes(t))).slice(0, 10);
    sug.innerHTML = f.map(x => `<a class="chip ${{x.k === 'Person' ? 'person' : x.k === 'Place' ? 'place' : ''}}" href="${{x.u}}"><span class="k">${{x.k}}</span> ${{esc(x.n)}} <span>${{x.c}}</span></a>`).join('');
  }};
  q.addEventListener('focus', load, {{ once: true }});
  q.addEventListener('input', run);
  const init = new URLSearchParams(location.search).get('q'); if (init) {{ q.value = init; run(); }}
}})();
</script>"""
    write(ROOT / "index.html", page("", home))
    write(ROOT / "blog/index.html", page("Posts", home, url="/blog"))

    # 404, sitemap, robots
    write(ROOT / "404.html", page("Not found", '<section class="head"><h1>Not found</h1><p class="lede">That page isn’t in the archive. <a href="/">Browse all posts</a> or search from the home page.</p></section>'))
    urls = ["/"] + [p["url"] + "/" for p in posts] + [pg["url"] + "/" for pg in pages] + [cat_url(c) + "/" for c in cat_names] + [tag_url(t) + "/" for t in tag_names] + ["/papers/"] + [d["url"] + "/" for d in docs] + ["/elsewhere/"] + [l["url"] + "/" for l in links] + [person_url(n) + "/" for n in ppl_names] + [inst_url(n) + "/" for n in inst_names]
    write(ROOT / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built {len(posts)} posts, {len(pages)} pages, {len(cat_names)} topics, {len(tag_names)} tags")


if __name__ == "__main__":
    main()
