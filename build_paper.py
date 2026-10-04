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
NUMBERS_PY = os.path.join(ROOT, "paper", "numbers.py")

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

# audit_hygiene #12: a reason is written for ONE sentence, but the allow-list alone
# admits the literal everywhere ("Accuracy improved by 60 per cent" passed on
# McGreivy's 60-of-76). So each literal is also bound to how many times it occurs in
# the body. A new occurrence changes the count and refuses the build until someone
# looks at the new sentence and re-states why it is not a result. A count of 0 marks
# a reason whose sentence has gone: the literal may not come back unreviewed.
ALLOWED_COUNT = {
    "0": 2, "0.2": 3, "0.5": 1, "0.7": 1, "1": 12, "1.1": 1, "1.5": 1, "2": 17,
    "3": 1, "4": 4, "5": 1, "6": 3, "7": 1, "8": 4, "9.7": 1, "10": 7, "12": 7,
    "20": 2, "24": 1, "48": 5, "50": 3, "60": 1, "64": 3, "76": 1, "79": 1, "80": 3,
    "95": 3, "96": 3, "99.9": 2, "128": 2, "192": 11, "240": 4, "256": 1,
    "1948": 1, "1953": 1, "1954": 1, "1982": 1,
    "216": 0, "17": 0, "3947": 0, "2000": 0, "29": 0, "1959": 0, "1908": 0, "11": 0,
}
if set(ALLOWED_COUNT) != set(ALLOWED):
    raise SystemExit("build_paper.py: ALLOWED_COUNT and _ALLOWED_PAIRS disagree on "
                     f"{sorted(set(ALLOWED_COUNT) ^ set(ALLOWED))}; every literal needs both.")

