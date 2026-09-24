# hygiene

validate.py's 24 gates are individually well-built but the harness leaks in exactly the shape working rule 6 names: six solver gates report PASS when their dataset is absent (proven empirically), contradicting validate.py's own docstring, and both ground-truth .npz files are gitignored so this is the state of every clone. build_paper.py refuses hand-typed digits but cannot see numbers spelled in English words, numbers inside \SI{}{} (six live in the manuscript today), or numbers hyphenated to a word — and validate.py's mirror of that check omits the mangled-macro test that B64 produced. The ledger count is correct and agrees with results/ledger_counts.json (26 A, 64 B, 90 total, 31 "our own error"); the kaggle/SINDy housekeeping is safe to delete except that RETRACTIONS.md A7's evidence and one tracked stale dataset ride along with it.

## 1. [blocking] validate.py:496-717

**What.** Six solver gates return PASS when their dataset file is absent, instead of SKIP or FAIL. Five of them catch the per-dataset Skip and append a row — `except Skip as e: rows.append(f"{Path(path).name}: SKIP ({e})"); continue` (lines 503-505, 531-533, 636-638, 696-698) — which makes `rows` non-empty, so the guard `if not rows: raise Skip("no datasets present")` at lines 512-513, 567-568, 652-653, 715-716 is unreachable dead code and `ok` is still True at the return. `gate_grid_converged` does it directly: `if not p.exists(): rows.append(f"{Path(path).name}: SKIP (absent)"); continue` (584-586). `gate_mtz_resolvable` sets `nz = None` and appends `f"{kind}: MTZ ... (no dataset)"` (line 620) without ever setting `ok = False`. Verified by pointing DATASETS at two nonexistent paths: gate_breakthrough_occurs, gate_front_resolved, gate_grid_converged, gate_mass_closure, gate_no_negative and gate_mtz_resolvable all returned PASS. This directly contradicts the module docstring at lines 11-12: "A gate that cannot run (missing file, failed import) is reported as SKIP, never as PASS."

**Why.** These six gates are the entire guarantee that the ground truth is a resolved, mass-conserving, physical solution. .gitignore:7 (`data/*.npz`) leaves both data/synthetic_breakthrough.npz and data/mof303_breakthrough.npz untracked (confirmed: `git ls-files` knows neither), so on any fresh clone the harness prints six green PASS lines about data that is not there, exit code 0. A referee who clones the repo and runs the harness gets a clean bill of health for a solver whose output is absent — and paper/numbers.py reads MassClosure/GridConv/GridNz out of that same run.

**Fix.** In each of the five Skip-catching gates, set `ok = False` (or collect the skipped paths and `raise Skip` if ALL datasets are missing, FAIL if only some are) instead of silently appending a row. In gate_grid_converged replace the `if not p.exists(): rows.append(...); continue` at 584-586 with the same rule. In gate_mtz_resolvable set `ok = False` in the `nz is None` branch at line 620. Then delete the now-live `if not rows: raise Skip` guards or keep them as the all-missing path.

## 2. [blocking] paper/manuscript.tex:294-296

**What.** build_paper.py strips \SI wholesale: `text = re.sub(r"\\SI\{[^}]*\}\{[^}]*\}", " ", text)   # \SI carries its own units` (build_paper.py:158). The comment justifies removing the UNIT argument but the substitution removes the VALUE with it. Six hand-typed experimental numbers currently ride through that hole: `a \SI{6.35}{\milli\metre} bed in a \SI{38.1}{\milli\metre} tube, ambient air at \SI{32.8}{\percent} relative humidity, \SI{298.15}{\kelvin}, bulk density \SI{429.6}{\kilo\gram\per\metre\cubed}`. Confirmed by probe: `\SI{55}{\percent} of runs.` yields zero numerals seen.

**Why.** siunitx is loaded (manuscript.tex:16) and \SI is the canonical way to write a measured quantity in this venue, so the gate that exists to stop hand-typed numbers is blind to the single most likely container for one. These particular six are the Lassitter-2024 anchor's bed geometry and operating conditions — the values the paper's only experimental comparison is built on — and they have no macro, no results file and no ALLOWED entry behind them. That is B21/B43 reproduced inside the fix for B21/B43.

**Fix.** Change the substitution to keep the value and drop only the unit: `re.sub(r"\\SI\{([^}]*)\}\{[^}]*\}", r" \1 ", text)`. Then either promote the six numbers to macros sourced from the digitised-anchor results file, or add them to _ALLOWED_PAIRS with the reason "reported by Lassitter et al. 2024 SI, quoted as that paper's stated condition" (the pattern already used for the McGreivy numbers at lines 85-87).

## 3. [blocking] build_paper.py:108

