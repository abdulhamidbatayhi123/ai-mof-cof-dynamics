"""Pre-submission checks for Paper 2's Stage-1 manuscript (paper2/stage1.tex).

Owner of audit_2026-10-12/stage1_checks.json. Exit 1 if any HARD check fails.
HARD checks:
  * the frozen pre-registration is byte-identical to the freeze commit d562f19;
  * the build log has no undefined reference or citation and no LaTeX error;
  * title <= 15 words, abstract <= 200 words with no citation (Nature Communications);
  * every \\cite key has a \\bibitem and every \\bibitem is cited;
  * CRLF line endings throughout;
  * every pre-declared verdict phrase in the manuscript occurs verbatim in the prereg.
REVIEW list (printed, not failing): every number in the prose that occurs neither in the
frozen prereg nor in a source file named in a provenance comment. Each must be read by
hand and either traced or removed.

    python check_stage1_p2.py           (after compiling paper2/stage1.tex)
"""
import json
import os
import re
import subprocess
import sys

TEX, LOG = "paper2/stage1.tex", "paper2/stage1.log"
PREREG, FREEZE = "PREREG_P2_discoverability.md", "d562f195ac7e30f0b7abe039946f4f2bd8b3ad6d"
OUT = "audit_2026-10-12/stage1_checks.json"
BS = chr(92)

raw = open(TEX, "rb").read()
tex = raw.decode("utf-8")
prereg = open(PREREG, encoding="utf-8").read()
hard, review = {}, []


def words(s):
    s = re.sub(r"%.*", "", s)
    s = re.sub(r"\$[^$]*\$", " X ", s)                    # a formula counts as one word
    s = re.sub(BS + BS + r"[a-zA-Z]+\*?(\[[^]]*\])?", " ", s)
    s = re.sub(r"[{}~]", " ", s)
    return [w for w in s.split() if re.search(r"[A-Za-z0-9]", w)]


# 1. frozen prereg unchanged since the freeze
frozen = subprocess.run(["git", "show", f"{FREEZE}:{PREREG}"], capture_output=True).stdout
hard["prereg_unchanged_since_freeze"] = frozen == open(PREREG, "rb").read()

# 2. build log
log = open(LOG, encoding="utf-8", errors="replace").read() if os.path.exists(LOG) else ""
hard["log_exists"] = bool(log)
hard["no_undefined_refs_or_cites"] = not re.search(r"undefined", log, re.I)
hard["no_latex_errors"] = not re.search(r"^! ", log, re.M)
overfull = [float(x) for x in re.findall(r"Overfull \\hbox \(([0-9.]+)pt", log)]

# 3. title and abstract
title = re.search(BS + BS + r"title\{(.*?)" + BS + BS + BS + BS, tex, re.S).group(1)
abstract = tex.split(BS + "begin{abstract}")[1].split(BS + "end{abstract}")[0]
n_title, n_abs = len(words(title)), len(words(abstract))
hard["title_le_15_words"] = n_title <= 15
hard["abstract_le_200_words"] = n_abs <= 200
hard["abstract_has_no_citation"] = BS + "cite" not in abstract

# 4. citations <-> bibliography
body = tex.split(BS + "begin{thebibliography}")[0]
body_nocomment = re.sub(r"(?<!\\)%.*", "", body)
cited = set()
for grp in re.findall(BS + BS + r"cite[pt]?\{([^}]*)\}", body_nocomment):
    cited.update(k.strip() for k in grp.split(","))
items = set(re.findall(BS + BS + r"bibitem\{([^}]+)\}", tex))
hard["every_cite_has_bibitem"] = not (cited - items)
hard["every_bibitem_cited"] = not (items - cited)

# 5. line endings
hard["crlf_only"] = raw.count(b"\n") == raw.count(b"\r\n")

# 6. verdict phrases verbatim in the prereg (braced placeholders normalised)
def canon(s):
    s = s.replace(BS + "{", "{").replace(BS + "}", "}")
    return re.sub(r"\s+", " ", s).strip().lower()


phrases = [canon(p) for p in re.findall(BS + BS + r"verdict\{((?:[^{}]|\\\{|\\\}|\{[^{}]*\})*)\}", body)]
pre_c = canon(prereg)
missing = sorted({p for p in phrases if p not in pre_c})
# the prereg writes some words with markdown bold: also try with ** removed
missing = [p for p in missing if p not in canon(prereg.replace("**", ""))]
hard["verdict_phrases_in_prereg"] = not missing

