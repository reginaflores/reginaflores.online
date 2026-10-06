"""Make web-sized copies of every referenced image in media/ (max 1400px).

Opaque PNGs become JPEGs; images with real transparency stay PNG; GIFs are copied as-is (animation).
Writes _data/media_files.json {asset_id: "id.ext"} for the site builder.
"""
import json, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LIB = Path.home() / "Library/CloudStorage/GoogleDrive-regina.flores@gmail.com/My Drive/Squarespace backup – reginafloresmir.com/Asset Library"
LIST = LIB.parent / "squarespace_assets_list.tsv"
OUT, CACHE = ROOT / "media", ROOT / "_cache"
MAX = 1400

names = {}
for line in LIST.read_text().splitlines():
    u, _, n = line.partition("\t")
    m = re.search(r"/(\d{13}-[A-Z0-9]{20})/", u)
    if m:
        names[m.group(1)] = n


def source(aid, url):
    p = LIB / names.get(aid, "\0")
    if names.get(aid) and p.is_file():
        return p
    c = CACHE / aid
    if not c.exists():
        subprocess.run(["curl", "-s", "-H", "Accept:", "--retry", "3", "-o", str(c), url], check=False)
    return c if c.exists() and c.stat().st_size else None


def has_alpha(im):
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        a = im.convert("RGBA").getchannel("A")
        return a.getextrema()[0] < 250
    return False


def one(item):
    aid, url = item
    for e in ("jpg", "png", "gif"):
        if (OUT / f"{aid}.{e}").exists():
            return aid, f"{aid}.{e}"
    src = source(aid, url)
    if not src:
        return aid, None
    try:
        im = Image.open(src)
        if im.format == "GIF" and getattr(im, "n_frames", 1) > 1:
            shutil.copy(src, OUT / f"{aid}.gif")
            return aid, f"{aid}.gif"
        im.load()
        im.thumbnail((MAX, MAX))
        if has_alpha(im):
            im.save(OUT / f"{aid}.png", optimize=True)
            return aid, f"{aid}.png"
        im.convert("RGB").save(OUT / f"{aid}.jpg", quality=80, optimize=True, progressive=True)
        return aid, f"{aid}.jpg"
    except Exception as e:
        print("FAIL", aid, e, file=sys.stderr)
        return aid, None


def main():
    OUT.mkdir(exist_ok=True); CACHE.mkdir(exist_ok=True)
    wanted = json.loads((ROOT / "_data/media.json").read_text())
    with ThreadPoolExecutor(8) as ex:
        res = dict(ex.map(one, wanted.items()))
    files = {k: v for k, v in res.items() if v}
    (ROOT / "_data/media_files.json").write_text(json.dumps(files, indent=1))
    print(len(files), "of", len(wanted), "images ready;", [k for k, v in res.items() if not v])


if __name__ == "__main__":
    main()
