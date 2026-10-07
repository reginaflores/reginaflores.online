"""Work elsewhere online: press, publications, exhibitions, videos, code, teaching, references.

Reads _data/online.json (research results) and writes _data/elsewhere.json.
Excluded on purpose: recent consulting/workshop repos (client names), personal repos,
the Summer Search interview (pending review), and anything not found.
"""
import json, re, subprocess, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"

SECTIONS = {"press": "Press", "papers": "Publications", "talks_exhibitions": "Exhibitions & awards",
            "projects_elsewhere": "Project sites", "videos": "Videos", "github": "Code", "teaching": "Teaching"}

EXCLUDE_TITLES = {
    # recent consulting / workshop material (client names) and non-archive repos
    "AIConsulting", "reginaflores.online", "AI_Workshop_June_3", "Decoded", "ai-integration-twopager",
    "ai-workshop-slides", "research-analyst", "AI_Workshop", "AI-workshops-Enterprise", "AI_Workshop_Buckley",
    "test-slides", "MetForMoms", "MFADT_Assessment", "MFADT Curriculum Assessment 2025–2026 dashboard", "SpotifyAPI",
}
EXCLUDE_SOURCES = {"Summer Search"}

# extra text per project so links pick up the same tags as the work itself
PROJECT_HINTS = {
    "Data Selfie": "Data Selfie Hang Do Thi Duc data visualization machine learning algorithms facebook api social data",
    "Holobiont Urbanism": "Holobiont Urbanism Kevin Slavin Chris Woebken Christopher Mason Ben Berman MIT Media Lab microbes bacteria bees beehives DNA metagenomic city urban data visualization maps",
    "Rappers Delight / The HipHop Project": "The Met Metropolitan Museum Met Media Lab hip hop api music",
    "Smart Spirulina System": "spirulina algae Terreform One Jimmy Tang Mitchell Joachim plants sensors arduino",
    "Parsons teaching": "teaching course Parsons",
    "The Met MediaLab": "The Met Metropolitan Museum Met Media Lab api",
    "<META>Methods": "The Met Metropolitan Museum algorithms data visualization",
    "Synergy": "performance dance openFrameworks",
    "microMACRO": "cosmos scale openFrameworks",
}

DATAX = [
    {"title": "Data Selfie (DATA X)", "date": "2016-12-12", "url": "https://github.com/d4t4x/data-selfie",
     "description": "Source for Data Selfie, the browser extension that tracks your own Facebook use and shows what machine learning infers about you. Built by DATA X.", "project": "Data Selfie"},
    {"title": "Data Selfie image classification (DATA X)", "date": "2017-12-23", "url": "https://github.com/d4t4x/data-selfie-image-classification",
     "description": "Image classification component for the Data Selfie extension. DATA X.", "project": "Data Selfie"},
    {"title": "Fuzzify.me (DATA X)", "date": "2018-02-02", "url": "https://github.com/d4t4x/facebook-cleaner",
     "description": "A browser extension that cleans out a Facebook user's ad preferences and shows the stream of ads they receive. DATA X.", "project": "Data Selfie"},
    {"title": "Tracked (DATA X)", "date": "2018-11-06", "url": "https://github.com/d4t4x/tracked-game",
     "description": "Assets for Tracked, a large-scale role-playing game about the data sharing economy. DATA X.", "project": "Data Selfie"},
]

REFERENCES = [
    {"title": "What is BioDesign? — William Myers", "source": "BioDesign: Nature + Science + Creativity (MoMA, 2012)",
     "date": "2012", "url": "https://www.moma.org/docs/publication_pdf/3167/BioDesign_PREVIEW.pdf",
     "description": "William Myers' short essay introducing biodesign — design that incorporates living organisms — from his book BioDesign. A key influence on the bio design work in this archive.",
     "project": "Bio Design"},
    {"title": "William Myers — Publications", "source": "william-myers.com",
     "date": "", "url": "https://www.william-myers.com/publications",
     "description": "William Myers' own list of his books and essays on biodesign, including BioDesign (MoMA / Thames & Hudson, 2012; revised 2018, 2022).",
     "project": "Bio Design"},
    {"title": "Biodesign: A Symbiotic Future — William Myers", "source": "UrbanNext",
     "date": "", "url": "https://urbannext.net/biodesign-a-symbiotic-future/",
     "description": "William Myers on biodesign as collaboration between living systems and the built environment.",
     "project": "Bio Design"},
]