# 7. number provenance (REVIEW, not hard)
sources = set(re.findall(r"(results/[A-Za-z0-9_.\-]+\.json|p2_generate\.log|tests/test_p2\.py"
                         r"|research/[A-Za-z0-9_.\-]+\.md|p2/[a-z_]+\.py)", tex))
src_text = prereg
for s in sources:
    if os.path.exists(s):
        src_text += "\n" + open(s, encoding="utf-8", errors="replace").read()
# Numbers traced by hand: value as printed -> where it comes from (rounded or derived).
TRACED = {
    "0.9": "research/lit_equation_discovery.md S1 addendum: Da = kL/v ~ 0.86",
    "2.4": "tests/test_p2.py mass-balance test comment 'measured 0.024'",
    "7.5": "tests/test_p2.py success-metric test: -0.0215 against 0.02 accepted",
    "3.84": "p2/identifiability.py: 2*(max loglik - loglik) <= 3.84",
    "414": "p2_generate.log: slowest main-grid solve 414 s",
    "2.6": "requirements_p2_venv.txt: pysr==2.6.1 (software version, printed as 2.6.1)",
    "0.761": "results/p2_operating_characteristics.json h2c_refined n20 log10 2: 0.489 + 0.272",
    "0.98": "results/p2_operating_characteristics.json h2c_refined n20 0.40: 0.901 + 0.079",
    "0.054": "results/p2_operating_characteristics.json h2b n20 gap 0: before 0.024 + outlives 0.03",
    "0.088": "results/p2_operating_characteristics.json single_boundary n20 slope 3 sd 0.0882",
    "0.143": "results/p2_operating_characteristics.json single_boundary n20 slope 1.5 sd 0.1428",
    "0.068": "results/p2_operating_characteristics.json single_boundary n20 slope 6 sd 0.0684",
    "863": "results/p2_operating_characteristics.json runtime_s 862.8",
    "0.008": "results/p2_operating_characteristics.json h2b n40 gap 0: before 0.004 + outlives 0.004",
    "144": "p2_operating_characteristics.py h2a(): 144 cells per slice (simulation setting)",
}
prose = body.split(BS + "begin{document}")[1]
prose = re.sub(r"(?<!\\)%.*", "", prose)
prose = re.sub(BS + BS + r"renewcommand\{" + BS + BS + r"arraystretch\}\{[0-9.]+\}", " ", prose)
for cmd in ("texttt", "url", "href", "label", "ref", "cite", "citep", "renewcommand",
            "begin", "includegraphics"):
    prose = re.sub(BS + BS + cmd + r"\{[^}]*\}", " ", prose)
prose = re.sub(r"[pm]\{[0-9.]+cm\}|[0-9.]+(cm|pt)", " ", prose)       # column widths, lengths
prose = re.sub(r"\b[0-9a-f]{7,40}\b", " ", prose)                   # commit hashes
num_re = r"(?<![A-Za-z_\\0-9.])(\d+(?:\.\d+)?)(?![0-9])"
numbers = sorted(set(re.findall(num_re, prose)), key=lambda x: float(x))
ignore = {str(i) for i in range(0, 11)} | {"2026", "2025", "2024", "2023"}
for n in numbers:
    if n in ignore or n in TRACED:
        continue
    if re.search(r"(?<![0-9.])" + re.escape(n) + r"(?![0-9])", src_text):
        continue
    ctx = [m.start() for m in re.finditer(num_re.replace(r"(\d+(?:\.\d+)?)", "(" + re.escape(n) + ")"), prose)]
    snippet = " | ".join(" ".join(prose[max(0, c - 60):c + 40].split()) for c in ctx[:2])
    review.append({"number": n, "context": snippet})

res = {"hard": hard, "title_words": n_title, "abstract_words": n_abs,
       "cited_not_in_bib": sorted(cited - items), "bib_not_cited": sorted(items - cited),
       "verdict_phrases_missing_from_prereg": missing,
       "overfull_pt": overfull, "provenance_sources": sorted(sources), "traced_by_hand": TRACED,
       "numbers_to_review": review}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in hard.items():
    print(f"{'PASS' if v else 'FAIL'}  {k}")
print(f"title {n_title} words; abstract {n_abs} words; {len(items)} references; "
      f"overfull boxes {overfull}")
if missing:
    print("verdict phrases not in prereg:", missing)
print(f"numbers to review by hand: {len(review)}")
for r in review:
    print(f"  {r['number']:>10s}  {r['context'][:150]}")
sys.exit(0 if all(hard.values()) else 1)
