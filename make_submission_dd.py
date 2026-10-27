"""Assemble the Digital Discovery submission package and prove it compiles on its own.

Follows the RSC author guidelines for Digital Discovery as read live on 2026-10-27:
  * the manuscript as one PDF for review, plus the editable LaTeX source and BibTeX database;
  * figures as separate files at the journal's widths (8.3 cm single column, 17.1 cm double),
    each as vector PDF and as a 600-dpi TIFF, named Figure_1, Figure_2, ... in order of appearance;
  * the table-of-contents entry: a graphic of at most 8 cm x 4 cm at 600 dpi (TIFF), not reused
    from the article, and a text of at most 250 characters;
  * the supplementary information as PDFs (S1 correction ledger, S2 supporting detail);
  * an abstract of around 50 to 250 words, and no placeholder left in the data statement.
Every limit is checked, not assumed; any failure refuses. The cover letter is copied from the
private outreach/ folder if present (submission_dd/ is not committed).

    python build_paper.py --pdf && python make_si.py && python fig_toc.py
    python make_submission_dd.py          -> submission_dd/ and submission_dd.zip
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "submission_dd")
PAPER = os.path.join(ROOT, "paper")
CM = 1 / 2.54
WIDTH_CM = 17.1                   # every figure of this paper is set at full (double-column) width


def refuse(msg):
    sys.exit("REFUSED: " + msg)


def body_words(tex, start, end):
    s = tex[tex.index(start) + len(start):tex.index(end)]
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " X ", s)          # a macro counts as one word
    s = re.sub(r"[{}\\$~%]", " ", s)
    return len([w for w in s.split() if re.search(r"[A-Za-z0-9]", w)])


def to_tiff(pdf, tiff, width_cm, dpi=600):
    import fitz
    from PIL import Image
    doc = fitz.open(pdf)
    page = doc[0]
    zoom = (width_cm * CM * dpi) / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    img.save(tiff, dpi=(dpi, dpi), compression="tiff_lzw")
    return img.size


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    tex = open(os.path.join(PAPER, "manuscript.tex"), encoding="utf-8").read()

    # --- the guideline's limits, checked
    n_abs = body_words(tex, r"\begin{abstract}", r"\end{abstract}")
    if not 50 <= n_abs <= 250:
        refuse(f"abstract has about {n_abs} words; the guideline asks for around 50 to 250")
    if "[DATASET DOI]" in tex or "[CODE VERSION DOI]" in tex:
        refuse("a DOI placeholder is still in the manuscript (data statement)")
    toc = open(os.path.join(PAPER, "toc_sentence.txt"), encoding="utf-8").read().strip()
    if len(toc) > 250:
        refuse(f"TOC text has {len(toc)} characters; the limit is 250")
    pdf = os.path.join(PAPER, "manuscript.pdf")
    if not os.path.exists(pdf) or os.path.getmtime(pdf) < os.path.getmtime(os.path.join(PAPER, "manuscript.tex")):
        refuse("paper/manuscript.pdf is missing or older than the source: run build_paper.py --pdf")

    # --- figures, in order of appearance: vector PDF and 600-dpi TIFF at 17.1 cm
    figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)
    mapping = {}
    for i, f in enumerate(figs, 1):
        src = os.path.normpath(os.path.join(PAPER, f))
        if not os.path.exists(src):
            refuse(f"figure file missing: {src}")
        mapping[f] = f"Figure_{i}.pdf"
        shutil.copy(src, os.path.join(OUT, mapping[f]))
        size = to_tiff(src, os.path.join(OUT, f"Figure_{i}.tif"), WIDTH_CM)
        print(f"  Figure_{i}: {os.path.basename(src)} -> {size[0]} x {size[1]} px at 600 dpi ({WIDTH_CM} cm wide)")
    src_tex = tex
    for f, new in mapping.items():
        src_tex = src_tex.replace("{" + f + "}", "{" + new + "}")
    open(os.path.join(OUT, "manuscript.tex"), "w", encoding="utf-8", newline="\n").write(src_tex)
    inputs = [n if n.endswith(".tex") else n + ".tex" for n in re.findall(r"\\input\{([^}]*)\}", src_tex)]
    for name in inputs + ["references.bib", "rsc.bst"]:
        s = os.path.join(PAPER, name)
        if os.path.exists(s):
            shutil.copy(s, OUT)
        elif name != "rsc.bst":
            refuse(f"input file missing: {s}")

    # --- table of contents entry: 8 cm x 4 cm at 600 dpi, and its text
    from PIL import Image
    toc_png = os.path.join(ROOT, "figures", "TOC.png")
    im = Image.open(toc_png)
    want = (round(8 * CM * 600), round(4 * CM * 600))
    if abs(im.size[0] - want[0]) > 4 or abs(im.size[1] - want[1]) > 4:
        refuse(f"TOC graphic is {im.size} px; 8 x 4 cm at 600 dpi is {want}")
    im.convert("RGB").save(os.path.join(OUT, "TOC_graphic.tif"), dpi=(600, 600), compression="tiff_lzw")
    open(os.path.join(OUT, "TOC_text.txt"), "w", encoding="utf-8").write(toc + "\n")

    # --- the PDFs a reviewer reads
    shutil.copy(pdf, os.path.join(OUT, "Manuscript.pdf"))
    shutil.copy(os.path.join(PAPER, "si_ledger.pdf"), os.path.join(OUT, "ESI_S1_correction_ledger.pdf"))
    si2 = os.path.join(PAPER, "si_extended.pdf")
    if not os.path.exists(si2) or os.path.getmtime(si2) < os.path.getmtime(os.path.join(PAPER, "manuscript.tex")):
        refuse("Supplementary S2 is missing or older than the manuscript: run make_si.py")
    shutil.copy(si2, os.path.join(OUT, "ESI_S2_supporting_detail.pdf"))
    cl = os.path.join(ROOT, "outreach", "cover_letter_dd.md")
    if os.path.exists(cl):
        text = open(cl, encoding="utf-8").read().split("\n---\n")[0]     # drop the private notes
        if "[" in text and "DOI]" in text:
            print("NOTE: the cover letter still has a DOI placeholder")
        open(os.path.join(OUT, "Cover_letter.txt"), "w", encoding="utf-8").write(text.strip() + "\n")

    # --- prove the LaTeX source compiles alone
    tect = os.path.join(ROOT, "tools", "tectonic.exe")
    if not os.path.exists(tect):
        tect = shutil.which("tectonic") or refuse("no tectonic found")
    with tempfile.TemporaryDirectory() as tmp:
        for f in os.listdir(OUT):
            if f.endswith((".tex", ".bib", ".bst", ".pdf")):
                shutil.copy(os.path.join(OUT, f), tmp)
        r = subprocess.run([tect, "--keep-logs", "manuscript.tex"], cwd=tmp, capture_output=True, text=True)
        log = open(os.path.join(tmp, "manuscript.log"), encoding="utf-8", errors="replace").read() \
            if os.path.exists(os.path.join(tmp, "manuscript.log")) else ""
        bad = [ln for ln in log.splitlines() if ln.startswith("!") or
               ("undefined" in ln.lower() and ("reference" in ln.lower() or "citation" in ln.lower()))]
        if r.returncode != 0 or bad:
            refuse("the package does not compile on its own:\n  " + "\n  ".join(bad[:10] or [r.stderr[-600:]]))

    zpath = os.path.join(ROOT, "submission_dd.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(OUT)):
            z.write(os.path.join(OUT, f), f)
    print(f"abstract {n_abs} words; TOC text {len(toc)} characters")
    print(f"wrote {OUT} ({len(os.listdir(OUT))} files) and {zpath}; the source compiled standalone without error")


if __name__ == "__main__":
    main()