**What.** `NUMERAL = re.compile(r"(?<![\\A-Za-z0-9.])(\d+(?:\.\d+)?)")` matches digits only. Nothing in build_paper.py or validate.py looks for a number spelled in English. Confirmed by probe: 'The speedup is fifty-five times.' and 'A five hundred per cent improvement.' both yield zero numerals seen. The manuscript body currently contains 194 English number-word tokens, including results: manuscript.tex:41 "Six are eliminated." (the count of falsified candidate explanations — a headline finding of the ladder), :38 "Seven candidate explanations were named in advance", :45 and :472 "across eight learning rates spanning three and a half decades", :137 "verified against four closed-form solutions", and :175 "about one per cent" — a mass-closure value stated in words two lines above the same quantity written correctly as the macro \nMassClosure.

**Why.** The gate's whole claim is "every numeral in the manuscript must be a macro resolved from a results file". A number written as a word is still a number in the rendered PDF and still has no script behind it, so the strongest sentence in the paper's methods section is false as written. manuscript.tex:175 is the sharpest case: the same measurement appears twice on adjacent lines, once gated and once not, which is precisely the drift the macro system was built to prevent.

**Fix.** Add a third check to build_paper.main() and mirror it in validate.gate_manuscript_numbers: scan strip_structural(line) for `\b(zero|one|two|...|ninety|hundred|thousand|million|dozen|half|third|quarter|[a-z]+fold)\b` and report each hit with its line, with an ALLOWED_WORDS list for genuinely non-quantitative usages ("one-dimensional", "two-dimensional", "on the other hand"). Start by converting manuscript.tex:41 "Six are eliminated" into a macro read from the ladder verdict file — that one is a result, not prose.

## 4. [blocking] paper/numbers.py:268

**What.** `("Gates", "results/validation.json", "n_pass", "{:d}")`. The manuscript's \nGates macro is the PASS COUNT, not the gate count. Nothing in numbers.py, build_paper.py or validate.py ever reads `n_fail` or `n_skip` (grep confirms no occurrence of either in paper/numbers.py). validate.py writes all three at lines 1088-1090 and they are simply ignored.

**Why.** If a gate fails or skips, \nGates silently shrinks and the paper reports a smaller harness rather than refusing to build. The paper would read "23 gates" where the truth is "24 gates, one failing" — a claim about verification coverage, altered by the very failure it should have blocked. build_paper.py:61-62 explicitly promoted this number from an allow-listed literal to a macro because it "is a RESULT"; making it n_pass turned it into a result that reports its own corruption as a smaller true value.

**Fix.** Source \nGates from `len(gates)` (add `"n_gates": len(records)` to the JSON at validate.py:1088) and add a hard failure in numbers.resolve() or build_paper.main(): if validation.json has `n_fail > 0` or `n_skip > 0` or `only is not None`, refuse the build and name the offending gates. The `only` field is already recorded at line 1089 and currently read by nobody.

## 5. [blocking] validate.py:236-278

**What.** `gate_manuscript_numbers` reimplements build_paper's checks 1 and 2 but never calls check 3. It computes `undefined = sorted(used - defined)` (261) and the numeral `hits` loop (263-266), and there is no reference to `bp.mangled` anywhere in the function — confirmed by string search over the function body. build_paper.mangled() exists only in build_paper.main() at line 191.

**Why.** B64 was a mangled macro — six references that lost their backslash and rendered as stray words. The fix landed in build_paper.py only. Anyone following working rule 1 ("no number from a failing validate.py category") and running `python validate.py` gets PASS on a manuscript full of mangled macros, because the gate that reports on the manuscript does not run the check written for that exact defect. Two documents guarding one artefact with two different rule sets is the same class of drift as the seven hand-maintained ledger counts.

**Fix.** Insert `broken = bp.mangled(body, defined)` after line 261 and fold it into the failure condition at 267 and the message at 268-273, so `validate.py` and `build_paper.py` enforce an identical rule. Better: have build_paper expose a single `check(tex_text, numbers_text) -> (undefined, hits, broken)` and call it from both.

## 6. [blocking] .gitignore:7, 28

**What.** `data/*.npz` is anchored to the repository root, so it hides data/synthetic_breakthrough.npz and data/mof303_breakthrough.npz (`git check-ignore -v` confirms both, and `git ls-files --error-unmatch` reports neither is known to git) but does NOT hide kaggle_run/data/synthetic_breakthrough.npz. `git ls-files "*.npz"` returns exactly one file: kaggle_run/data/synthetic_breakthrough.npz.

**Why.** The only breakthrough dataset the repository actually ships is the one inside the directory RESULTS.md:1151 and 03_LADDER_PROTOCOL.md:1492 both call "a stale duplicate carrying every original defect", and which retraction A3 records as containing no breakthrough at all. The authoritative datasets are absent. Combined with the PASS-on-missing-file defect above, a clone runs the harness against nothing, gets six green solver gates, and the only data on disk is retracted data. AUDIT_2026-08-30 called kaggle_run/ "A LIVE HAZARD" for exactly this reason.

