"""Papers & presentations: copy PDFs into papers/, render covers, extract text for tags/search.

Source PDFs are the Squarespace /s/ uploads backed up to Google Drive. Resumes and third-party
writing are deliberately excluded.
Writes _data/papers.json.
"""
import json, re, shutil, subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = Path.home() / "Library/CloudStorage/GoogleDrive-regina.flores@gmail.com/My Drive/Squarespace backup – reginafloresmir.com/PDFs and files"
OUT = ROOT / "papers"

# file -> (slug, title, kind, year, context, collaborators)
DOCS = {
    "final_draft_final.pdf": ("us-swaps-time-series", "Time Series Analysis of the US Swaps Markets", "Paper", "2008", "M.A. Statistics, Columbia University · Advanced Data Analysis", ""),
    "LAB-III-RADIO-RECEIVERS.pdf": ("lab-radio-receivers", "Lab III: Radio Receivers", "Lab report", "", "B.A. Physics, Barnard College", ""),
    "Final_Paper_D21C_Regina_Flores.pdf": ("ecological-synergies", "Ecological Synergies: A Model for a Better World", "Paper", "2015", "Parsons MFA · Design for This Century", ""),
    "Project1_ofxStats.pdf": ("ofxstats", "ofxStats: Experiments in Image Statistics", "Presentation", "2015", "Parsons MFA · Major Studio 2, Project 1", ""),
    "Project_2_Proposal.pdf": ("femme-form", "Femme Form", "Presentation", "2015", "Parsons MFA · Major Studio 2, Project 2 proposal", ""),
    "Presentation_1_V2-zbjj.pdf": ("met-media-lab-intern-presentation", "Met Media Lab Intern Presentation", "Presentation", "2015", "The Met Media Lab", ""),
    "Presentation.pdf": ("high-line-interaction-scenarios", "The High Line: Interaction Scenarios", "Presentation", "2015", "Parsons MFA · Interactive Spaces", ""),
    "KineticWall-V2.pdf": ("high-line-kinetic-wall", "The High Line Kinetic Wall", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Jenna Demchuk, Jaskirat Randhawa"),
    "Project_2_small.pdf": ("jpg-experiments", "The JPG Experiments", "Presentation", "2015", "Parsons MFA · Major Studio 2, Project 2", ""),
    "KineticBirds.pdf": ("kinetic-birds", "Natural History Museum: Kinetic Birds", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Jenna Demchuk, Jaskirat Randhawa"),
    "Final_Project_Proposal_Presentation.pdf": ("meta-methods-proposal", "<META> Methods: Final Project Proposal", "Presentation", "2015", "Parsons MFA · Major Studio 2", ""),
    "Project_1_Fashion_Show.pdf": ("faceless-fashion", "Interactive Events: #MMFacelessFashion", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Tyler Henry, Jaskirat Randhawa"),
    "Flores_Assignment_5.pdf": ("washington-square-interactive-song", "Washington Square Park Interactive Song", "Presentation", "2015", "Parsons MFA · Interactive Spaces", ""),
    "Assignement_6_Interactive_Spaces_Final_2.pdf": ("holi-interaction-through-ritual", "Interaction Design Through Ritual: Holi", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Tyler Henry, Jaskirat Randhawa"),
    "Assignement_7_Interactive_Spaces_Final_ONLINEVERSION.pdf": ("holi-water-colorscape", "Holi: An Interactive Water Color-scape", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Tyler Henry, Jaskirat Randhawa"),
    "Final_Paper_Mat_Tech_Flores_Regina.pdf": ("plastic-alternatives-mycelium", "Plastic Alternatives: Exploring Mycelium as a Medium", "Paper", "2015", "Parsons MFA · Materials Technology", ""),
    "Flores_Regina_MS_II_Final_Paper.pdf": ("meta-methods-paper", "<META>METHODS: Algorithmic Art Using the Metropolitan Museum of Art's Digital Archive", "Paper", "2015", "Parsons MFA · Major Studio 2", ""),
    "Tesla_Presentation1compressed.pdf": ("tesla-retail-research", "Tesla — Future of Retail: Client Research", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Jaskirat Randhawa, Tyler Henry"),
    "Tesla_Phase2compressed.pdf": ("tesla-retail-concept", "Tesla — Future of Retail: Concept", "Presentation", "2015", "Parsons MFA · Interactive Spaces", "Jaskirat Randhawa, Tyler Henry"),
    "terreform_one_final_presentation.pdf": ("smart-spirulina-system-presentation", "Smart Spirulina System", "Presentation", "2015", "Terreform ONE", "Jimmy Tang"),
    "Grid_of_Nine_Final_small.pdf": ("grid-of-nine", "Grid of Nine: Thesis Domains", "Presentation", "2015", "Parsons MFA · Thesis 1", ""),
    "CHICANO_FinalSmallcompressed.pdf": ("chicano-street-art", "Chicano Street Art", "Presentation", "2015", "Parsons MFA · Physical Graffiti", "Henry Lam"),
    "Thesis_Midterm_Presentationcompressed.pdf": ("anthropocene-thesis-concept", "In the Age of the Anthropocene: Thesis Concept", "Presentation", "2015", "Parsons MFA · Thesis 1", ""),
    "PostPlanetaryResearchNotes.pdf": ("post-planetary-research-notes", "Post-Planetary Design: Research Notes", "Notes", "2016", "Parsons MFA · Post-Planetary Design", ""),
    "PetchaKutcha_Final_vcompressed.pdf": ("in-pursuit-of-the-human-pecha-kucha", "In Pursuit of the Human (Pecha Kucha)", "Presentation", "2016", "Parsons MFA · Post-Planetary Design", ""),
    "Regina_Flores_Post_Planetary_Design_Final_Paper.pdf": ("in-pursuit-of-the-human", "In Pursuit of the Human", "Paper", "2016", "Parsons MFA · Post-Planetary Design", ""),
}


def main():
    OUT.mkdir(exist_ok=True)
    (ROOT / "media/covers").mkdir(parents=True, exist_ok=True)
    docs = []
    for fn, (slug, title, kind, year, context, collab) in DOCS.items():
        src = SRC / fn
        dest = OUT / f"{slug}.pdf"
        if not dest.exists():
            shutil.copy(src, dest)
        cover = ROOT / f"media/covers/{slug}.jpg"
        if not cover.exists():
            tmp = ROOT / f"_cache/cover-{slug}"
            subprocess.run(["pdftoppm", "-r", "60", "-f", "1", "-l", "1", "-png", "-singlefile", str(src), str(tmp)], check=True)
            im = Image.open(f"{tmp}.png").convert("RGB"); im.thumbnail((900, 900))
            im.save(cover, quality=80, optimize=True)
        text = subprocess.run(["pdftotext", "-q", str(src), "-"], capture_output=True, text=True).stdout
        text = re.sub(r"\s+", " ", text).strip()
        pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(src)], capture_output=True, text=True).stdout).group(1))
        docs.append({"kind": "doc", "url": f"/papers/{slug}", "pdf": f"/papers/{slug}.pdf", "title": title,
                     "doc_type": kind, "year": year, "context": context, "collaborators": collab,
                     "pages": pages, "mb": round(src.stat().st_size / 1048576, 1),
                     "cover": f"/media/covers/{slug}.jpg", "text": text[:20000]})
    (ROOT / "_data/papers.json").write_text(json.dumps(docs, indent=1))
    print(len(docs), "documents")


if __name__ == "__main__":
    main()
