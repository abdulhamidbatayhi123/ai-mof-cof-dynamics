# Audit status — which of the 133 findings are closed

Written 2026-09-25 so that no session has to re-derive this. Update a line when you
close a finding. Classification of numbers/prose made by a read-only pass against the
source at that date; citations/hygiene by the session that fixed them.

## audit_citations.md (13)
CLOSED: #1 (generated secondary-source list, `\input{secondary_sources}`), #2 (B65: every
given name gated against fetched provenance; Taraz, Do & Do corrected), #3 (ledger DOI was
the wrong one; 404 recorded), #4, #5, #6 (four weighting refs added; Rathore cited in the
L4 rewrite), #7 ("first" dropped), #8, #9 (NOT_EMITTED in references.py), #10, #11, #12.
OPEN: #13 (Papapicco still REFUSED — needs a direct Crossref fetch of 10.1016/j.cma.2022.114687).

## audit_hygiene.md (28)
CLOSED: #1, #2, #4, #5, #7, #8 (B66), #9 (figure gate triggers on savefig; SOLVER/DIGITISED
provenances), #14 (except ImportError), #17, #18, #19 (kaggle/SINDy removed; A7 evidence kept),
#21/#22 (resume.sh now alarms on a dead autorun QUEUE — the old banner could not see it).
OPEN: #3 (no word-number scanner), #6 (.npz datasets still untracked — decide: track or
document regeneration; gates now SKIP→build refuses, so a clone can no longer build green),
#10, #11, #12, #13, #15, #16, #20, #23, #24, #25, #26, #27, #28.

## audit_numbers.md (23)
CLOSED: 1, 2, 3, 4, 5, 12, 14, 15, 20, 22. PARTIAL: 6 (NEW ERROR: manuscript "At p = 128 it
sits \nONetxFloor× above its own lower bound" but that macro's numerator is the p=8 arm),
11. OPEN: 7 (L5 LR envelope is 2.3 decades, prose says 3.5), 8 (L4 rewrite), 9, 10 (L3: prose
and ABSTRACT say "eight learning rates, three and a half decades"; l3_merged.json grid read by
the audit pass as 7 rates 3e-5..3e-2 — VERIFY), 13, 16, 17, 18, 19, 21, 23.

## audit_prose.md (34)
CLOSED: 1, 3, 4, 5, 6, 7 (Conclusions added 2026-09-25), 8, 10–21, 23, 27, 32.
PARTIAL: 9 (no MDE for L5 or the warp null; L2 MDE keys unused), 22, 31, 34.
OPEN: 2 (L4 rewrite + "Six are eliminated" recount), 24, 25 (fig:dataset, fig:rungs,
fig:mechanism, fig:warp, tab:cost never \ref'd), 26, 28, 29, 30, 33 (\address).

## audit_followup.md, audit_risk.md — not re-classified; see CONTINUE_HERE.md §4.

## Gap not in any audit
No TeX engine is installed on this machine: build_paper.py checks macros, numerals and
citations but nothing compiles the document. Install MiKTeX/TeX Live or tectonic and add
a compile step to the build before submission.