**Fix.** Delete kaggle_run/ (see the housekeeping findings below) which removes the tracked stale .npz. Separately decide the real datasets' provenance: either track them (they are the ground truth every solver gate reads) or add a documented regeneration command to README.md and make the solver gates FAIL, not PASS, when they are absent.

## 7. [major] validate.py:1031, 1096

**What.** `gates = [g for g in REGISTRY if not args.only or g.category == args.only]` accepts any string. A category name that does not exist selects zero gates, the loop body never runs, and `return 1 if n_fail else 0` returns 0. Demonstrated: `python validate.py --only slover --no-color` prints "0 passed, 0 failed, 0 skipped" and exits 0.

**Why.** The module docstring at lines 10-11 offers this as a pre-commit/CI hook. A typo in the category name — or a category renamed later — turns the hook permanently green while running nothing, and nothing in the output says so. A gate suite that reports success for having run no gates is the purest form of the defect this file exists to prevent.

**Fix.** Validate `--only` against `{g.category for g in REGISTRY}` and exit non-zero with the valid list if it does not match; additionally treat `n_pass == 0` as a failure.

## 8. [major] validate.py:1020-1024, 1091-1095

**What.** `--json` has `const="results/validation.json"`, the same default path a full run writes, and `--only` does not change it. The code notices — line 1095 prints `", {args.only} only — NOT a full record"` — but writes the file anyway, at the authoritative path, and records `"only": args.only` in a field nothing reads. `validate.py --only solver --json` overwrites results/validation.json with n_pass=8, and because by_gate then still contains "global mass balance closes" and "solution is grid-converged" with their `values` dicts, every macro in paper/numbers.py:268-273 resolves cleanly. The manuscript builds, reporting \nGates = 8.

**Why.** A keyword default that defeats the gate, precisely as working rule 6 describes. A warning printed to a terminal is not a gate; the artefact on disk is indistinguishable from a full record except by a field nobody consults, and the paper's headline verification claim silently becomes a third of itself.

**Fix.** When `--only` is set, derive the default json path from the category (`results/validation_{only}.json`) or refuse `--json` with `--only` unless an explicit path is given. Independently, make numbers.py refuse a validation.json whose `only` is not null (this pairs with the \nGates fix above).

## 9. [major] validate.py:196

**What.** `draws_model = path.name.startswith("fig") or re.search(r"label\s*=\s*(?:rf|fr|[rbfu])?[\"'][^\"']*(PIKAN|MLP|DeepONet|FNO|WNO|DeepOKAN|POD)", src, re.I)`. The comment two lines above claims "EVERY figure script must declare a provenance whatever its labels say", but "every" is implemented as a filename prefix plus a seven-name keyword list. Enumerating the repository: compare_lassitter.py (which draws Fig7_anchor.png), compare_lassitter_posthoc.py and digitise_lassitter.py all call plt. and are all SKIPPED by this gate, because their names do not start with "fig" and their labels read "this solver, cited MOF-303, primary" (compare_lassitter.py:168) and "authors' COMSOL (fitted CSFR kinetics)" (:169).

**Why.** The gate's stated rule and its implemented rule differ, and the difference is a rename away from being exploited. The escaped scripts are clean today — compare_lassitter.py writes results/lassitter_comparison.json at line 153 — but Figure 7 is the paper's only experimental anchor and it is drawn by a script the anti-fabrication gate does not look at. B37's shape exactly: a gate defeated by the absence of a naming convention.

**Fix.** Drop the filename/label heuristic and check EVERY root *.py that contains `plt.` and writes into figures/, i.e. gate on `re.search(r"figures/", src)` or on a savefig call. Then the provenance rule is what the comment says it is.

## 10. [major] validate.py:180, 205, 218

**What.** Provenance (B) is established by string presence alone. `_RESULTS_PATH = re.compile(r"[\"'](results/[\w./-]+\.json|verify_solver\.json)[\"']")` is applied to the whole source with `named = sorted({m.group(1) for m in _RESULTS_PATH.finditer(src)})`, and the only follow-up is `missing = [p for p in named if not (ROOT / p).exists() and p not in pending]`. Nothing checks that the file is opened, that anything is read from it, or that the plotted array came from it. The same is true of provenance (A): `if "load_state_dict" in src` (line 201) is a substring test that a comment or docstring satisfies.

**Why.** The comment at lines 168-171 promises "(B) is admitted only on proof, never on assertion (B37: a gate that can be bypassed is not a gate)". A quoted filename in a docstring is an assertion. A figure script could hardcode every plotted number and satisfy this gate with one string literal it never uses — which is A1's defect with an extra line of camouflage.

