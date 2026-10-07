"""Courses taught, built from the course repos on GitHub (READMEs saved in _data/courses/).

Room numbers, e-mail addresses and TA contact details are stripped before publishing.
Writes _data/courses.json.
"""
import json, re
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_data/courses"

# repo -> (slug, title, term, year, program, codes, links)
COURSES = [
    ("MFADT_bootcamp_2015", "bootcamp-code-2015", "MFA D+T Bootcamp: Code Section", "Summer 2015", "2015",
     "MFA Design & Technology, Parsons", "Code section leader",
     [("Teacher repo", "https://github.com/reginaflores/MFADT_bootcamp_2015"),
      ("In-class code", "https://github.com/reginaflores/MFADT_Bootcamp_InClass"),
      ("Student homework", "https://github.com/reginaflores/MFADT_Bootcamp_Student_Homework")]),
    ("oF_Dorkshop", "openframeworks-dorkshop-2015", "openFrameworks Dorkshop", "Summer 2015", "2015",
     "MFA Design & Technology, Parsons", "Bootcamp workshop",
     [("Repo", "https://github.com/reginaflores/oF_Dorkshop")]),
    ("p5js_Dorkshop", "p5js-dorkshop-2015", "p5.js Dorkshop", "Summer 2015", "2015",
     "MFA Design & Technology, Parsons", "Bootcamp workshop",
     [("Repo", "https://github.com/reginaflores/p5js_Dorkshop")]),
    ("AlgoSims2016", "algorithms-and-simulations-2016", "Creative Coding with openFrameworks: Algorithms and Simulations",
     "Fall 2016", "2016", "MFA Design & Technology, Parsons", "PGTE 5566",
     [("Course repo", "https://github.com/reginaflores/AlgoSims2016"),
      ("Student repo", "https://github.com/reginaflores/AlgoSims2016__students")]),
    ("Critical_Computation_Lab_2022", "critical-computation-lab-2022", "Critical Computation Lab", "Fall 2022", "2022",
     "MFA + BFA Design & Technology, Parsons", "PGTE 5251 · PUDT 2109",
     [("Course repo", "https://github.com/reginaflores/Critical_Computation_Lab_2022"),
      ("Course website", "https://parsonsdt.github.io/critical-computation-2022/index.html")]),
    ("Advanced_Critical_Computation_2023", "advanced-critical-computation-2023", "Advanced Critical Computation Lab",
     "Spring 2023", "2023", "BFA Design & Technology, Parsons", "PUDT 2112",
     [("Course repo", "https://github.com/reginaflores/Advanced_Critical_Computation_2023"),
      ("Course website", "https://advanced-critical-computation-23.glitch.me/")]),
    ("Critical_Computation_Lab_2023", "critical-computation-lab-2023", "Critical Computation Lab", "Fall 2023", "2023",
     "MFA + BFA Design & Technology, Parsons", "PGTE 1946 · PUDT 2759",
     [("Course repo", "https://github.com/reginaflores/Critical_Computation_Lab_2023"),
      ("Course website", "https://parsonsdt.github.io/critical-computation-2023/index.html")]),
    ("Advanced_Critical_Computation_2024", "advanced-critical-computation-2024", "Advanced Critical Computation Lab",
     "Spring 2024", "2024", "BFA Design & Technology, Parsons", "PUDT 2112",
     [("Course repo", "https://github.com/reginaflores/Advanced_Critical_Computation_2024"),
      ("Course website", "https://advanced-critical-computation-2024.glitch.me/"),
      ("Student work", "https://reginaflores.github.io/Advanced_Critical_Computation_2024/class_list.html")]),
    ("Data_As_Material_2026", "data-as-material-2026", "Data as Material", "Fall 2026", "2026",
     "Parsons School of Design", "Current course",
     [("Course repo", "https://github.com/reginaflores/Data_As_Material_2026")]),
]

PRIVATE_LINE = re.compile(r"(@newschool\.edu|@gmail|Location:|Room \d|TA:|\bRm \d)", re.I)


def clean(md):
    lines = [l for l in md.splitlines() if not PRIVATE_LINE.search(l)]
    md = "\n".join(lines)
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"^#\s.*$", "", md, count=1, flags=re.M)          # title (shown as page h1)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)                   # repo-relative images
    md = re.sub(r"\*\*Course Instructor:?\*\*.*", "", md)
    md = re.sub(r"\*\s*\*\*Faculty( e-mail)?:\*\*.*", "", md)
    return md.strip()


def main():
    out = []
    for repo, slug, title, term, year, program, codes, links in COURSES:
        p = SRC / f"{repo}.README.md"
        md = p.read_text(errors="ignore") if p.exists() else ""
        tree = SRC / f"{repo}.tree.txt"
        dirs = [d for d in tree.read_text().split() if "/" not in d] if tree.exists() else []
        if md.strip():
            body = markdown.markdown(clean(md), extensions=["tables", "sane_lists"])
        elif dirs:
            items = "".join(f"<li>{re.sub(r'^[0-9.]+_', '', d).replace('_', ' ')}</li>" for d in sorted(dirs))
            body = f"<h2>Outline</h2><ol>{items}</ol>"
        else:
            body = "<p>This course is running now; materials will be added as the semester unfolds.</p>"
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
        desc = re.search(r"## Course Description\s+(.+?)\n\n", md, re.S) or re.search(r"## Description\s+(.+?)\n\n", md, re.S)
        out.append({"kind": "course", "url": f"/teaching/{slug}", "title": title, "term": term, "year": year,
                    "program": program, "codes": codes, "links": links, "html": body,
                    "description": re.sub(r"\s+", " ", desc.group(1)).strip()[:300] if desc else "",
                    "text": f"{title} {term} {program} {codes} teaching course " + text})
    (ROOT / "_data/courses.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(len(out), "courses")


if __name__ == "__main__":
    main()