MACRO = re.compile(r"\\n([A-Za-z]+)")
# a numeral not immediately preceded by a backslash-command or a letter
# audit_hygiene #13: a leading-decimal number (".55") was invisible; now matched.
NUMERAL = re.compile(r"(?<![\\A-Za-z0-9.])(\d+(?:\.\d+)?|\.\d+)")


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

    audit_hygiene #11: that signature only covers macros written with trailing `\\ ` or
    `{}`; `\\nGates gates` or `\\nLedgerA.` mangle into bare words it cannot see. So any
    defined name standing as a WHOLE WORD without its `\\n` is flagged, and the English
    homographs are allowed by their exact CONTEXT (MANGLED_OK), never by name alone.
    """
    out = []
    for i, line in enumerate(body.splitlines(), 1):
        for name in defined:
            for m in re.finditer(r"(?<![\\A-Za-z])" + re.escape(name) + r"\b", line):
                if line[max(0, m.start() - 2):m.start()] == "\\n":
                    continue
                if any(n == name and c in line for n, c in MANGLED_OK):
                    continue
                out.append((i, name, line.strip()[:100]))
    return out


# (macro name, exact line context) pairs where the bare word is English, not a wreck.
MANGLED_OK = [("Gates", r"\paragraph{Gates.}")]


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
    # audit_hygiene #13: only a CAPITALISED name (MOF-303, PCA-Net) is exempt; the old
    # pattern also exempted "about-55", a number hyphenated to an ordinary word.
    text = re.sub(r"\b[A-Z][A-Za-z]*-\d+[A-Za-z]*", " ", text)
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
    ap.add_argument("--pdf", action="store_true",
                    help="also COMPILE with tools/tectonic.exe and refuse on any LaTeX error, "
                         "undefined reference or undefined citation. Until 2026-09-28 nothing "
                         "compiled the manuscript at all; the gates checked text, not a document.")
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
    seen = {k: [] for k in ALLOWED}
    for i, line in enumerate(b.splitlines(), 1):
        for m in NUMERAL.finditer(strip_structural(line)):
            tok = m.group(1)
            if tok in ALLOWED:
                seen[tok].append((i, line.strip()[:110]))
                continue
            hits.append((i, tok, line.strip()[:110]))
    # an allowed literal whose occurrence count moved is reported as a hit on every
    # occurrence, so the reviewer sees each sentence, not just a number
    for tok, occ in seen.items():
        if len(occ) != ALLOWED_COUNT[tok]:
            for i, ctx in occ or [(0, "(no occurrence left)")]:
                hits.append((i, tok, f"[allowed {ALLOWED_COUNT[tok]}x, found {len(occ)}x: "
                                     f"re-justify or update ALLOWED_COUNT] {ctx}"))

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
    # Check 6: control characters. A script that writes "\nMacro\times" through a
    # string literal produces a NEWLINE + "Macro" + a TAB + "imes" (hit 2026-09-27;
    # the mangled check keys on trailing LaTeX spacing and missed it). The manuscript
    # contains no legitimate tab, so any tab is corruption.
    tabs = [i for i, ln in enumerate(raw_body.splitlines(), 1) if "\t" in ln]
    if tabs:
        print(f"  CONTROL CHARACTER (tab) at line(s) {tabs[:8]} -- a backslash escape was "
              f"written as a real character")
        bad_pct = bad_pct or [(tabs[0], "tab")]
    if bad_pct:
        print("\nBUILD REFUSED: an unescaped % after a quantity comments out the rest of the line.")
        sys.exit(1)

    # Check 7: every results file the manuscript reads must have an OWNER -- a script that
    # writes it. Unowned files carried headline numbers seven times (B21, B43, B63, the
    # L5 verdict, B70, and B71 twice). Detected: a script naming the file that also dumps
    # JSON. Declared: OWNERS below, for writers whose path is built at run time.
    OWNERS = {
        "results/validation.json": "validate.py --json",
        "results/dataset_summary_legacy.json": "dataset_summary.py --root data/parametric --out ...",
        "results/l3_results_B24_WITHDRAWN.json": "run_l3.py output, renamed when B24 withdrew it",
    }
    import glob
    import importlib.util
    spec = importlib.util.spec_from_file_location("_nums", NUMBERS_PY)
    _n = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_n)
    srcs = {}
    for pth in glob.glob(os.path.join(ROOT, "*.py")) + glob.glob(os.path.join(ROOT, "p2", "*.py")):
        name = os.path.basename(pth)
        if name.startswith("fig") or name in ("validate.py", "build_paper.py"):
            continue
        srcs[name] = open(pth, encoding="utf-8", errors="replace").read()
    unowned = []
    for f in sorted({s[1] for s in _n.SPEC}):
        base = os.path.basename(f)
        writers = [n for n, s in srcs.items() if base in s and re.search(r"json\.dump|write_atomic", s)]
        if not writers and f not in OWNERS:
            unowned.append(f)
    if unowned:
        print("  UNOWNED results file(s) -- no script writes them:\n    " + "\n    ".join(unowned))
        print("\nBUILD REFUSED: rule 10 -- an unowned number is indistinguishable from a wrong one.")
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

    if args.pdf:
        tect = os.path.join(ROOT, "tools", "tectonic.exe")
        if not os.path.exists(tect):
            print("\n--pdf: tools/tectonic.exe not found (see CONTINUE_HERE); cannot compile.")
            sys.exit(1)
        r = subprocess.run([tect, "--keep-logs", "manuscript.tex"], cwd=os.path.join(ROOT, "paper"),
                           capture_output=True, text=True)
        log = os.path.join(ROOT, "paper", "manuscript.log")
        text = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
        bad = [ln for ln in text.splitlines()
               if ln.startswith("!") or "undefined" in ln.lower() and ("reference" in ln.lower()
                                                                      or "citation" in ln.lower())]
        if r.returncode != 0 or bad:
            print("\nCOMPILE REFUSED:\n  " + "\n  ".join(bad[:10] or [r.stderr.strip()[-400:]]))
            sys.exit(1)
        over = [ln for ln in text.splitlines() if ln.startswith("Overfull") and
                float(ln.split("(")[1].split("pt")[0]) > 20]
        print(f"\nCOMPILED: paper/manuscript.pdf; {len(over)} overfull box(es) wider than 20 pt")
        for ln in over:
            print("  " + ln[:100])


if __name__ == "__main__":
    main()