**Fix.** Parse the source with `ast` and require the results path to appear inside a call to `open`/`json.load`/`np.load` whose result is bound and used, and require `load_state_dict` to be an ast.Call rather than a substring. At minimum, require the results path to appear on a line containing `open(` or `load(`.

## 11. [major] build_paper.py:132

**What.** `for m in re.finditer(re.escape(name) + r"(\\|\{\})", line)` — mangled() only recognises a lost backslash when the macro's TRAILING LaTeX spacing survives as `\` or `{}`. Confirmed by probe against the 212 defined macros: 'the gate count is Gates{} today' is caught; 'we ran Gates gates', 'we ran Gates, and stopped' and 'the speedup was LedgerA.' are all missed.

**Why.** The docstring at lines 122-124 states the assumption openly — "only the leading `\n` is lost, so the TRAILING LaTeX spacing survives" — but that only holds for macros the author happened to write as `\nName\ ` or `\nName{}`. A macro written `\nGates gates` (no trailing token, which is legal LaTeX before a word starting with a non-letter, and common before punctuation) mangles into ordinary prose that check 1 cannot see, check 2 cannot see, and check 3 cannot see either. B64 is fixed for the instances that produced it, not for its class.

**Fix.** Also flag a defined macro name appearing as a standalone word not preceded by `\n`: `re.finditer(r"(?<![\\\\A-Za-z])" + re.escape(name) + r"\b", line)` with the `\n`-preceded case excluded, and allow-list the handful of names that are also English words (the docstring notes `\paragraph{Gates.}` was a false positive — allow-list it by context rather than by weakening the pattern).

## 12. [major] build_paper.py:187-188

**What.** `if tok in ALLOWED: continue` — the allow-list is global and positionless. Forty literals are whitelisted for every occurrence anywhere in the document, including ones justified by a single specific sentence: `("60", "the numerator of McGreivy & Hakim's 60-of-76")`, `("50", "the 50 % crossing, which DEFINES the t50 breakthrough time")`, `("80", "the power level at which every MDE is quoted")`, `("29", "an interpolation-floor percentage from a reported exclusion")`, `("0.2", "the R-squared threshold...")`. Probe: 'Accuracy improved by 60 per cent.' passes, on McGreivy's justification.

**Why.** The reasons are described at lines 39-40 as "the audit trail", but the trail does not bind a literal to the place it was justified. A new sentence reporting a fabricated 60 % speedup, an 80 % accuracy, or a 50 % reduction passes the gate on a reason written for a different sentence. The duplicate-key check at lines 98-103 protects the reasons from each other but not from the document.

**Fix.** Make the allow-list positional: store `(literal, line-context-substring, reason)` and require the hit's line to contain the recorded context, or record a per-key expected occurrence count and fail when the count changes. Either turns the reason into something the gate actually enforces.

## 13. [major] build_paper.py:153, 108

**What.** Two shapes of numeral are erased before the check. (a) `text = re.sub(r"[A-Za-z]+-\d+[A-Za-z]*", " ", text)` deletes any digit run hyphenated to a preceding word — probe: 'A factor-55 speedup over the solver.' yields zero numerals seen. (b) NUMERAL's lookbehind `(?<![\\A-Za-z0-9.])` blocks a match whose preceding character is a period, so a decimal written without a leading zero is invisible — probe: 'The error is .55 of the baseline.' yields zero numerals seen.

**Why.** Both render normally in the PDF. "a factor-55 speedup", "an order-3 correction", "the top-10 modes" are ordinary technical prose, and ".55" is a legal and common way to write a fraction. The comment at 150-152 justifies (a) for names like MOF-303 and PCA-Net, which is right, but the pattern is far broader than the justification.

**Fix.** For (a), narrow to a known-name pattern (require the digit run to be followed by a word boundary and the whole token to appear in a NAMES allow-list, or require capitalisation: `[A-Z][A-Za-z]*-\d+`). For (b), change the lookbehind to `(?<![\\A-Za-z0-9])` and let the `\d+(?:\.\d+)?` alternation handle `0.5` — then add `(?:\.\d+)` as a leading alternative so bare `.55` is matched.

## 14. [major] validate.py:89-91, 289-291, 730-731, 773-774, 799-801, 873-875, 959-960, 987-988

**What.** Eight gates convert ANY exception during import into a SKIP: `except Exception as e: raise Skip(f"import failed ({e})")` (730-731, 773-774), `raise Skip(f"torch unavailable ({e})")` (289-291), `raise Skip(f"cannot import solver_fd ({e})")` (89-91), and the same idiom at 799-801, 873-875, 959-960, 987-988. A SyntaxError, NameError or AttributeError raised while importing kan_model, operator_models, baseline_models, pde_adsorption or solver_fd is indistinguishable from "torch is not installed". SKIP does not affect the exit code — `return 1 if n_fail else 0` (line 1096).

