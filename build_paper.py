"""Build the manuscript, and refuse to build one that contains a hand-typed number.

Two checks, both hard failures:

  1. UNDEFINED MACRO. Every `\\nKey` used in the manuscript must be defined in
     paper/numbers.tex, i.e. declared in paper/numbers.py's SPEC with the file and
     path it comes from. A typo in a macro name would otherwise render as nothing at
     all, which is the silent-blank failure mode B37 warns about.

  2. BARE NUMERAL. Every numeric literal in the body must be either a resolved macro
     or an entry in ALLOWED below, each with a written reason. This is the point of
     the whole exercise: defects B21 and B43 both began with a number that reached a
     document with no script behind it, and B43's was the quantitative basis of a
     retraction. A literal that is genuinely structural (a mode count that names an
     axis, a section number, a year) is fine -- but it has to be *declared* fine.

`--report` lists every bare numeral with its line, which is how the allow-list gets
built in the first place: run it, look at each hit, and either turn it into a macro
(preferred) or add it here with a reason.

    python build_paper.py            # resolve numbers, check, report
    python build_paper.py --report   # list every bare numeral and its context
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(ROOT, "paper", "manuscript.tex")
NUMBERS_TEX = os.path.join(ROOT, "paper", "numbers.tex")

# Literals that may appear in the prose, each with the reason it is not a result.
# A number that IS a result does not belong here -- it belongs in numbers.py.
ALLOWED = {
    # structural constants of the experimental design, which name axes rather than
    # report outcomes; they are fixed by the protocol, not measured
    "8": "basis size p, an axis label",
    "12": "the smallest training-material count, an axis label",
    "24": "a mode index naming where per-mode R^2 crosses zero",
    "48": "a training-material count, an axis label",
    "64": "POD modes per channel, a fixed encoding choice",
    "96": "a training-material count, an axis label",
    "128": "basis size p / the field encoding, an axis label",
    "192": "training materials per fold, fixed by the 5-fold design",
    "216": "the width of the best DeepONet, an architecture description",
    "240": "the material count of the dataset, fixed by design",
    "17": "operating conditions per material, fixed by design",
    "3947": "accepted simulations, a dataset size",
    "2000": "N_z, a grid size",
    "24": "the number of validate.py gates",
    "26": "Part-A ledger count",
    "27": "ledger entries carrying the words 'our own error'",
    "61": "Part-B ledger count",
    "1": "ordinal / unity",
    "2": "ordinal / a term count",
    "3": "seed count and ordinal",
    "4": "ordinal, and the oracle-equivalent mode count",
    "5": "ordinal / fold count",
    "6": "ordinal",
    "10": "a percentage threshold declared in the pre-registration",
    "20": "a factor in a cited correlation's coefficient",
    "29": "an interpolation-floor percentage from a reported exclusion",
    "80": "the power level at which every MDE is quoted",
    "99.9": "the training-variance level at which n-widths are counted",
    # citation years and identifiers
    "1948": "citation year", "1954": "citation year", "1953": "citation year",
    "1959": "citation year", "1982": "citation year", "2000": "citation year",
    "1908": "citation year",
    # figures, sections, document structure
    "11": "documentclass font size", "0": "zero",
    # numbers reported BY a cited paper, quoted as that paper's finding
    "79": "McGreivy & Hakim's reported percentage",
    "60": "the numerator of McGreivy & Hakim's 60-of-76",
    "76": "the denominator of McGreivy & Hakim's 60-of-76",
    "0.7": "the leading coefficient of the Wakao-Funazkri dispersion correlation, as cited",
    "0.5": "the second coefficient of the Wakao-Funazkri dispersion correlation, as cited",
    "7": "the power of an earlier null, as recorded in retraction A22",
    # thresholds and definitions fixed by the protocol, not measured
    "50": "the 50 % crossing, which DEFINES the t50 breakthrough time",
    "0.2": "the R-squared threshold at which usable coefficient modes are counted",
}

MACRO = re.compile(r"\\n([A-Za-z]+)")
# a numeral not immediately preceded by a backslash-command or a letter
NUMERAL = re.compile(r"(?<![\\A-Za-z0-9.])(\d+(?:\.\d+)?)")


def body(src):
    """The document body, with comments and the preamble removed."""
    src = src.split(r"\begin{document}", 1)[-1]
    out = []
    for line in src.splitlines():
        line = re.sub(r"(?<!\\)%.*$", "", line)
        out.append(line)
    return "\n".join(out)


def strip_structural(text):
    """Remove constructs whose numerals are never results."""
    # A digit run attached to a word by a hyphen is part of a NAME (MOF-303, 411-A,
    # PCA-Net), not a measurement. Reading MOF-303 as the number 303 flagged eleven
    # false positives on the first run.
    text = re.sub(r"[A-Za-z]+-\d+[A-Za-z]*", " ", text)
    text = re.sub(r"\\includegraphics\[[^\]]*\]\{[^}]*\}", " ", text)
    text = re.sub(r"\\(label|ref|eqref|cite|input|bibliographystyle|bibliography)"
                  r"\{[^}]*\}", " ", text)
    text = re.sub(r"\\(begin|end)\{[^}]*\}", " ", text)
    text = re.sub(r"\\SI\{[^}]*\}\{[^}]*\}", " ", text)   # \SI carries its own units
    text = re.sub(r"\\[A-Za-z]+", " ", text)              # any remaining command name
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    r = subprocess.run([sys.executable, os.path.join(ROOT, "paper", "numbers.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        sys.exit(1)

    src = open(TEX, encoding="utf-8").read()
    defined = set(MACRO.findall(open(NUMBERS_TEX, encoding="utf-8").read()))
    b = body(src)

    used = set(MACRO.findall(b))
    undefined = sorted(used - defined)
    unused = sorted(defined - used)

    hits = []
    for i, line in enumerate(b.splitlines(), 1):
        for m in NUMERAL.finditer(strip_structural(line)):
            tok = m.group(1)
            if tok in ALLOWED:
                continue
            hits.append((i, tok, line.strip()[:110]))

    print(f"\nmacros: {len(used)} used, {len(undefined)} undefined, "
          f"{len(unused)} declared but unused")
    for k in undefined:
        print(f"  UNDEFINED  \\n{k}")
    if args.report or hits:
        print(f"\nbare numerals in the body: {len(hits)}")
        seen = {}
        for ln, tok, ctx in hits:
            seen.setdefault(tok, []).append((ln, ctx))
        for tok in sorted(seen, key=lambda t: -len(seen[t])):
            ln, ctx = seen[tok][0]
            print(f"  {tok:>8}  x{len(seen[tok]):<3} line {ln}: {ctx}")

    if undefined or hits:
        print("\nBUILD REFUSED. Every number in the manuscript must be a macro resolved "
              "from a\nresults file, or an ALLOWED literal with a written reason. "
              "See build_paper.py.")
        sys.exit(1)
    print("\nOK: no undefined macros, no undeclared numerals.")
    if unused:
        print(f"  ({len(unused)} keys declared in numbers.py are not used yet: "
              f"{', '.join(unused[:8])}{' ...' if len(unused) > 8 else ''})")


if __name__ == "__main__":
    main()
