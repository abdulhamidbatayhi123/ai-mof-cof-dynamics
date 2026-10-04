"""Build the Supplementary Information ledger (paper/si_ledger.tex) from RETRACTIONS.md.

Referee minor 9: the manuscript cites ledger codes (A26, B43, B72, ...) that a reader
could not look up. The SI is GENERATED from the ledger file itself, every row in full,
so the two can never disagree; it is rebuilt by build_paper.py --pdf.

    python ledger_si.py            # writes paper/si_ledger.tex
"""
import re

SRC = "RETRACTIONS.md"
OUT = "paper/si_ledger.tex"

UNI = {"±": r"$\pm$", "∂": r"$\partial$", "²": r"$^2$", "³": r"$^3$", "≥": r"$\geq$", "≤": r"$\leq$",
       "×": r"$\times$", "→": r"$\rightarrow$", "←": r"$\leftarrow$", "≈": r"$\approx$", "∞": r"$\infty$",
       "α": r"$\alpha$", "β": r"$\beta$", "ε": r"$\varepsilon$", "λ": r"$\lambda$", "Λ": r"$\Lambda$",
       "τ": r"$\tau$", "σ": r"$\sigma$", "η": r"$\eta$", "μ": r"$\mu$", "ρ": r"$\rho$", "Δ": r"$\Delta$",
       "δ": r"$\delta$", "θ": r"$\theta$", "π": r"$\pi$", "√": r"$\surd$", "·": r"$\cdot$", "−": "-",
       "—": "---", "–": "--", "’": "'", "‘": "`", "“": "``", "”": "''", "…": r"\ldots{}", "⁻": r"$^{-}$",
       "¹": r"$^1$", "⁰": r"$^0$", "⁴": r"$^4$", "⁵": r"$^5$", "⁶": r"$^6$", "≠": r"$\neq$", "∝": r"$\propto$",
       "✓": "yes", "✗": "no", "✘": "no", "✔": "yes", "⚠": "(!)", "°": r"$^\circ$", "ö": r'\"o', "ä": r'\"a',
       "ü": r'\"u', "é": r"\'e", "ã": r"\~a", "Ü": r'\"U', "★": "*"}
UNI.update({"Θ": r"$\Theta$", "γ": r"$\gamma$", "κ": r"$\kappa$", "ξ": r"$\xi$", "ⁿ": r"$^n$",
            "ₛ": r"$_s$", "∈": r"$\in$", "️": ""})
UNI.update({chr(0x2080 + d): f"$_{d}$" for d in range(10)})
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(s):
    out = "".join(SPECIAL.get(ch, ch) for ch in s)
    return "".join(UNI.get(ch, ch) for ch in out)


def inline(md):
    """Markdown inline -> LaTeX: `code`, **bold**, *emph*; everything else escaped."""
    parts = re.split(r"(`[^`]*`)", md)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(r"\texttt{" + esc(p[1:-1]) + "}")
            continue
        p = esc(p)
        p = re.sub(r'"([^"]*)"', r"``\1''", p)          # straight quotes -> LaTeX pairs
        p = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", p)
        p = re.sub(r"(?<![\\*])\*(?!\s)(.+?)(?<!\s)\*", r"\\emph{\1}", p)
        out.append(p)
    return "".join(out)


def cells(line):
    s = line.strip().strip("|")
    # split on unescaped pipes (the ledger writes a literal pipe as \|)
    return [c.strip().replace(r"\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def main():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    entries, part, header = [], None, None
    for ln in lines:
        if ln.startswith("## PART A"):
            part = "A"; continue
        if ln.startswith("## PART B"):
            part = "B"; continue
        if ln.startswith("## ") and part:
            part = None; continue
        if part and ln.startswith("| #"):
            header = cells(ln)[1:]; continue
        m = re.match(r"^\| \*\*([AB]\d+)\*\* \|", ln)
        if part and m:
            c = cells(ln)
            entries.append((m.group(1), c[1:], header))
    labels_a = ["Claim withdrawn", "Replaced with", "Why it was wrong"]
    labels_b = ["Defect", "Resolution", "Note"]
    body = [r"\documentclass[10pt]{article}", r"\usepackage[margin=2cm]{geometry}",
            r"\usepackage[T1]{fontenc}", r"\usepackage{lmodern}", r"\usepackage{enumitem}",
            r"\usepackage[hidelinks]{hyperref}", r"\usepackage[htt]{hyphenat}",
            r"\setlength{\parindent}{0pt}", r"\sloppy", r"\setlength{\emergencystretch}{3em}",
            r"\begin{document}",
            r"\section*{Supplementary Information S1: the correction ledger}",
            esc(f"Generated from RETRACTIONS.md by ledger_si.py; {sum(e[0][0] == 'A' for e in entries)} "
                f"withdrawn claims (A) and {sum(e[0][0] == 'B' for e in entries)} caught defects (B), "
                f"every entry in full. The main text cites entries by these codes."),
            ""]
    for code, cs, hdr in entries:
        labs = labels_a if code[0] == "A" else (labels_b if len(cs) == 3 else ["Defect", "How it was caught"])
        body.append(r"\subsection*{" + code + "}" + r"\label{led:" + code + "}")
        body.append(r"\begin{description}[leftmargin=0pt,itemsep=1pt]")
        for lab, txt in zip(labs, cs):
            body.append(r"\item[" + lab + ".] " + inline(txt))
        body.append(r"\end{description}")
    body.append(r"\end{document}")
    open(OUT, "w", encoding="utf-8").write("\n".join(body) + "\n")
    print(f"wrote {OUT}: {len(entries)} entries")


if __name__ == "__main__":
    main()