**Why.** A real break in a model file silently removes the gates that guard that model file, and the harness still exits 0. gate_temperature_bounded exists because "the head lived in six separate copies across the model files and every copy had the defect" (lines 864-866); if a seventh copy is added with a syntax error, the gate that would catch it disappears with a yellow SKIP line and a zero exit code.

**Fix.** Narrow each to `except ImportError` (or `ModuleNotFoundError`) for the genuinely-absent-dependency case and let every other exception propagate to the runner's `except Exception` at line 1074, which already records FAIL. Separately, make the exit code non-zero when n_skip exceeds a declared expected set, so a suite that stops testing cannot report success.

## 15. [major] validate.py:837, 841, 849

**What.** `for path in sorted(ROOT.glob("run_*.py")) + [ROOT / "train_pikan.py"]` — the boundary-condition gate inspects only files named run_*.py plus one hardcoded name. refine_l4b_v2.py, refine_sweep_l4b_v2.py, learning_curve_v2.py and analyze_* are never examined. Detection is also name-bound in two more ways: `uses_pde = bool(_re.search(r"(?:pde_residual|compute_adsorption_pde_residuals)\s*\(", src))` misses an aliased import, and `calls_bc = bool(_re.search(r"boundary_residuals?\s*\(\s*model", src))` requires the first argument to be literally named `model` and is satisfied by any textual occurrence, including a dead branch.

**Why.** B20 cost "nRMSE 5,480 on temporal extrapolation" (lines 826-828) and the docstring says "Only a structural check catches it". A structural check that stops at a filename prefix is a naming convention. A refinement or sweep script that trains with a PDE residual is exactly where the omission would recur, and it is outside the glob.

**Fix.** Glob all root *.py, skip validate.py, and gate on whether the file trains at all (contains `.backward()` or an optimiser step) rather than on its name. Resolve the residual call through ast so an alias is caught, and require the boundary call to be a live ast.Call with a model-typed first argument rather than a regex on a literal parameter name.

## 16. [major] validate.py:131-136, 143

**What.** The fabrication patterns are narrower than the defect they name. `(r"np\.random\.normal\s*\([^)]*\)\s*(?:#.*)?$", ...)` is anchored to end of line, so `y = np.random.normal(0, 0.001, n) + c_true` does not match; and `np.random.randn`, `np.random.uniform`, `np.random.rand` and `np.random.default_rng().normal()` are not covered at all. The scan is also non-recursive: `for path in sorted(ROOT.glob("*.py"))` (line 143) never descends into kaggle_run/, whose kaggle_main.py:16-21 and sindy_discovery.py:98-108 contain the fabricated series retraction A7 was written about.

**Why.** A1's actual code was `c_true + 0.15*sin(t/50)` and `c_true + N(0, 0.001)` — an additive term, which is the form the `$` anchor excludes. The gate matches the retraction's description but not the retraction's code. And the directory the repository itself calls "a stale duplicate carrying every original defect" is outside every integrity gate's field of view.

**Fix.** Drop the `$` anchor, add `np\.random\.(randn|rand|uniform|normal)` and `default_rng\(\)\.\w+` to _FABRICATION_PATTERNS, and switch line 143 (and the identical globs at 188 and 937) to `ROOT.rglob("*.py")` with an explicit skip list — or delete kaggle_run/ so the question does not arise.

## 17. [major] kaggle_run/:n/a

**What.** DELETE. Eight tracked files (kaggle_main.py, kan_model.py, pde_adsorption.py, sindy_discovery.py, solver_fd.py, train_pikan.py, kernel-metadata.json, data/synthetic_breakthrough.npz). References that would break or lose meaning: deploy_kaggle.py:8 `kaggle_dir = "kaggle_run"` (delete that file too, see below). References that are DESCRIPTIONS of the directory and survive its deletion as history: 03_LADDER_PROTOCOL.md:1492, RESULTS.md:1151, CONTINUE_HERE.md:239, NEW_SESSION_PROMPT.md:178, and five entries in audit_2026-08-30/literature_review_raw.json (173, 243, 497, 573-574, 2293). No prereg, no CITATION.cff, no requirements.txt and no validate.py gate references it — grep confirms zero hits in PREREG_*.md.

**Why.** AUDIT_2026-08-30 calls it "A LIVE HAZARD... If reviewers or readers get the repository, they get that directory" (literature_review_raw.json:497). It carries the only .npz git actually ships (see the .gitignore finding), and no integrity gate can see inside it because every gate globs non-recursively. Nothing in the live pipeline imports from it.

