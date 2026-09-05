"""Count the correction ledger, so the count is never typed anywhere.

`RETRACTIONS.md` is the source of truth for what has been withdrawn and what was
caught. Its counts are quoted in `README.md`, `CONTINUE_HERE.md`,
`NEW_SESSION_PROMPT.md`, `MANUSCRIPT_OUTLINE.md`, `RESULTS.md` and the manuscript
itself -- seven places, updated by hand every time an entry is added. In one session
they drifted three times, and the manuscript gate caught the last one.

A number quoted in seven documents and maintained in none of them is B43's defect
with extra steps. This counts the ledger and writes the result where
`paper/numbers.py` can read it.

    python ledger_counts.py           # writes results/ledger_counts.json
"""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "RETRACTIONS.md")
OUT = os.path.join(ROOT, "results", "ledger_counts.json")

ROW = re.compile(r"^\| \*\*([AB])(\d+)\*\* \|(.*)$", re.M)


def main():
    text = open(SRC, encoding="utf-8").read()
    rows = ROW.findall(text)
    part = {"A": [], "B": []}
    own = []
    for letter, num, body in rows:
        key = f"{letter}{num}"
        if key in part[letter]:
            raise SystemExit(f"duplicate ledger entry {key}")
        part[letter].append(key)
        if "our own error" in body.lower():
            own.append(key)

    for letter in "AB":
        nums = sorted(int(k[1:]) for k in part[letter])
        expected = list(range(1, len(nums) + 1))
        if nums != expected:
            missing = sorted(set(expected) - set(nums))
            extra = sorted(set(nums) - set(expected))
            raise SystemExit(f"Part {letter} is not a contiguous run from 1: "
                             f"missing {missing}, unexpected {extra}")

    out = {
        "source": "RETRACTIONS.md",
        "n_part_a": len(part["A"]),
        "n_part_b": len(part["B"]),
        "n_total": len(part["A"]) + len(part["B"]),
        "n_own_error_phrase": len(own),
        "own_error_entries": own,
        "note": "n_own_error_phrase counts entries containing the literal words "
                "'our own error'. Several more are self-attributed in other words; "
                "they are named in RESULTS.md rather than counted here, because a "
                "count needs a rule and 'self-attributed' has no mechanical one.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"ledger: {out['n_part_a']} Part-A, {out['n_part_b']} Part-B, "
          f"{out['n_total']} total; {out['n_own_error_phrase']} carry the words "
          f"'our own error'")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
