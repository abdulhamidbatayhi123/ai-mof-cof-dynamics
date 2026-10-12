"""Write the Nature Communications Stage-1 design table as a Word file.

Columns as in the journal's template (nature.com/documents/updated_ncomms-registered-
report-table.docx, read 2026-10-12): Question | Hypotheses | Outcome Measures | Sampling
Plan (N, power analyses) | Analysis Plan | Interpretation given to different outcomes.
The rows restate Table 1 of paper2/stage1.tex, which restates the frozen PREREG_P2
(commit d562f19, as amended by A1); power figures from results/p2_operating_characteristics.json (n = 45). A fresh document is
built here; the publisher's file is not copied.

    python make_stage1_table_docx.py   -> paper2/submission/stage1_design_table.docx
"""
import json
import os

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Cm, Pt

OUT = "paper2/submission/stage1_design_table.docx"
oc = json.load(open("results/p2_operating_characteristics.json", encoding="utf-8"))
b45, cr45, cm45 = oc["h2b"]["45"], oc["h2c_refined_grid"]["45"], oc["h2c_main_grid"]["45"]
det = lambda d: d["moves_by_factor"] + d["detectably_less_than_2"]
b_wrong0 = f"{b45['0.00']['before'] + b45['0.00']['outlives']:.3f}"
b_04, b_05 = f"{b45['0.40']['outlives']:.3f}", f"{b45['0.50']['outlives']:.3f}"
c_ref04, c_main04, c_f2 = f"{det(cr45['0.40']):.3f}", f"{det(cm45['0.40']):.3f}", f"{det(cr45['0.30']):.3f}"
h2a_min = f"{min(max(v.values()) for v in oc['h2a_12_slices']['45'].values()):.3f}"

HEAD = ["Question", "Hypotheses", "Outcome Measures", "Sampling Plan (N, power analyses)",
        "Analysis Plan", "Interpretation given to different outcomes"]
ROWS = [
    ["Is the discovery boundary set by the driving force relative to the combined error?",
     "H2a: P(success) plotted against R = δ/ε_eff collapses onto one curve across Da, Pe, "
     "isotherm shape and observation model (O1, O2); the spread of R* across slices is below "
     "half a decade.",
     "Success of the best method per replicate (exact support, correct signs, coefficient "
     "ratio −1 within 10 %); R* (50 % crossing) per slice.",
     "60 replicates per cell (15 select the best method, 45 estimate); slices are (Pe, "
     "isotherm, observation model), O1 and O2, pooling every σ, ε and Da; cells with R "
     "undefined (σ = ε = 0 on O1) excluded. Thresholds on the spread (0.5 and 1 decade); "
     f"simulated verdict correct with probability ≥ {h2a_min}.",
     "Logistic regression of success on log10 R per slice; R* its 50 % crossing; spread = "
     "max − min of log10 R* with a bootstrap interval; slices without a crossing listed, "
     "never imputed.",
     "Spread < 0.5 decade: “R collapses the boundary”. Spread ≥ 1 decade: “R does not "
     "collapse the boundary; the boundary depends additionally on {named axis}”. Between: "
     "“inconclusive: R narrows the boundary to a spread of {x} decades”."],
    ["Does discovery fail before, with or after the rate constant stops being identifiable?",
     "H2b: compare Da*_disc (best discovery method) with Da*_ident (profile likelihood, true "
     "law known); confirmatory on O1, descriptive on O2 and O3.",
     "Gap log10 Da*_disc − log10 Da*_ident per O1 slice (σ, ε, isotherm); the "
     "hypothesis-level verdict by the two-thirds rule.",
     "9 Da levels × 45 estimation replicates for both boundaries (15 more select the method). "
     f"Smallest effect of interest 0.40 decade. Simulated: wrong verdict {b_wrong0} at no gap; "
     f"correct verdict {b_04} at 0.40 decade and {b_05} at 0.50.",
     "Same logistic estimator for both boundaries, on the estimation set; percentile "
     "bootstrap (2000 resamples) within Da levels. Sensitivity: success also requiring "
     "k̂ in [k/2, 2k]. O2 and O3 (3 replicates) descriptive.",
     "Gap ≤ −0.25: “discovery fails before identifiability”. |gap| < 0.25: “discovery fails "
     "with identifiability”. Gap ≥ +0.25: “discovery outlives identifiability”. No crossing: "
     "no verdict. Overall: the word of at least two thirds of the slices, else “mixed”."],
    ["Does an errors-in-variables fit move the boundary when the isotherm is wrong?",
     "H2c: M5 (EIV best-subset) shifts Da*_disc upwards against the best strong-form "
     "non-EIV method at ε > 0, on O1; predicted size a factor 2.",
     "Shift in log10 Da*_disc, M5 minus the best strong-form non-EIV method, per (isotherm, "
     "ε > 0) at σ = 2 %.",
     "45 estimation replicates; for ε = 2 % the 9 levels plus 8 refined levels inside "
     "±0.5 decade of the best non-EIV boundary. Simulated: no false detection; detection "
     f"{c_ref04} (refined) and {c_main04} (main grid) at 0.40 decade; {c_f2} at the "
     "predicted factor 2.",
     "Same estimator and bootstrap, on the estimation set; the non-EIV method chosen on the "
     "selection set; the shift against the best non-EIV method over both forms reported "
     "descriptively.",
     "Holds where the upward shift is ≥ 0.25. Graded: ≥ log10 2 (0.30): “EIV moves the "
     "boundary by {factor}”; 0.25 to log10 2: “EIV moves the boundary by {factor}, "
     "detectably but by less than the predicted factor 2”. Below 0.25 at every ε > 0: “EIV "
     "does not move the boundary detectably (MDE {x})”. Down by at least 0.25: “EIV moves the "
     "boundary DOWN by {factor}”."],
    ["Can a loading-dependent rate at a MOF-like isotherm step be discovered?",
     "H2d (exploratory): no directional prediction.",
     "Discovery of k(q) per cell: support contains q*_meas and q; Spearman ρ < −0.8 across 10 "
     "bins; top-bin rate ≤ 0.6 of bottom-bin rate.",
     "Step isotherm, true law L2, 60 replicates per cell. No power analysis (exploratory).",
     "Rate of discovery per (σ, observation) cell.",
     "Reported as rates; no confirmatory claim rests on H2d."],
]

doc = Document()
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(1.5))
doc.add_paragraph().add_run(
    "Study design table: When can AI discover adsorption kinetics? A discoverability map "
    "(Registered Report, Stage 1). Every entry restates the frozen pre-registration "
    "(PREREG_P2, commit d562f19, as amended by A1).").bold = True
t = doc.add_table(rows=1 + len(ROWS), cols=len(HEAD))
t.style = "Table Grid"
for j, h in enumerate(HEAD):
    t.cell(0, j).text = h
    t.cell(0, j).paragraphs[0].runs[0].bold = True
for i, row in enumerate(ROWS, start=1):
    for j, txt in enumerate(row):
        t.cell(i, j).text = txt
for row in t.rows:
    for cell in row.cells:
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(8)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
print("wrote", OUT)