**Fix.** Delete the directory. Then rewrite the four open-item entries that describe it (03_LADDER_PROTOCOL.md:1492, RESULTS.md:1151, CONTINUE_HERE.md:239, NEW_SESSION_PROMPT.md:178) from an instruction into a closed record — e.g. "removed 2026-09-07; superseded copy of the pipeline as of 2026-08-20, kept in git history at commit <sha>" — so the audit's finding stays traceable and the item stops reading as outstanding. Leave audit_2026-08-30/ untouched: it is a dated external record.

## 18. [major] sindy_discovery.py:n/a

**What.** DELETE the root copy. Referenced by deploy_kaggle.py:42 (`import sindy_discovery`, live import — breaks on deletion), build_kaggle_pkg.py:18 (file manifest — breaks), 03_LADDER_PROTOCOL.md:950 and identify_kinetics.py:5 (both prose references explaining what replaced it). CRITICAL DISTINCTION: identify_kinetics.py:129 defines its OWN `sindy_library()`, writes `sindy_terms`/`sindy_has_q`/`sindy_q_sign` into results/kinetics_identification.json, and is the live estimator that 03_LADDER_PROTOCOL.md:945 says "closes the SINDy open item". It must NOT be deleted or renamed. The two are unrelated code paths sharing a word.

**Why.** Root sindy_discovery.py is the retracted script of A7 ("Returns dq/dt = 0 on the real data, at every threshold tested"). Its `__main__` block at lines 95-117 IS A7's evidence: `node_idx = N_z // 2` is the "sampled at z = 0.5 m where the front had reached 0.235 m" that produced κ(Θ)=1.07e44. Deleting it without preserving that is deleting the exhibit behind a retraction, in a project whose central claim is that the record is complete.

**Fix.** Delete sindy_discovery.py and kaggle_run/sindy_discovery.py, but first append the sampling site to RETRACTIONS.md A7 in words so the evidence survives the file — the `node_idx = N_z // 2` line and the hand-written `dQ_dt_true = 0.05 * q_star - 0.05 * q` at kaggle_run/sindy_discovery.py:105 (A7 already narrates the latter; give it the file:line). Then close open item 6 in RESULTS.md:1154 and 03_LADDER_PROTOCOL.md:1497, which currently reads as an outstanding task ("SINDy needs something to discover") though identify_kinetics.py already answered it.

## 19. [major] deploy_kaggle.py:n/a

**What.** DELETE, together with build_kaggle_pkg.py and kaggle_mof_dynamics_pkg.zip. deploy_kaggle.py:8 points at kaggle_run/, :42 imports sindy_discovery, and :46-53 fabricates the SINDy input (`q = np.random.rand(N, 1) * 10 ... dQ_dt_noisy = (0.05 * q_star - 0.05 * q) + np.random.randn(N, 1) * 0.001`) — the same regression-onto-its-own-basis A7 retracts. build_kaggle_pkg.py:6 names the zip and :18 lists sindy_discovery.py. The zip is gitignored (`git check-ignore -v` → `.gitignore:28:*.zip`) and untracked, so it is a local-only 156 KB artefact. Nothing else in the repository references any of the three.

**Why.** All three are dead deployment scaffolding for a Kaggle path the project no longer uses, and deploy_kaggle.py is a second live copy of A7's fabricated-input defect sitting at the repository root where the non-recursive fabrication gate does look — but does not flag, because the gate only inspects files containing `plt.`.

**Fix.** Delete deploy_kaggle.py, build_kaggle_pkg.py and kaggle_mof_dynamics_pkg.zip. They are self-contained; nothing imports them. This is the whole of the kaggle cluster once kaggle_run/ and sindy_discovery.py go, so the four open-item entries can be closed in the same pass.

## 20. [major] CONTINUE_HERE.md:263

**What.** `- Ledger counts: 26 Part-A, 59 Part-B (B43/B44 figure pass, B45-B53 citation tranche 4, B54-B59 tranche 4b, all 2026-09-05).` The counted values today are 26 Part-A and 64 Part-B. Recounted read-only with ledger_counts.py's own ROW regex: A=26 (contiguous 1..26), B=64 (contiguous 1..64), total 90, 31 entries carrying the literal words "our own error" — identical to results/ledger_counts.json on disk, and no duplicate ids. Every other quotation is currently correct: CONTINUE_HERE.md:165 (26/64/31), README.md:104 (26/64), MANUSCRIPT_OUTLINE.md:41 and :89 (26/64), NEW_SESSION_PROMPT.md:24 (26/64), RESULTS.md:1127 (31 of 90, and it names ledger_counts.py as the source).

