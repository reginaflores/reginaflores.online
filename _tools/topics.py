"""Fine-grained topic tags derived from post text, grouped for drill-down.

Each tag has word-boundary patterns. A post gets the tag when a pattern appears in its title,
or appears at least MIN_HITS times in its body. Tags covering fewer than MIN_POSTS posts are dropped.
"""
import re

MIN_HITS = 2
MIN_POSTS = 2

TAXONOMY = {
    "Code & tools": {
        "openFrameworks": [r"openframeworks", r"\bofx\w*"],
        "Processing & p5.js": [r"\bprocessing\.org\b", r"\bp5(\.js)?\b", r"\bprocessing sketch"],
        "JavaScript": [r"\bjavascript\b", r"\bnode(\.js)?\b", r"\bjquery\b"],
        "Three.js & WebGL": [r"\bthree\.?js\b", r"\bwebgl\b"],
        "Unity": [r"\bunity\b"],
        "Shaders": [r"\bshaders?\b", r"\bglsl\b"],
        "Arduino & electronics": [r"\barduino\b", r"\bsensors?\b", r"\bleds?\b", r"\bcircuits?\b", r"\bservos?\b"],
        "Kinect & computer vision": [r"\bkinect\b", r"\bcomputer vision\b", r"\bopencv\b"],
        "APIs & social data": [r"\bapis?\b", r"\binstagram\b", r"\btwitter\b", r"\bfacebook\b"],
        "Machine learning & algorithms": [r"\bmachine learning\b", r"\balgorithms?\b", r"\bneural\b", r"\bgenerative\b"],
    },
    "Making": {
        "3D printing & modeling": [r"\b3d print\w*", r"\brhino\b", r"\b3d model\w*", r"\bgrasshopper\b"],
        "Laser cutting & CNC": [r"\blaser[- ]cut\w*", r"\bcnc\b"],
        "Projection mapping": [r"\bprojection mapping\b", r"\bprojections?\b", r"\bprojector\b"],
        "Installation": [r"\binstallations?\b"],
        "Kinetic & physical": [r"\bkinetic\b", r"\bphysical computing\b", r"\bpcomp\b"],
        "Materials": [r"\bmaterials?\b", r"\btextures?\b"],
    },
    "Biology": {
        "Microbes & bacteria": [r"\bmicrob\w*", r"\bbacteri\w*", r"\bmicrobiome\b"],
        "Fungi & mycelium": [r"\bfung\w*", r"\bmycel\w*", r"\bmushroom\w*"],
        "Algae & spirulina": [r"\balgae\b", r"\bspirulina\b"],
        "Bees": [r"\bbees?\b", r"\bbeekeep\w*", r"\bhives?\b", r"\bhoney\b"],
        "Plants": [r"\bplants?\b", r"\bbotan\w*", r"\bseeds?\b"],
        "DNA & synthetic biology": [r"\bdna\b", r"\bsynthetic biology\b", r"\bgenom\w*", r"\bgenetic\w*"],
        "Bioplastic": [r"\bbio ?plastics?\b"],
    },
    "Science & cosmos": {
        "Cosmos & space": [r"\bcosm\w*", r"\buniverse\b", r"\bgalax\w*", r"\bdark matter\b", r"\bstars?\b", r"\bbig bang\b", r"\bastro\w*"],
        "Physics & particles": [r"\bphysics\b", r"\bparticles?\b", r"\bquantum\b", r"\bstring theory\b"],
        "Planet & Earth": [r"\bplanet\w*", r"\bearth\b", r"\bgaia\b"],
        "Scale": [r"\bscales?\b", r"\bpowers of ten\b", r"\bisomorph\w*"],
    },
    "Data": {
        "Data visualization": [r"\bdata ?vi[sz]\w*", r"\bvisuali[sz]\w*", r"\binfographic\w*"],
        "Maps & mapping": [r"\bmaps?\b", r"\bmapping\b", r"\bgis\b", r"\bcartograph\w*"],
        "Networks": [r"\bnetworks?\b", r"\bgraph theory\b", r"\bnodes?\b"],
        "Statistics & finance": [r"\bstatistic\w*", r"\bregression\b", r"\btime series\b", r"\bfinanc\w*", r"\bswaps?\b", r"\btrading\b", r"\bhedge fund\w*", r"\bportfolio\b", r"\bwall street\b"],
    },
    "City & environment": {
        "Cities & urbanism": [r"\bcit(y|ies)\b", r"\burban\w*", r"\bnew york\b", r"\bnyc\b"],
        "Architecture": [r"\barchitect\w*", r"\bbuildings?\b"],
        "Climate & environment": [r"\bclimate\b", r"\benvironment\w*", r"\bpollution\b", r"\bsustainab\w*"],
        "Ecology": [r"\becolog\w*", r"\becosystems?\b"],
        "Anthropocene": [r"\banthropocene\b"],
        "Energy & waste": [r"\benergy\b", r"\bwaste\b", r"\brecycl\w*"],
    },
    "Culture & ideas": {
        "Critical & speculative design": [r"\bcritical design\b", r"\bspeculative\b", r"\bdesign fiction\b", r"\bcritical\b"],
        "Futures": [r"\bfutures?\b"],
        "Theory & reading": [r"\btheory\b", r"\breadings?\b", r"\bessay\b", r"\bphilosoph\w*"],
        "Museums & The Met": [r"\bmuseums?\b", r"\bthe met\b", r"\bmetropolitan museum\b"],
        "Art & art history": [r"\bart history\b", r"\bartists?\b", r"\bartworks?\b", r"\bpaintings?\b"],
        "Performance & dance": [r"\bperformances?\b", r"\bdanc\w*", r"\bimprov\w*"],
        "Film & video": [r"\bfilms?\b", r"\bvideos?\b", r"\bdocumentar\w*"],
        "Sound & music": [r"\bsound\b", r"\bmusic\w*", r"\baudio\b", r"\bmidi\b"],
        "Virtual & augmented reality": [r"\bvirtual reality\b", r"\baugmented reality\b", r"\bvr\b"],
    },
    "Process": {
        "Prototypes": [r"\bprototyp\w*"],
        "User research & testing": [r"\buser test\w*", r"\binterviews?\b", r"\bsurveys?\b", r"\busers?\b", r"\bplaytest\w*"],
        "Presentations": [r"\bpresentations?\b", r"\bslides?\b", r"\bcritique\b"],
        "Research": [r"\bresearch\b", r"\bprecedents?\b", r"\bcase stud\w*"],
        "Teaching": [r"\bteach\w*", r"\bbootcamp\b", r"\bdorkshop\b", r"\bsyllabus\b", r"\bworkshops?\b", r"\bfaculty\b"],
    },
}


