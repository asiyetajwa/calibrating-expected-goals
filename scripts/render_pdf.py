#!/usr/bin/env python3
"""Render manuscript.md to a clean academic PDF with fpdf2."""
from fpdf import FPDF

BASE = "/home/hatch/workspace/o1-authorship/betting-paper"

class Paper(FPDF):
    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Times", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"{self.page_no()}", align="C")

def parse(path):
    """Yield (kind, text) blocks."""
    blocks = []
    lines = open(path).read().split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("# "):
            blocks.append(("title", ln[2:].strip())); i += 1
        elif ln.startswith("## "):
            blocks.append(("h2", ln[3:].strip())); i += 1
        elif ln.startswith("### "):
            blocks.append(("h3", ln[4:].strip())); i += 1
        elif ln.startswith("**") and ln.endswith("**") and len(ln) < 120:
            blocks.append(("author", ln.strip("*"))); i += 1
        elif ln.startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                tbl.append(cells); i += 1
            # drop separator row
            tbl = [r for r in tbl if not all(set(c) <= set("-: ") for c in r)]
            blocks.append(("table", tbl))
        elif ln.strip() == "":
            i += 1
        else:
            para = []
            while i < len(lines) and lines[i].strip() != "" and not lines[i].startswith(("#", "|")):
                para.append(lines[i].strip()); i += 1
            text = " ".join(para)
            if text.startswith("Keywords:"):
                blocks.append(("keywords", text))
            else:
                blocks.append(("p", text))
    return blocks

pdf = Paper(format="A4")
pdf.set_auto_page_break(True, margin=25)
pdf.set_margins(28, 25, 28)
pdf.add_page()

for kind, text in parse(f"{BASE}/manuscript.md"):
    if kind == "title":
        pdf.set_font("Times", "B", 20)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 9, text, align="C")
        pdf.ln(6)
    elif kind == "author":
        pdf.set_font("Times", "", 12)
        pdf.cell(0, 6.5, text, align="C", new_x="LMARGIN", new_y="NEXT")
    elif kind == "p" and ("Working paper" in text or "@" in text or text.startswith("October")):
        pdf.set_font("Times", "I", 11)
        pdf.cell(0, 6.5, text, align="C", new_x="LMARGIN", new_y="NEXT")
        if "Working paper" in text:
            pdf.ln(8)
    elif kind == "h2":
        pdf.ln(4)
        pdf.set_font("Times", "B", 14)
        pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    elif kind == "h3":
        pdf.ln(2)
        pdf.set_font("Times", "B", 12)
        pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    elif kind == "keywords":
        pdf.set_font("Times", "I", 10)
        pdf.multi_cell(0, 5.5, text, align="J")
        pdf.ln(2)
    elif kind == "p":
        pdf.set_font("Times", "", 11)
        pdf.multi_cell(0, 6, text, align="J")
        pdf.ln(1.5)
    elif kind == "table":
        # keep small tables on one page: roughly 2 header + rows
        est_h = 6 * (len(text) + 1) + 10
        if pdf.get_y() + est_h > pdf.h - 30:
            pdf.add_page()
        pdf.ln(2)
        ncol = len(text[0])
        avail = pdf.w - 56
        # first column gets extra width for model names
        ratios = [1.9] + [1.0] * (ncol - 1)
        widths = [avail * r / sum(ratios) for r in ratios]
        pdf.set_font("Times", "B", 8.5)
        for c, w in zip(text[0], widths):
            pdf.cell(w, 6, c, border=1, align="C")
        pdf.ln()
        pdf.set_font("Times", "", 8.5)
        for row in text[1:]:
            for c, w in zip(row, widths):
                pdf.cell(w, 6, c, border=1, align="C")
            pdf.ln()
        pdf.ln(4)

# Figures at the end, each on its own page region
for fig, cap in [
    ("results/figure1_calibration.png",
     "Figure 1: Reliability diagram. Mean predicted probability vs observed outcome frequency, pooled over all match-outcome pairs. The Dixon-Coles model (ECE 0.014) tracks the diagonal closely; the xG Poisson (ECE 0.035) is slightly overconfident at high probabilities."),
    ("results/figure2_backtest.png",
     "Figure 2: Cumulative profit/loss of the flat-stake backtest at a 3 percent edge threshold, settled at Pinnacle closing odds. Both equity curves decline steadily, consistent with strong-form efficiency of the closing line."),
]:
    pdf.add_page()
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, cap.split(":")[0], new_x="LMARGIN", new_y="NEXT")
    pdf.image(f"{BASE}/{fig}", x=28, w=pdf.w - 56)
    pdf.ln(3)
    pdf.set_font("Times", "", 10)
    pdf.multi_cell(0, 5.5, cap, align="J")

out = f"{BASE}/results/Calibrating_Expected_Goals_Simiyu_2026.pdf"
pdf.output(out)
print("wrote", out)