**Why.** ledger_counts.py exists (its docstring, lines 4-10) because this number is "quoted in seven documents and maintained in none of them". This is the eighth quotation and it has already drifted by five, in the file the next session is told to read first. B60-B64 landed after it was written and nothing updated it.

**Fix.** Replace the hand-typed figures at CONTINUE_HERE.md:263 with a pointer to results/ledger_counts.json, or delete the line — CONTINUE_HERE.md:165 already carries the correct count sixteen lines earlier in the same document. Longer term, add a gate: read results/ledger_counts.json and grep the six .md files for a `\d+ Part-A` / `\d+ Part-B` pattern that disagrees.

## 21. [major] resume.sh:82-95

**What.** The stall banner is computed from one file only: `cells("results/l4b_v2_results.json", 66)` at line 91, with `want` hardcoded to 66. Nothing else can trigger it. The STATE block above reports eight other incomplete-able artefacts (L3 15 arms, L3 bracket 6, L5 FNO 6, L1-v2 72 cells, LC-v2 135, L2-v2 420, L6-v2, L7-v2) and a stall in any of them produces no warning at all. Worse, the same quantity is counted by two different rules in one script: line 54 `sum(1 for ax in d.get("sweep", {}).values() for a in ax.values() for s in a)` iterates seed KEYS unconditionally, while line 88-89 `sum(1 for axis in d.get("sweep", {}).values() for arm in axis.values() for s in arm.values() if "held" in s)` iterates seed VALUES and requires a "held" key.

**Why.** The comment at lines 67-72 states the purpose exactly — "A stall that looks identical to progress is the problem, so say it loudly, at the top of every state report" — and then implements it for one chain. The twelve-hour loss it describes happened to L4b; the next one will happen to whichever chain is not L4b. And because the two cell counts use different rules, the banner and the state line immediately above it can print contradictory completion figures for the same file.

**Fix.** Extract one `cells_complete(path)` helper and call it from both the STATE loop and the INCOMPLETE test. Then drive the banner from every artefact in the STATE table (any `n < want` with zero matching processes), not from l4b alone.

## 22. [major] resume.sh:79

**What.** `Where-Object { \$_.CommandLine -match 'run_l4b_v2|refine_l4b_v2|run_l6_v2|run_l1_v2|run_l2_v2|run_l5_fno' }` omits refine_sweep_l4b_v2.py, run_l7_v2.py and learning_curve_v2.py, all of which exist and are invoked by the chain scripts. `refine_l4b_v2` does not appear as a substring of `refine_sweep_l4b_v2`, so it does not cover it. Bash processes running the chain_*.sh wrappers are not counted either — only python.exe is queried.

**Why.** RUNNING falls to 0 for a healthy machine that happens to be inside a refinement sweep or the L7 rung, and the banner then declares "A CHAIN IS INCOMPLETE AND NOTHING IS RUNNING" over a job that is working fine. The comment at lines 74-78 records that this check already cried wolf once; the residual false-positive is the same failure with a smaller radius, and it trains the reader to ignore the one alarm the script exists to raise.

**Fix.** Build the pattern from the runner filenames rather than typing it: `'(run|refine|refine_sweep|analyze|learning_curve)_l?[0-9a-z_]*v2|run_l5_fno'`, or simply match `\.py` under this repository's path. Also count the chain shells.

## 23. [minor] resume.sh:125-137

**What.** The completeness test reads `results/l5_fno.json` (line 127) but the job it launches writes elsewhere: `--out results/l5_fno_m16.json` (line 134). Nothing merges the two. results/l5_fno_m16.json does not exist; results/l5_fno.json currently contains all six arms including both modes=16 rows with 3 seeds each, so the branch is dormant today.

**Why.** If the modes=16 arm ever goes missing or a fresh run starts from an incomplete l5_fno.json, `./resume.sh go` launches a three-hour job whose output the test can never see, and re-launches it on every subsequent invocation. A resume script that cannot observe its own work is an infinite loop with a long period.

**Fix.** Either write to `results/l5_fno.json` (the runner already merges arms — that is how the other five got there) or teach the check at 127-129 to consider both files.

## 24. [minor] validate.py:776, 788-790

**What.** `rows, ok = [], []` — `ok` is a LIST in this gate, and the verdict is `if not all(ok): return False, ...` at line 788. `all([])` is True, so an empty list PASSES. If DATASETS were empty, or if `term_coefficients(nd, phys)` returned an empty dict, the gate returns `True, "dominant coefficient = 1 in every equation | " + "; ".join(rows[:3]) + " ..."` — an affirmative claim about zero equations, with an empty evidence string.

**Why.** Vacuous truth reported as verification. This is the same shape as the missing-dataset PASS above but reached through an empty accumulator instead of a caught exception, and it would be much harder to spot because the evidence line still reads like a pass.

