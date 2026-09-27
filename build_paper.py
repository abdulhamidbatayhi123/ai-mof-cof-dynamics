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
#
# The REASONS are the audit trail, so the list is built as pairs and checked for
# duplicate keys rather than written as a dict literal: a repeated key in a dict
# literal silently keeps the last value and throws the other justification away,
# which happened twice here ("24" as a mode index and as the gate count; "2000" as a
# grid size and as a citation year). A justification that vanishes without a word is
# the same failure as a number without a script.
_ALLOWED_PAIRS = [
    # structural constants of the experimental design, which name axes rather than
    # report outcomes; they are fixed by the protocol, not measured
    ("8", "basis size p, an axis label"),
    ("12", "the smallest training-material count, an axis label"),
    ("24", "a mode index naming where per-mode R^2 crosses zero"),
    ("48", "a training-material count, an axis label"),
    ("64", "POD modes per channel, a fixed encoding choice"),
    ("96", "a training-material count, an axis label"),
    ("128", "basis size p / the field encoding, an axis label"),
    ("192", "training materials per fold, fixed by the 5-fold design"),
    ("216", "the width of the best DeepONet, an architecture description"),
    ("256", "the hidden-layer width of the reported arm, a fixed architecture choice"),
    ("240", "the material count of the dataset, fixed by design"),
    ("17", "operating conditions per material, fixed by design"),
    ("3947", "accepted simulations, a dataset size"),
    ("2000", "N_z, a grid size"),
    # the validate.py gate count used to be allow-listed here as "24"; it is a RESULT
    # and is now the macro \nGates, read from results/validation.json
    ("1", "ordinal / unity"),
    ("2", "ordinal / a term count"),
    ("3", "seed count and ordinal"),
    ("4", "ordinal, and the oracle-equivalent mode count"),
    ("5", "ordinal / fold count"),
    ("6", "ordinal"),
    ("10", "a percentage threshold declared in the pre-registration"),
    ("20", "a factor in a cited correlation's coefficient"),
    ("29", "an interpolation-floor percentage from a reported exclusion"),
    ("80", "the power level at which every MDE is quoted"),
    ("99.9", "the training-variance level at which n-widths are counted"),
    # citation years and identifiers
    ("1948", "citation year"),
    ("1954", "citation year"),
    ("1953", "citation year"),
    ("1959", "citation year"),
    ("1982", "citation year"),
    ("1908", "citation year"),
    # figures, sections, document structure
    ("11", "documentclass font size"),
    ("0", "zero"),
    # numbers reported BY a cited paper, quoted as that paper's finding
    ("79", "McGreivy & Hakim's reported percentage"),
    ("60", "the numerator of McGreivy & Hakim's 60-of-76"),
    ("76", "the denominator of McGreivy & Hakim's 60-of-76"),
    ("0.7", "the leading coefficient of the Wakao-Funazkri dispersion correlation, as cited"),
    ("0.5", "the second coefficient of the Wakao-Funazkri dispersion correlation, as cited"),
    ("9.7", "the constant in Edwards & Richardson's mechanical coefficient, as cited"),
    ("1.1", "a disagreement threshold the text declares, not a measured value"),
    ("1.5", "a disagreement threshold the text declares, not a measured value"),
    ("95", "the 95 % crossing, which DEFINES the t95 breakthrough time"),
    ("7", "the power of an earlier null, as recorded in retraction A22"),
    # thresholds and definitions fixed by the protocol, not measured
    ("50", "the 50 % crossing, which DEFINES the t50 breakthrough time"),
    ("0.2", "the R-squared threshold at which usable coefficient modes are counted"),]

# Merge with a duplicate check: a repeated literal means two different justifications
# were written for the same number and one of them would be lost.
ALLOWED = {}
for _k, _why in _ALLOWED_PAIRS:
    if _k in ALLOWED:
        raise SystemExit(
            f"build_paper.py: literal {_k!r} is declared twice in _ALLOWED_PAIRS, with "
            f"reasons {ALLOWED[_k]!r} and {_why!r}. Keep one, or the other reason is "
            f"silently discarded.")
    ALLOWED[_k] = _why

MACRO = re.compile(r"\\n([A-Za-z]+)")
# a numeral not immediately preceded by a backslash-command or a letter
NUMERAL = re.compile(r"(?<![\\A-Za-z0-9.])(\d+(?:\.\d+)?)")


