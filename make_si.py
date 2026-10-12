"""Compile Supplementary Material S2 (paper/si_extended.tex) against the main text.

The main manuscript is compiled first in a scratch copy of paper/ with its auxiliary
file kept, so that S2's references to main-text sections, figures, tables and
equations resolve to the numbers the reader sees. Any LaTeX error, undefined
reference or undefined citation refuses.

    python build_paper.py     (first: numbers.tex, references.bib, manuscript)
    python make_si.py         -> paper/si_extended.pdf
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TECT = os.path.join(ROOT, "tools", "tectonic.exe")


def compile_in(d, name):
    r = subprocess.run([TECT, "--keep-logs", "--keep-intermediates", name + ".tex"],
                       cwd=d, capture_output=True, text=True)
    log = open(os.path.join(d, name + ".log"), encoding="utf-8", errors="replace").read() \
        if os.path.exists(os.path.join(d, name + ".log")) else ""
    bad = [ln for ln in log.splitlines() if ln.startswith("!") or
           ("undefined" in ln.lower() and ("reference" in ln.lower() or "citation" in ln.lower()))]
    if r.returncode != 0 or bad:
        sys.exit(f"REFUSED: {name} does not compile cleanly:\n  " + "\n  ".join(bad[:10] or [r.stderr[-600:]]))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        paper = os.path.join(tmp, "paper")
        shutil.copytree(os.path.join(ROOT, "paper"), paper,
                        ignore=shutil.ignore_patterns("*.pdf", "*.log", "*.aux"))
        shutil.copytree(os.path.join(ROOT, "figures"), os.path.join(tmp, "figures"))
        compile_in(paper, "manuscript")
        compile_in(paper, "si_extended")
        shutil.copy(os.path.join(paper, "si_extended.pdf"), os.path.join(ROOT, "paper", "si_extended.pdf"))
    print("wrote paper/si_extended.pdf (Supplementary S2), references resolved against the main text")


if __name__ == "__main__":
    main()
