"""Numbers written as English words: the hole in the numerals gate (audit_hygiene #3).

build_paper.py refuses any DIGIT that is not a macro resolved from a results file.
It could not see "Six are eliminated", "about one per cent" or "eleven of fifty-four
runs" -- measured or counted quantities with no script behind them, in a paper whose
methods section claims every number has one. Two audits found ~40 of them.

Most number-words are prose ("two waves", "one term", "third-type boundary
condition"), so a blanket ban is wrong and a keyword allow-list is too blunt. This is
a RATCHET instead:

  * every number-word occurrence is keyed by its surrounding text (not its line
    number, so edits elsewhere do not disturb it) and must appear in
    paper/number_words.json with a class and a reason:
        PROSE   not a quantity (structural English, a boundary-condition type, ...)
        DESIGN  a count fixed by the protocol, not measured (three seeds, five folds)
        CITED   a number reported by a cited paper, not by us
        OWED    a measured or counted result still in words -- it needs a macro
  * an occurrence with NO entry fails the build: a new number-word must be reviewed;
  * OWED entries are counted and printed on every build, like PENDING values, so the
    debt is visible and cannot be mistaken for a clean manuscript.

Converting an OWED sentence to a macro removes its occurrence; `--prune` then drops
the stale entry.

    python paper/number_words.py            # report
    python paper/number_words.py --prune    # drop entries whose text is gone
    python paper/number_words.py --classify SUBSTRING CLASS "reason"
                                            # review UNREVIEWED occurrences whose
                                            # key contains SUBSTRING
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "paper", "manuscript.tex")
REVIEWED = os.path.join(ROOT, "paper", "number_words.json")

_W = (r"(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
      r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
      r"sixty|seventy|eighty|ninety|hundred|thousand|million|half|halves|third|thirds|"
      r"quarter|quarters|fifth|fifths|tenth|tenths|twentieth|dozen|twice|double|triple|"
      r"[a-z]+fold)")
WORD = re.compile(r"(?i)\b" + _W + r"(?:-" + _W + r")?\b")
# Phrases in which a number-word is grammar, never a quantity. Kept deliberately
# short: anything not here must be reviewed individually.
STRUCTURAL = re.compile(
    r"(?i)\b(one|two|three)-(dimensional|wave|landmark|shift|term|step|parameter|sided|"
    r"layer|point|site|stage|mode)\b|\bone of\b|\bthe one\b|\bone another\b|\bno one\b|"
    r"\bone (?:is|that|which|we)\b|\bspans? zero\b|\bspanning zero\b|\bbelow zero\b|"
    r"\bfrom zero\b|\bis zero\b|\bexactly zero\b")
CLASSES = {"PROSE", "DESIGN", "CITED", "OWED"}
CTX = 30


def occurrences(body_text, strip):
    """(line, word, key) for every number-word not excused as structural."""
    out = []
    for i, line in enumerate(body_text.splitlines(), 1):
        s = strip(line)
        s = STRUCTURAL.sub(lambda m: " " * len(m.group(0)), s)
        for m in WORD.finditer(s):
            left = re.sub(r"\s+", " ", s[max(0, m.start() - CTX):m.start()]).strip()
            right = re.sub(r"\s+", " ", s[m.end():m.end() + CTX]).strip()
            out.append((i, m.group(0), f"{left} [{m.group(0)}] {right}"))
    return out


def load():
    if not os.path.exists(REVIEWED):
        return {}
    return {e["key"]: e for e in json.load(open(REVIEWED, encoding="utf-8"))}


def check(body_text, strip):
    """Return (unreviewed, owed, stale). unreviewed is a hard failure."""
    rev = load()
    occ = occurrences(body_text, strip)
    seen = {k for _, _, k in occ}
    unreviewed = [(i, w, k) for i, w, k in occ if k not in rev]
    owed = [(i, w, k, rev[k]["reason"]) for i, w, k in occ
            if k in rev and rev[k]["class"] == "OWED"]
    bad_class = [k for k, e in rev.items() if e["class"] not in CLASSES]
    if bad_class:
        raise SystemExit(f"number_words.json: unknown class on {bad_class[:3]}")
    stale = sorted(set(rev) - seen)
    return unreviewed, owed, stale


def main():
    sys.path.insert(0, ROOT)
    import build_paper as bp
    body_text = bp.body(open(TEX, encoding="utf-8").read())
    unreviewed, owed, stale = check(body_text, bp.strip_structural)
    if "--classify" in sys.argv:
        i = sys.argv.index("--classify")
        sub, cls, why = sys.argv[i + 1], sys.argv[i + 2], sys.argv[i + 3]
        if cls not in CLASSES:
            raise SystemExit(f"class must be one of {sorted(CLASSES)}")
        hits = [(ln, w, k) for ln, w, k in unreviewed if sub in k]
        if not hits:
            raise SystemExit(f"no UNREVIEWED occurrence contains {sub!r}")
        rev = load()
        for ln, w, k in hits:
            rev[k] = {"key": k, "word": w, "class": cls, "reason": why, "line_at_review": ln}
            print(f"classified {cls}: line {ln}: {k}")
        json.dump(list(rev.values()), open(REVIEWED, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        unreviewed, owed, stale = check(body_text, bp.strip_structural)
    if "--prune" in sys.argv and stale:
        rev = load()
        keep = [e for k, e in rev.items() if k not in set(stale)]
        json.dump(keep, open(REVIEWED, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"pruned {len(stale)} stale entr(y/ies)")
    print(f"{len(owed)} measured quantit(y/ies) still written in words (OWED):")
    for i, w, k, why in owed:
        print(f"  line {i:>4}: {k}  -- {why}")
    if unreviewed:
        print(f"\n{len(unreviewed)} UNREVIEWED number-word(s) -- classify in paper/number_words.json:")
        for i, w, k in unreviewed:
            print(f"  line {i:>4}: {k}")
        sys.exit(1)


if __name__ == "__main__":
    main()