slug_seen = set()


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "item"
    base, i = s, 2
    while s in slug_seen:
        s, i = f"{base}-{i}", i + 1
    slug_seen.add(s)
    return s


def vimeo_thumb(url):
    q = "https://vimeo.com/api/oembed.json?width=640&url=" + urllib.parse.quote(url, safe="")
    out = subprocess.run(["curl", "-s", "--max-time", "20", q], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except Exception:
        return {}


def main():
    raw = json.loads((DATA / "online.json").read_text())
    items = []
    for key, label in SECTIONS.items():
        for x in raw.get(key, []):
            if key == "teaching" or x.get("project") == "Parsons teaching":
                continue  # courses have their own pages (_tools/courses.py)
            if x.get("title") in EXCLUDE_TITLES or (x.get("source") or "") in EXCLUDE_SOURCES:
                continue
            if "NOT FOUND" in (x.get("note") or ""):
                continue
            if key == "videos" and "vimeo.com/user" in x.get("url", ""):
                continue  # channel link itself
            href = x["url"]
            dead = (x.get("note") or "").startswith("DEAD")
            if dead:
                href = "https://web.archive.org/web/2017/" + href
            items.append({"kind": "link", "section": label, "title": x["title"].strip(), "source": x.get("source", ""),
                          "date": "", "year": str(x.get("date") or "")[:4], "sortdate": str(x.get("date") or ""),
                          "href": href, "dead": dead, "description": x.get("description", ""),
                          "project": x.get("project") or "", "verified": bool(x.get("verified"))})
    for r in DATAX:
        items.append({"kind": "link", "section": "Code", "title": r["title"], "source": "GitHub (DATA X)",
                      "date": "", "year": r["date"][:4], "sortdate": r["date"], "href": r["url"], "dead": False,
                      "description": r["description"], "project": r["project"], "verified": True})
    for r in REFERENCES:
        items.append({"kind": "link", "section": "Influences & references", "title": r["title"], "source": r["source"],
                      "date": "", "year": r["date"], "sortdate": r["date"], "href": r["url"], "dead": False,
                      "description": r["description"], "project": r["project"], "verified": True})

    # Vimeo thumbnails (downloaded so the archive does not depend on Vimeo's CDN)
    vids = [i for i in items if i["section"] == "Videos" and "vimeo.com" in i["href"]]
    with ThreadPoolExecutor(8) as ex:
        metas = list(ex.map(lambda i: vimeo_thumb(i["href"]), vids))
    (ROOT / "media/vimeo").mkdir(parents=True, exist_ok=True)
    for i, m in zip(vids, metas):
        vid = re.search(r"vimeo\.com/(?:video/)?(\d+)", i["href"])
        if not (m.get("thumbnail_url") and vid):
            continue
        dest = ROOT / f"media/vimeo/{vid.group(1)}.jpg"
        if not dest.exists():
            subprocess.run(["curl", "-s", "--max-time", "30", "-o", str(dest), m["thumbnail_url"]])
            try:
                im = Image.open(dest).convert("RGB"); im.thumbnail((640, 640)); im.save(dest, quality=78)
            except Exception:
                dest.unlink(missing_ok=True); continue
        i["thumb"] = f"/media/vimeo/{vid.group(1)}.jpg"
        i["vimeo_id"] = vid.group(1)
        i["duration"] = m.get("duration")

    for i in items:
        i["url"] = "/elsewhere/" + slugify(i["title"])
        i["text"] = " ".join([i["title"], i["source"], i["description"], i["project"], PROJECT_HINTS.get(i["project"], "")])
    (DATA / "elsewhere.json").write_text(json.dumps(items, indent=1, ensure_ascii=False))
    from collections import Counter
    print(len(items), "items", Counter(i["section"] for i in items), sum(1 for i in vids if i.get("thumb")), "video thumbs")


if __name__ == "__main__":
    main()