# original Squarespace tags folded into the taxonomy
LEGACY = {"openFrameworks": "openFrameworks", "projection": "Projection mapping", "javascript": "JavaScript",
          "Arduino": "Arduino & electronics", "PComp": "Kinetic & physical", "API": "APIs & social data",
          "instagram": "APIs & social data", "bioplastic": "Bioplastic", "performance": "Performance & dance",
          "essay": "Theory & reading", "installation": "Installation", "personalMap": "Maps & mapping"}


def derive(entries):
    """Return ({url: [tags]}, {group: [tags kept]})."""
    compiled = {g: {t: [re.compile(p, re.I) for p in pats] for t, pats in tags.items()} for g, tags in TAXONOMY.items()}
    hits = {}
    for e in entries:
        title, body = e["title"], e["text"]
        got = []
        for g, tags in compiled.items():
            for t, pats in tags.items():
                need = max(MIN_HITS, len(body) // 4000)  # long documents need more mentions
                if any(p.search(title) for p in pats) or sum(len(p.findall(body)) for p in pats) >= need:
                    got.append(t)
        for t in e.get("tags") or []:
            if LEGACY.get(t) and LEGACY[t] not in got:
                got.append(LEGACY[t])
        hits[e["url"]] = got
    counts = {}
    for got in hits.values():
        for t in got:
            counts[t] = counts.get(t, 0) + 1
    keep = {t for t, n in counts.items() if n >= MIN_POSTS}
    groups = {g: [t for t in tags if t in keep] for g, tags in TAXONOMY.items()}
    return {u: [t for t in got if t in keep] for u, got in hits.items()}, groups, counts