def mangled(body, defined):
    """Macro names appearing WITHOUT their leading backslash-n.

    The third check, and it exists because the first two both missed a real break.
    An editing pass that loses the backslash turns `\\nLedgerA` into the literal word
    `LedgerA`: it is no longer a macro reference, so check 1 cannot see it, and it is
    not a numeral, so check 2 cannot either. The manuscript then renders a stray
    identifier where a number should be, and the build reports success.

    That is precisely B37's shape -- a gate defeated by the absence of something --
    committed inside the gate written to prevent hand-typed numbers.

    The mangling has a signature: only the leading `\\n` is lost, so the TRAILING
    LaTeX spacing survives and the wreck reads `LedgerA\\ withdrawn` or `Gates{}`.
    Keying on that trailing token rather than on the bare name is what keeps the
    check from firing on ordinary English -- `\\paragraph{Gates.}` is a heading, not a
    broken macro, and an earlier version of this function flagged it.
    """
    out = []
    for i, line in enumerate(body.splitlines(), 1):
        for name in defined:
            for m in re.finditer(re.escape(name) + r"(\\|\{\})", line):
                if line[max(0, m.start() - 2):m.start()] != "\\n":
                    out.append((i, name, line.strip()[:100]))
    return out


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
    # Drop the UNIT, keep the VALUE. Stripping both let six experimental inputs reach
    # the paper ungated (audit_hygiene #2).
    text = re.sub(r"\\SI\{([^}]*)\}\{[^}]*\}", r" \1 ", text)
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

    # The citation gate. It regenerates references.bib and refuses an unverified
    # entry, a cited-but-missing key, or a given name with no fetched provenance
    # (rule 11). Until 2026-09-25 nothing in the build ran it, so a bibliography
    # that violated rule 11 built green.
    r = subprocess.run([sys.executable, os.path.join(ROOT, "paper", "references.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        print("\nThe citation gate refused. The manuscript may not be built.")
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

    broken = mangled(b, defined)

    # Check 4: numbers written as WORDS (audit_hygiene #3). A ratchet, not a ban --
    # see paper/number_words.py. An unreviewed number-word refuses the build; the
    # reviewed-but-OWED ones are counted on every build so the debt stays visible.
    # Check 5: an UNESCAPED percent sign right after a quantity. In LaTeX `%` starts a
    # comment, so "\nX\,% of the samples" silently deletes the rest of the line from the
    # PDF -- and every other check runs AFTER comments are stripped, so none can see it.
    # Caught 2026-09-27 in an edit of this very session before it was built.
    raw_body = src.split(r"\begin{document}", 1)[-1]
    bad_pct = [(i, ln.strip()[:100]) for i, ln in enumerate(raw_body.splitlines(), 1)
               if re.search(r"(\\,|\\\s|\d|\\n[A-Za-z]+\{\})%", ln)]
    for ln, ctx in bad_pct:
        print(f"  UNESCAPED %  line {ln}: {ctx}")
    if bad_pct:
        print("\nBUILD REFUSED: an unescaped % after a quantity comments out the rest of the line.")
        sys.exit(1)

    sys.path.insert(0, os.path.join(ROOT, "paper"))
    import number_words
    nw_unreviewed, nw_owed, nw_stale = number_words.check(b, strip_structural)

    print(f"\nmacros: {len(used)} used, {len(undefined)} undefined, "
          f"{len(broken)} mangled, {len(unused)} declared but unused")
    for k in undefined:
        print(f"  UNDEFINED  \\n{k}")
    for ln, name, ctx in broken:
        print(f"  MANGLED    {name} lost its backslash at line {ln}: {ctx}")
    if args.report or hits:
        print(f"\nbare numerals in the body: {len(hits)}")
        seen = {}
        for ln, tok, ctx in hits:
            seen.setdefault(tok, []).append((ln, ctx))
        for tok in sorted(seen, key=lambda t: -len(seen[t])):
            ln, ctx = seen[tok][0]
            print(f"  {tok:>8}  x{len(seen[tok]):<3} line {ln}: {ctx}")

    print(f"number-words: {len(nw_unreviewed)} unreviewed, {len(nw_owed)} OWED "
          f"(measured quantities still in words), {len(nw_stale)} stale review entries")
    for ln, w, k in nw_unreviewed:
        print(f"  UNREVIEWED number-word at line {ln}: {k}")
    if undefined or hits or broken or nw_unreviewed:
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
