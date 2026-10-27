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
        changed = write_si_labels(os.path.join(paper, "si_extended.aux"))
    print("wrote paper/si_extended.pdf (Supplementary S2), references resolved against the main text")
    if changed:
        sys.exit("REFUSED: S2's numbering changed, so paper/si_labels.tex was rewritten; "
                 "run build_paper.py --pdf and make_si.py again")


def write_si_labels(aux):
    """The main text cites S2 tables and sections by \\SIref{label}; their numbers are read from
    S2's own .aux into paper/si_labels.tex, so they cannot drift when S2 gains a table. A hand-
    typed 'Table S2' went stale exactly that way. Returns True if the file changed."""
    import re
    labels = {}
    for ln in open(aux, encoding="utf-8", errors="replace"):
        m = re.match(r"\\newlabel\{(s2:[^}]*)\}\{\{([^}]*)\}", ln)
        if m:
            labels[m.group(1)] = m.group(2)
    used = set(re.findall(r"\\SIref\{([^}]*)\}",
                          open(os.path.join(ROOT, "paper", "manuscript.tex"), encoding="utf-8").read()))
    missing = sorted(used - set(labels))
    if missing:
        sys.exit(f"REFUSED: the main text cites S2 labels that S2 does not define: {missing}")
    body = "".join(f"\\expandafter\\def\\csname SIn@{k}\\endcsname{{{labels[k]}}}\n" for k in sorted(used))
    text = ("% written by make_si.py from si_extended.aux; do not edit\n"
            "\\makeatletter\n" + body + "\\makeatother\n")
    path = os.path.join(ROOT, "paper", "si_labels.tex")
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != text:
        open(path, "w", encoding="utf-8").write(text)
        return True
    return False


if __name__ == "__main__":
    main()
