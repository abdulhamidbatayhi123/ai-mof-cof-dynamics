"""Build the ChemRxiv version of the manuscript from the CMAME submission package.

ChemRxiv's FAQ (read live 2026-10-12) asks authors not to post a template that names a
third-party publisher or journal, and lists "providing a clean template" among the
reasons a submission is returned. The CMAME source prints "Preprint submitted to
Computer Methods in Applied Mechanics and Engineering" on the title page; this script
compiles the identical manuscript with that footer removed and nothing else changed.

    python make_submission.py   (first; it assembles and test-compiles the package)
    python make_chemrxiv.py     -> chemrxiv/manuscript_chemrxiv.pdf and the supplement
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(ROOT, "submission")
OUT = os.path.join(ROOT, "chemrxiv")

FOOTER = ("  \\def\\@oddfoot{\\footnotesize\\itshape Preprint submitted to \\@journal\\hfill}%\n")
CLEAN = ("  \\def\\@oddfoot{\\hfill}%\n")


def main():
    if not os.path.exists(os.path.join(SUB, "manuscript.tex")):
        sys.exit("run make_submission.py first")
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for f in os.listdir(SUB):
            shutil.copy(os.path.join(SUB, f), tmp)
        p = os.path.join(tmp, "manuscript.tex")
        tex = open(p, encoding="utf-8").read()
        if tex.count(FOOTER) != 1:
            sys.exit("REFUSED: the journal footer line was not found exactly once")
        tex = tex.replace(FOOTER, CLEAN)
        if "Preprint submitted to" in tex:
            sys.exit("REFUSED: a journal footer is still present")
        open(p, "w", encoding="utf-8", newline="\n").write(tex)
        r = subprocess.run([os.path.join(ROOT, "tools", "tectonic.exe"), "--keep-logs", "manuscript.tex"],
                           cwd=tmp, capture_output=True, text=True)
        log = open(os.path.join(tmp, "manuscript.log"), encoding="utf-8", errors="replace").read()
        bad = [ln for ln in log.splitlines() if ln.startswith("!") or
               ("undefined" in ln.lower() and ("reference" in ln.lower() or "citation" in ln.lower()))]
        if r.returncode != 0 or bad:
            sys.exit("REFUSED: compile failed:\n  " + "\n  ".join(bad[:10] or [r.stderr[-600:]]))
        shutil.copy(os.path.join(tmp, "manuscript.pdf"), os.path.join(OUT, "manuscript_chemrxiv.pdf"))
    shutil.copy(os.path.join(SUB, "Supplementary_S1_correction_ledger.pdf"), OUT)
    print(f"wrote {OUT}: manuscript_chemrxiv.pdf (no journal footer) and the supplement")


if __name__ == "__main__":
    main()