**Fix.** Add `if not ok: raise Skip("no equations to check")` before line 788, and consider renaming `ok` to `checks` since it is not a boolean.

## 25. [minor] validate.py:407-408

**What.** `if not np.all(np.isfinite(cs)): continue` — a loading at which the isotherm cannot be inverted is dropped silently, with no row appended and no mark on the verdict. Only if ALL six (2 datasets x 3 loadings) fail does `if not rows: raise Skip("isotherm could not be inverted at any loading")` fire at line 418-419. `_invert_isotherm` returns np.nan whenever `_q_of_c(phys, c_hi, T)[0] < q_target` (lines 327-328), i.e. whenever the target loading is unreachable below c_hi=1e4.

**Why.** The gate's docstring says the identity must hold "at every loading". If the 75 % point becomes unreachable — which is exactly what happens as the isotherm sharpens toward the step this project deliberately models — the gate quietly checks two loadings instead of three and still reports PASS, with an evidence string that lists only what it managed to check. A reader cannot tell a three-of-three pass from a one-of-three pass.

**Fix.** Append a row recording the skipped loading (`f"{kind}@{frac:.0%}: NOT INVERTIBLE below c={c_hi}"`) and set `ok = False`, or at minimum report the number of loadings actually checked in the pass message so the coverage is visible.

## 26. [minor] validate.py:275

**What.** `pend = _json.loads((ROOT / "paper" / "numbers.json").read_text(encoding="utf-8")).get("pending", [])` executes AFTER the pass/fail decision at 267-273, is not guarded, and its result only produces a note appended to the evidence string: `note = f"; {len(pend)} value(s) PENDING a run still in flight"` (line 276). A manuscript containing `\textbf{[PENDING]}` placeholders (paper/numbers.py:45) therefore PASSES this gate.

**Why.** paper/numbers.py:39-40 states the intent: "the build reports how many are pending, so a manuscript can never be finalised while any remain". The build reports it; the gate does not enforce it. Anyone following working rule 1 gets a green manuscript gate over a document with visible [PENDING] markers. Separately, if paper/numbers.json is absent this line raises FileNotFoundError, which the runner turns into a FAIL with a raw traceback rather than the intended SKIP.

**Fix.** Move the numbers.json read up beside the numbers.tex existence check at 255-257 (raising Skip if absent), and make a non-empty `pending` list either a FAIL or a distinct reported state — not a suffix on a pass message.

## 27. [minor] dataset_summary.py:49-52, 102-104

**What.** The non-reconstructible branch returns early with only five keys — `{"root", "design", "n_samples", "n_materials", "damkohler"}` — but main() then prints `out['n_conditions']` (line 103) and `out['n_rejected']` and `out['n_held_out_materials']` (lines 103-104), none of which that dict contains. The graceful-degradation path raises KeyError.

**Why.** The branch exists to report cleanly that Damköhler is unavailable; it crashes instead, on a manifest that lacks per-material k_LDF. Minor because it is reachable only via `--root data/parametric` on a manifest older than the ones present, but it is a fallback that has never been executed.

**Fix.** Use `out.get(...)` in the print block, or have the early return carry the same key set with None values.

## 28. [minor] RESULTS.md:1141-1145, 1154

**What.** Two open items are stale against the ledger. Item 1 — "Every MOF-303 parameter is a literature-range placeholder. Until replaced with cited values and the isotherm refitted to a published water isotherm, **no result may be described as \"MOF-303\"**" — was discharged: RETRACTIONS.md A4 carries a `[PARTIALLY DISCHARGED 2026-08-31 ... **Results may now be described as MOF-303-parameterised**, provided three exclusions are stated]` block, and paper/manuscript.tex:294 and compare_lassitter.py:168 both already say "cited MOF-303". Item 5's speed figure disagrees across documents: RESULTS.md:1145 says "one condition in 4.2 s (MOF-303 config, N_z = 2000)", 03_LADDER_PROTOCOL.md:1495 says "~150 s", and RETRACTIONS.md A6 says "~150 s (2.16 s in the original under-resolved setup)".

**Why.** An open-items list that still forbids what the manuscript already does is worse than no list — the next session either obeys a retracted prohibition or learns to distrust the list. And the speed claim is the one A6 was written about; it now exists in three documents with two different values, none macro-backed, which is the drift ledger_counts.py and paper/numbers.py were both built to end.

**Fix.** Strike RESULTS.md item 1 and replace it with a pointer to A4's discharge and its three stated exclusions (rho_p/eps_t are packing values, C_ps is a 900-2400 J/kg/K band, isotherm_n/henry_fraction are fitted shape parameters). For item 5, resolve 4.2 s vs ~150 s against a timing run, put the survivor in a results file, and reference it as a macro — it is a headline claim about the paper's cost argument.

