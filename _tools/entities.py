"""People and institutions mentioned across the archive, with aliases.

Each name gets a page listing every post, project and paper that mentions it.
Matching is whole-word and case-sensitive on the aliases below.
"""
import re

PEOPLE = {
    # collaborators
    "Jimmy Tang": ["Jimmy Tang"],
    "Mitchell Joachim": ["Mitchell Joachim", "Mitch Joachim"],
    "Ben Berman": ["Ben Berman"],
    "Chris Woebken": ["Chris Woebken"],
    "Christopher Mason": ["Christopher Mason", "Chris Mason"],
    "Hang Do Thi Duc": ["Hang Do Thi Duc"],
    "Tyler Henry": ["Tyler Henry"],
    "Jaskirat Randhawa": ["Jaskirat Randhawa", "Jaskirat Singh Randhawa", "Jas Randhawa"],
    "Jenna Demchuk": ["Jenna Demchuk"],
    "Henry Lam": ["Henry Lam"],
    "Ed Keller": ["Ed Keller"],
    "Oliver Medvedik": ["Oliver Medvedik"],
    "Clive Dilnot": ["Clive Dilnot"],
    # design, architecture, biodesign
    "Buckminster Fuller": ["Buckminster Fuller", "Bucky Fuller"],
    "Charles and Ray Eames": ["Charles and Ray Eames", "Ray Eames", "Charles Eames", "Eames"],
    "Paolo Soleri": ["Paolo Soleri", "Soleri"],
    "Neri Oxman": ["Neri Oxman"],
    "François Roche": ["Francois Roche", "François Roche"],
    "Alisa Andrasek": ["Alisa Andrasek"],
    "David Benjamin": ["David Benjamin"],
    "William Myers": ["William Myers"],
    "Anthony Dunne & Fiona Raby": ["Anthony Dunne", "Fiona Raby", "Dunne and Raby", "Dunne & Raby"],
    "Suzanne Lee": ["Suzanne Lee"],
    "Achim Menges": ["Achim Menges"],
    "Marcos Cruz": ["Marcos Cruz"],
    "Oron Catts": ["Oron Catts"],
    # art & media art
    "Sol LeWitt": ["Sol LeWitt", "Sol Lewitt"],
    "Yayoi Kusama": ["Yayoi Kusama", "Kusama"],
    "Casey Reas": ["Casey Reas"],
    "Golan Levin": ["Golan Levin"],
    "Christopher Baker": ["Christopher Baker"],
    "Lev Manovich": ["Lev Manovich", "Manovich"],
    "Martin Krzywinski": ["Martin Krzywinski"],
    "Karsten Schmidt": ["Karsten Schmidt"],
    "Fernanda Viégas": ["Fernanda Viégas", "Fernanda Viegas"],
    "Rachel Garrard": ["Rachel Garrard"],
    "Guerrilla Girls": ["Guerrilla Girls"],
    "Chaz Bojórquez": ["Chaz Bojorquez", "Chaz Bojórquez"],
    "Edward Tufte": ["Edward Tufte", "Tufte"],
    "Ernst Haeckel": ["Ernst Haeckel", "Haeckel"],
    # science, theory, futures
    "Richard Feynman": ["Richard Feynman", "Feynman"],
    "Carl Sagan": ["Carl Sagan"],
    "Michio Kaku": ["Michio Kaku"],
    "Benjamin Bratton": ["Benjamin Bratton"],
    "Kevin Slavin": ["Kevin Slavin"],
    "Jaron Lanier": ["Jaron Lanier"],
    "Jeremy Rifkin": ["Jeremy Rifkin"],
    "Kim Stanley Robinson": ["Kim Stanley Robinson"],
    "Bret Victor": ["Bret Victor"],
    "Michel Foucault": ["Michel Foucault", "Foucault"],
    "Marshall McLuhan": ["Marshall McLuhan", "McLuhan"],
    "Spike Jonze": ["Spike Jonze"],
    "Stanley Kubrick": ["Stanley Kubrick", "Kubrick"],
    "Elon Musk": ["Elon Musk"],
    "Martin Margiela": ["Martin Margiela", "Maison Margiela", "Maison Martin Margiela"],
}

INSTITUTIONS = {
    "The Met": ["The Met", "the Met", "Metropolitan Museum", "Met Media Lab", "Met Museum"],
    "MIT Media Lab": ["MIT Media Lab", "Media Lab", "Mediated Matter"],
    "Terreform ONE": ["Terreform One", "Terreform ONE", "Terreform"],
    "Parsons": ["Parsons"],
    "The New School": ["New School", "Newschool"],
    "Columbia University": ["Columbia University", "Columbia"],
    "Barnard College": ["Barnard"],
    "NASA": ["NASA", "Ames Research Center", "SOFIA"],
    "NRAO": ["NRAO", "National Radio Astronomy"],
    "Arecibo / NAIC": ["Arecibo", "National Astronomy and Ionosphere Center", "Ionosphere Center"],
    "Goldman Sachs": ["Goldman Sachs", "Goldman"],
    "JP Morgan": ["JP Morgan", "J.P. Morgan", "JPMorgan"],
    "Cue Group": ["Cue Group"],
    "Cooper Hewitt": ["Cooper Hewitt", "Cooper-Hewitt"],
    "Biofabricate": ["Biofabricate", "BIOFABRICATE"],
    "Ecovative": ["Ecovative"],
    "Genspace": ["Genspace", "GenSpace"],
    "Weill Cornell Medicine": ["Weill Cornell", "Cornell"],
    "Mori Building": ["Mori Building", "MORI"],
    "Venice Biennale": ["Venice Biennale", "Biennale"],
    "SXSW": ["SXSW"],
    "ACADIA": ["ACADIA", "Acadia"],
    "The High Line": ["High Line"],
    "Washington Square Park": ["Washington Square"],
    "American Museum of Natural History": ["Natural History Museum", "Museum of Natural History", "AMNH"],
    "Museum of Mathematics": ["MoMath", "Museum of Mathematics"],
    "Tesla": ["Tesla"],
    "Burning Man": ["Burning Man", "Playa"],
    "Eyebeam": ["Eyebeam"],
    "NEW INC": ["NEW INC", "New Inc"],
}


def _compile(table):
    return {name: re.compile(r"(?<![\w-])(" + "|".join(re.escape(a) for a in aliases) + r")(?![\w-])") for name, aliases in table.items()}


def find(entries, table, min_posts=1):
    pats = _compile(table)
    hits = {e["url"]: [] for e in entries}
    for e in entries:
        hay = e["title"] + " \n " + e["text"]
        for name, p in pats.items():
            if p.search(hay):
                hits[e["url"]].append(name)
    counts = {}
    for names in hits.values():
        for n in names:
            counts[n] = counts.get(n, 0) + 1
    keep = {n for n, c in counts.items() if c >= min_posts}
    return {u: [n for n in ns if n in keep] for u, ns in hits.items()}, {n: counts[n] for n in keep}
