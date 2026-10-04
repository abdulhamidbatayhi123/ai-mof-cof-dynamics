"""Every number the manuscript quotes, resolved from a results file. Nothing typed.

B21 and B43 are the same defect: a number reached a document with no script behind
it. B43 was the expensive one — three of L2-v2's four quoted comparisons, including
the 21.3 % that retraction A26 rests on, existed in no results file and no log. They
were correct, but nobody could have known that without recomputing them by hand.

This module makes that defect structurally impossible for the manuscript. Every
quoted quantity is declared here as

    (key, file, dotted path into that file, formatter)

and resolved at build time. A key whose file is missing, whose path does not exist,
or whose value is not finite is a **hard failure**, never a silent blank — a gate that
can be bypassed is not a gate (B37). The renderer then refuses to emit a manuscript
containing an unresolved placeholder, and `validate.py` refuses to pass a manuscript
containing a bare numeral outside a declared exemption.

    python paper/numbers.py              # resolve, report, write numbers.{tex,json}
    python paper/numbers.py --list       # every key and where it comes from
    python paper/numbers.py --check      # resolve only; non-zero exit if anything fails

Adding a number to the manuscript means adding a row here first. That is the point.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_TEX = os.path.join(ROOT, "paper", "numbers.tex")
OUT_JSON = os.path.join(ROOT, "paper", "numbers.json")

# Results files that a run still in flight has not written. A key sourced from one of
# these resolves to the placeholder text below instead of failing — and the build
# reports how many are pending, so a manuscript can never be finalised while any
# remain. Remove an entry the moment its run lands; a PENDING file that EXISTS is a
# hard failure, exactly as in validate.py's figure gate.
PENDING = {}          # L4b-v2 landed 2026-09-08; nothing is in flight
PENDING_TEXT = r"\textbf{[PENDING]}"

# Keys whose results file EXISTS but whose value is not yet final, because a
# pre-registered step that can change it has not finished. Each is gated on a
# completion marker in a log; until the marker appears the key renders PENDING and is
# counted as pending. Added 2026-09-28: the material-axis L4b verdict read "PHYSICS
# HELPS" from the analyser while PREREG §4.2 still required another decade (w1e-6),
# and the Conclusions interpolated it -- a provisional verdict one build from the PDF.
GATED = {
    "LthreeBestKanSig": ("l3_final_pair.log", "L3_FINAL_PAIR_DONE",
                         "B71: re-derivation of the paired interval (autorun job 2c)"),
    "LthreeBestKanLo": ("l3_final_pair.log", "L3_FINAL_PAIR_DONE",
                        "B71: re-derivation of the paired interval (autorun job 2c)"),
    "LthreeBestKanHi": ("l3_final_pair.log", "L3_FINAL_PAIR_DONE",
                        "B71: re-derivation of the paired interval (autorun job 2c)"),
    "LfourbVerdictMaterial": ("chain_l4b_v2_ext2_outer.log", "L4B_V2_EXT2_DONE",
                              "second PREREG 4.2 edge extension (w1e-6, material axis)"),
}


# LaTeX specials that are a HARD ERROR in text mode, and the escapes for them.
# Every macro VALUE goes through this. The build gate already refused an undefined
# macro, a mangled macro and a bare numeral, but it never looked at what a macro
# EXPANDED TO -- so the macro nLtwoBestFam, resolving to the literal string
# "mlp_depth", passed every check and produced a manuscript that cannot compile
# ("Missing $ inserted"). Three of the four L4b verdict branches interpolate an arm name and
# every arm name carries an underscore, so the document built only because the
# branch that happened to fire was the one string with no arm name in it.
_TEX_ESCAPES = {"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#"}
_TEX_FORBIDDEN = "$^~"


def tex_safe(key, value):
    """Escape what can be escaped; refuse what cannot."""
    v = str(value)
    if "\\" in v:
        # a value that already contains a control sequence is either deliberate
        # (PENDING_TEXT) or a sign that a results file is carrying LaTeX, which is
        # not something a results file should ever do.
        if v.strip().startswith(r"\textbf{") or v.strip().startswith(r"\emph{"):
            return v
        raise ValueError(f"{key}: value contains a backslash and is not a known "
                         f"markup wrapper: {v!r}")
    bad = [c for c in _TEX_FORBIDDEN if c in v]
    if bad:
        raise ValueError(f"{key}: value contains LaTeX-special {bad} that cannot be "
                         f"escaped automatically: {v!r}. Fix it at the source.")
    for ch, esc in _TEX_ESCAPES.items():
        v = v.replace(ch, esc)
    return v


def pct(x):
    return f"{100 * x:.1f}"


def pct_sig(x, n=2):
    """A percentage to `n` significant figures, not to one decimal place.

    `pct` destroyed exactly the numbers the paper most needs. The solver
    verification table quotes a retarded-front error of 0.0272 %, a thermal-wave
    error of 0.0123 % and a mass closure of 0.0497 %, and one decimal place prints
    all three as "0.0 %" -- which reads either as a broken macro or as an
    implausible claim of exact agreement, in the one table the rest of the paper
    rests on. Three significant digits of a verification error are the evidence;
    rounding them away is not a formatting choice.
    """
    v = 100.0 * x
    if v == 0:
        return "0"
    d = max(0, n - 1 - int(math.floor(math.log10(abs(v)))))
    return f"{v:.{d}f}"


def sig(x, n=3):
    if x == 0:
        return "0"
    d = max(0, n - 1 - int(math.floor(math.log10(abs(x)))))
    return f"{x:.{d}f}"


# key -> (file, dotted path, formatter). The dotted path may index lists with [i].
SPEC = [
    # ---------------------------------------------------------------- L0
    ("LzeroTracer", "verify_solver.json", "tracer_van_genuchten.max_abs_err_vs_third_type", "{:.2e}"),
    ("LzeroTracerFront", "verify_solver.json", "tracer_van_genuchten.front_rel_err", pct_sig),
    ("LzeroTracerPe", "verify_solver.json", "tracer_van_genuchten.Pe", "{:.0f}"),
    ("LzeroBCdiff", "verify_solver.json", "tracer_van_genuchten.bc_difference_max", pct),
    ("LzeroRetarded", "verify_solver.json", "retarded_front.rel_err", pct_sig),
    ("LzeroRetardedR", "verify_solver.json", "retarded_front.R", "{:.0f}"),
    ("LzeroThermal", "verify_solver.json", "thermal_wave.rel_err", pct_sig),
    ("LzeroLDF", "verify_solver.json", "ldf_anzelius_schumann.max_abs_err", "{:.1e}"),

    # ------------------------------------------------- the isotherm, whole space
    ("IsoNmat", "results/isotherm_space.json", "n_materials", "{:d}"),
    ("IsoKHmin", "results/isotherm_space.json", "K_H.min", sig),
    ("IsoKHmed", "results/isotherm_space.json", "K_H.median", sig),
    ("IsoKHmax", "results/isotherm_space.json", "K_H.max", sig),
    ("IsoKHdec", "results/isotherm_space.json", "K_H.decades", "{:.1f}"),
    ("IsoHenryMed", "results/isotherm_space.json", "log10_c_henry_over_c_in_median.median", "{:.1f}"),
    ("IsoHenryMax", "results/isotherm_space.json", "log10_c_henry_over_c_in_median.max", "{:.1f}"),
    ("IsoHenryBelowMilli", "results/isotherm_space.json", "n_henry_region_below_1e3_of_feed", "{:d}"),
    ("IsoHenryBelowMicro", "results/isotherm_space.json", "n_henry_region_below_1e6_of_feed", "{:d}"),

    # ------------------------------------------------------------ calibration
    ("AlphaFolds", "results/calibration_v2.json", "v2_5fold.alpha", "{:g}"),
    ("NclustFolds", "results/calibration_v2.json", "v2_5fold.n_clusters", "{:d}"),
    ("FprFoldsNominal", "results/calibration_v2.json", "v2_5fold.fpr_by_alpha.0.05", "{:.1f}"),
    ("FprFoldsCal", "results/calibration_v2.json", "v2_5fold.fpr_by_alpha.0.02", "{:.1f}"),
    ("AlphaManifest", "results/calibration_v2.json", "v2.alpha", "{:g}"),
    ("NclustManifest", "results/calibration_v2.json", "v2.n_clusters", "{:d}"),
    ("FprLegacyNominal", "results/calibration_v2.json", "legacy.fpr_by_alpha.0.05", "{:.1f}"),
    ("NclustLegacy", "results/calibration_v2.json", "legacy.n_clusters", "{:d}"),

    # ------------------------------------------------------------- L1 on v2
    ("LoneMLP", "results/l1_v2_verdict.json", "folds.table.mlp.c", "{:.4f}"),
    ("LoneXGB", "results/l1_v2_verdict.json", "folds.table.xgb.c", "{:.4f}"),
    ("LoneRF", "results/l1_v2_verdict.json", "folds.table.rf.c", "{:.4f}"),
    ("LoneRidge", "results/l1_v2_verdict.json", "folds.table.ridge.c", "{:.4f}"),
    ("LonePodFloor", "results/l1_v2_verdict.json", "folds.pod_floor_pooled.c", "{:.2e}"),
    ("LoneMLPvsXGBdiff", "results/l1_v2_verdict.json", "folds.comparisons.xgb.mean_diff", "{:.5f}"),
    ("LoneMLPvsXGBlo", "results/l1_v2_verdict.json", "folds.comparisons.xgb.ci_low", "{:.5f}"),
    ("LoneMLPvsXGBhi", "results/l1_v2_verdict.json", "folds.comparisons.xgb.ci_high", "{:.5f}"),

    # ------------------------------------------------- the materials learning curve
    ("LCbeta", "results/learning_curve_v2_verdict.json", "axes.materials.beta", "{:.3f}"),
    ("LCbetaLo", "results/learning_curve_v2_verdict.json", "axes.materials.beta_ci[0]", "{:.3f}"),
    ("LCbetaHi", "results/learning_curve_v2_verdict.json", "axes.materials.beta_ci[1]", "{:.3f}"),
    ("LCsmallest", "results/learning_curve_v2_verdict.json", "axes.materials.rows[0].refit", "{:.4f}"),
    ("LClargest", "results/learning_curve_v2_verdict.json", "axes.materials.rows[4].refit", "{:.4f}"),
    ("LClargestFixed", "results/learning_curve_v2_verdict.json", "axes.materials.rows[4].fixed", "{:.4f}"),
    ("LCsmallestFixed", "results/learning_curve_v2_verdict.json", "axes.materials.rows[0].fixed", "{:.4f}"),
    ("LCratio", "results/learning_curve_v2_verdict.json", "axes.materials.ratio_first_to_last", "{:.2f}"),
    ("LClastDiff", "results/learning_curve_v2_verdict.json", "axes.materials.steps[3].mean_diff", "{:.5f}"),
    ("LClastLo", "results/learning_curve_v2_verdict.json", "axes.materials.steps[3].ci_low", "{:.5f}"),
    ("LClastHi", "results/learning_curve_v2_verdict.json", "axes.materials.steps[3].ci_high", "{:.5f}"),
    ("LCmodesSmall", "results/learning_curve_v2_verdict.json", "axes.materials.rows[0].modes_r2_gt_0.2", "{:d}"),
    ("LCmodesLarge", "results/learning_curve_v2_verdict.json", "axes.materials.rows[4].modes_r2_gt_0.2", "{:d}"),
    ("LCcondBeta", "results/learning_curve_v2_verdict.json", "axes.conditions.beta", "{:.3f}"),

    # ------------------------------------------------------------- L2 on v2
    ("LtwoBest", "results/l2_v2_verdict.json", "best_overall[0]", "{:.4f}"),
    ("LtwoBestFam", "results/l2_v2_verdict.json", "best_overall[1]", "{}"),
    ("LtwoBestCfg", "results/l2_v2_verdict.json", "best_overall[2]", "{}"),
    ("LtwoPodFloor", "results/l2_v2_verdict.json", "pod_floor_mean", "{:.2e}"),
    ("LtwoDepthShape", "results/l2_v2_verdict.json", "families.mlp_depth.shape", "{}"),
    ("LtwoWidthShape", "results/l2_v2_verdict.json", "families.mlp_width.shape", "{}"),
    # the optimum as a plain number (the shape strings render as "U-SHAPED, optimum at w64")
    ("LtwoWidthBest", "results/l2_v2_verdict.json", "families.mlp_width.best", lambda b: b.lstrip("w")),
    # A27: the random forest is still improving at its capacity ceiling (leaf 1)
    ("LtwoRfBest", "results/l2_v2_verdict.json", "families.rf_leaf.last_step.mean_a", "{:.4f}"),
    ("LtwoRfLastLo", "results/l2_v2_verdict.json", "families.rf_leaf.last_step.ci_low", "{:.4f}"),
    ("LtwoRfLastHi", "results/l2_v2_verdict.json", "families.rf_leaf.last_step.ci_high", "{:.4f}"),
    ("LtwoDepthBest", "results/l2_v2_verdict.json", "families.mlp_depth.best", lambda b: b.lstrip("d")),
    ("LtwoXgbBest", "results/l2_v2_verdict.json", "families.xgb_depth.best", lambda b: b.lstrip("md")),
    ("LtwoXgbShape", "results/l2_v2_verdict.json", "families.xgb_depth.shape", "{}"),
    ("LtwoRfShape", "results/l2_v2_verdict.json", "families.rf_leaf.shape", "{}"),
    ("LtwoDepthMDE", "results/l2_v2_verdict.json", "families.mlp_depth.mde_last_step.mde_80", pct),
    ("LtwoXgbMDE", "results/l2_v2_verdict.json", "families.xgb_depth.mde_last_step.mde_80", pct),

    # ------------------------------------------------------------- L3 (legacy)
    ("LthreeMlpSmall", "results/l3_merged.json", "table.50000_mlp.novel", "{:.4f}"),
    ("LthreeMlpLarge", "results/l3_merged.json", "table.800000_mlp.novel", "{:.4f}"),
    ("LthreeRbfLarge", "results/l3_merged.json", "table.800000_rbf_kan.novel", "{:.4f}"),
    ("LthreeChebyLarge", "results/l3_merged.json", "table.800000_cheby_kan.novel", "{:.4f}"),
    ("LthreeMlpLr", "results/l3_merged.json", "table.800000_mlp.lr", "{:g}"),
    ("LthreeChebyLr", "results/l3_merged.json", "table.50000_cheby_kan.lr", "{:g}"),
    ("LthreeArms", "results/l3_merged.json", "n_arms", "{:d}"),
    ("LthreeNfailAll", "results/l3_merged.json", "failed_all_seeds", lambda x: str(len(x))),
    ("LthreeNfailSome", "results/l3_merged.json", "failed_some_seeds", lambda x: str(len(x))),
    # l3_edges.py: the grid as actually run across three files, and how far the
    # perceptron's bottom-edge selection is from saturated (rule 4 needs it measured).
    ("LthreeNrates", "results/l3_edges.json", "n_rates", "{:d}"),
    ("LthreeDecades", "results/l3_edges.json", "decades", "{:.1f}"),
    ("LthreeEdgeSatMin", "results/l3_edges.json", "edge_saturation_min", lambda x: f"{100 * x:.2f}"),
    ("LthreeEdgeSatMax", "results/l3_edges.json", "edge_saturation_max", lambda x: f"{100 * x:.2f}"),
    # B71: the means are owned by audit_l3.py (identical values); the paired interval
    # below is GATED until l3_final_pair.py (autorun job 2c) re-derives it.
    ("LthreeBestKanMlp", "results/l3_audit.json", "mlp", "{:.4f}"),
    ("LthreeBestKan", "results/l3_audit.json", "rbf_g4", "{:.4f}"),
    ("LthreeBestKanSig", "results/l3_final_pair.json", "significant",
     lambda b: "significant" if b else "not significant"),
    ("LthreeBestKanLo", "results/l3_final_pair.json", "ci[0]", "{:.4f}"),
    ("LthreeBestKanHi", "results/l3_final_pair.json", "ci[1]", "{:.4f}"),

    # ------------------------------------------------------------- L5 (legacy)
    ("LfiveFNO", "results/l5_fno_verdict.json", "fno_best.mean", "{:.4f}"),
    ("LfiveFNOmodes", "results/l5_fno_verdict.json", "fno_best.modes", "{:d}"),
    ("LfiveFNOwidth", "results/l5_fno_verdict.json", "fno_best.width", "{:d}"),
    # the best DeepONet's width, which the prose used to type as a bare "216" and
    # build_paper.py used to launder through ALLOWED as "an architecture
    # description". It is the selected cell of a sweep, i.e. a result.
    ("LfiveONetWidth", "results/l5_fno_verdict.json", "deeponet_best_width", "{:d}"),
    ("LfiveONetP", "results/l5_fno_verdict.json", "deeponet_best_p", "{:d}"),
    # l5_oracle_rank.py: what each method's error is worth in oracle modes, and the
    # per-mode R^2 bands. RESULTS.md carried the oracle-rank table with no script
    # and "median R^2 < 0 beyond mode 24" -- true, but 24 was arbitrary: the median
    # of the remaining modes is negative from mode 1. The cut is now after the
    # leading predictable run.
    ("LfiveOracleONet", "results/l5_oracle_rank.json", "ranks.deeponet_best.oracle_rank", "{:d}"),
    ("LfiveOracleFNO", "results/l5_oracle_rank.json", "ranks.fno_best.oracle_rank", "{:d}"),
    ("LfiveLeadModes", "results/l5_oracle_rank.json", "mode_r2_p128.leading_predictable_run", "{:d}"),
    ("LfiveTailModes", "results/l5_oracle_rank.json", "mode_r2_p128.n_tail_modes", "{:d}"),
    ("LfiveTailMedian", "results/l5_oracle_rank.json", "mode_r2_p128.median_r2_tail", "{:.3f}"),
    ("LfiveTailFracNeg", "results/l5_oracle_rank.json", "mode_r2_p128.frac_tail_below_zero",
     lambda x: f"{100 * x:.0f}"),
    # L5's learning-rate envelope for DeepONet, as run. The prose said "three and a
    # half decades" -- L3's envelope; L5's was 2.3 (audit_numbers #7).
    ("LfiveNrates", "results/l5_merged.json", "selected.deeponet_p8.n_lr_tried", "{:d}"),
    ("LfiveDecades", "results/l5_merged.json", "selected.deeponet_p8.grid",
     lambda g: f"{__import__('math').log10(max(g) / min(g)):.1f}"),
    ("LfiveONetEdgeMove", "results/l5_merged.json", "selected.deeponet_p16.edge_sensitivity",
     lambda x: f"{100 * x:.1f}"),
    ("LfiveWidthRatio", "results/l5_fno_verdict.json", "width_ratio_onet_over_fno", "{:.1f}"),
    ("LfiveNclust", "results/l5_fno_verdict.json", "_n_clusters", "{:d}"),
    ("LfiveAlpha", "results/l5_fno_verdict.json", "_alpha", "{:g}"),
    ("LfiveONet", "results/l5_fno_verdict.json", "deeponet_best", "{:.4f}"),
    ("LfiveOKAN", "results/l5_fno_verdict.json", "deepokan_best", "{:.4f}"),
    ("LfiveFloor", "results/l5_fno_verdict.json", "pod_floor_p128", "{:.2e}"),
    ("LfiveONetFNOdiff", "results/l5_fno_verdict.json", "deeponet_vs_fno.mean_diff", "{:.5f}"),
    ("LfiveONetFNOlo", "results/l5_fno_verdict.json", "deeponet_vs_fno.ci_low", "{:.5f}"),
    ("LfiveONetFNOhi", "results/l5_fno_verdict.json", "deeponet_vs_fno.ci_high", "{:.5f}"),
    ("LfiveFlatDiff", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.mean_diff", "{:.5f}"),
    ("LfiveFlatLo", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.ci_low", "{:.5f}"),
    ("LfiveFlatHi", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.ci_high", "{:.5f}"),
    ("LfiveFlatBase", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.mean_a", "{:.5f}"),
    # the legacy 12-cluster design's own 80 %-power MDE, as a RELATIVE effect.
    # calibrate_v2.py's own printout reads "a 'no difference' verdict on this split
    # excludes improvements larger than ~50 %". That is the weakest design in the
    # paper and the number appeared nowhere in it.
    ("LegacyMDE", "results/calibration_v2.json", "legacy.mde_at_80pct", pct),
    # calibrate_v2 SELECTED alpha = 0.01 for the 12-cluster design, but
    # metrics.ALPHA_CALIBRATED -- the default every legacy-design rung actually ran
    # at -- is 0.005, which is stricter. Declare the level that was USED and its
    # measured size, and the selected one alongside, rather than implying they are
    # the same number.
    ("AlphaLegacySel", "results/calibration_v2.json", "legacy.alpha", "{:g}"),
    ("FprLegacyUsed", "results/calibration_v2.json", "legacy.fpr_by_alpha.0.005", "{:.2f}"),
    ("LfiveFloorSmall", "results/l5_merged.json", "pod_floor.8", "{:.2e}"),
    ("LfiveFloorLarge", "results/l5_merged.json", "pod_floor.128", "{:.2e}"),
    ("LfiveBasisSmall", "results/l5_bottleneck.json", "rows[0].basis_floor_novel", "{:.5f}"),
    ("LfiveBasisLarge", "results/l5_bottleneck.json", "rows[4].basis_floor_novel", "{:.5f}"),
    ("LfiveCoefSmall", "results/l5_bottleneck.json", "rows[0].coef_pred_novel", "{:.4f}"),
    ("LfiveCoefLarge", "results/l5_bottleneck.json", "rows[4].coef_pred_novel", "{:.4f}"),

    # ------------------------------------------------------------- L6 on v2
    ("LsixJoint", "results/l6_v2_verdict.json", "pooled.mean_a", "{:.4f}"),
    ("LsixSeparate", "results/l6_v2_verdict.json", "pooled.mean_b", "{:.4f}"),
    ("LsixDiff", "results/l6_v2_verdict.json", "pooled.mean_diff", "{:.5f}"),
    ("LsixLo", "results/l6_v2_verdict.json", "pooled.ci_low", "{:.5f}"),
    ("LsixHi", "results/l6_v2_verdict.json", "pooled.ci_high", "{:.5f}"),
    ("LsixSlope", "results/l6_v2_verdict.json", "slope_test.slope", "{:.5f}"),
    ("LsixSlopeLo", "results/l6_v2_verdict.json", "slope_test.ci_low", "{:.5f}"),
    ("LsixSlopeHi", "results/l6_v2_verdict.json", "slope_test.ci_high", "{:.5f}"),
    ("LsixSlopeR", "results/l6_v2_verdict.json", "slope_test.pearson_r", "{:.3f}"),
    ("LsixBetweenSD", "results/l6_v2_verdict.json", "between_material_sd", "{:.4f}"),
    ("LsixMDE", "results/l6_v2_mde_corrected.json", "mde_80", pct),
    ("LsixPowerFour", "results/l6_v2_mde_corrected.json", "power.0.04", "{:.0f}"),
    ("LsixPowerTwo", "results/l6_v2_mde_corrected.json", "power.0.02", "{:.0f}"),
    ("LsixSizeNull", "results/l6_v2_mde_corrected.json", "size_at_null", "{:.1f}"),
    ("LsixBetweenOverBase", "results/l6_v2_mde_corrected.json", "between_over_base", pct),
    ("LsixDaMin", "results/l6_v2_checks.json", "da.min", "{:.1f}"),
    ("LsixDaMax", "results/l6_v2_checks.json", "da.max", "{:.0f}"),
    ("LsixDaMedian", "results/l6_v2_checks.json", "da.median", "{:.1f}"),
    ("LsixDaDecades", "results/l6_v2_checks.json", "da.decades", "{:.2f}"),
    ("LsixKineticRtwo", "results/l6_v2_checks.json", "descriptor_r2.d_p", "{:.3f}"),
    ("LsixStepRtwo", "results/l6_v2_checks.json", "descriptor_r2.step_rh", "{:.2f}"),
    ("LsixQmaxRtwo", "results/l6_v2_checks.json", "descriptor_r2.q_max", "{:.2f}"),

    # ------------------------------------------------------------- L7 on v2
    ("LsevenLearned", "results/l7_v2_verdict.json", "comparisons.mlp vs klinkenberg.mean_a", "{:.4f}"),
    ("LsevenKlinkenberg", "results/l7_v2_verdict.json", "comparisons.mlp vs klinkenberg.mean_b", "{:.4f}"),
    ("LsevenShock", "results/l7_v2_verdict.json", "comparisons.mlp vs equilibrium_shock.mean_b", "{:.4f}"),
    ("LsevenPattern", "results/l7_v2_verdict.json", "comparisons.mlp vs constant_pattern.mean_b", "{:.4f}"),
    ("LsevenDiff", "results/l7_v2_verdict.json", "comparisons.mlp vs klinkenberg.mean_diff", "{:.4f}"),
    ("LsevenLo", "results/l7_v2_verdict.json", "comparisons.mlp vs klinkenberg.ci_low", "{:.4f}"),
    ("LsevenHi", "results/l7_v2_verdict.json", "comparisons.mlp vs klinkenberg.ci_high", "{:.4f}"),
    ("LsevenRatio", "results/l7_v2_verdict.json", "best_classical_over_learned", "{:.2f}"),

    # -------------------------------------------------------- the coordinate change
    ("WarpFixed", "results/warp_verdict.json", "means.fixed", "{:.5f}"),
    ("WarpPredicted", "results/warp_verdict.json", "means.two_wave", "{:.5f}"),
    ("WarpOracle", "results/warp_verdict.json", "means.two_wave_oracle", "{:.5f}"),
    ("WarpPredDiff", "results/warp_verdict.json", "fixed_vs_two_wave.mean_diff", "{:.5f}"),
    ("WarpPredLo", "results/warp_verdict.json", "fixed_vs_two_wave.ci_low", "{:.5f}"),
    ("WarpPredHi", "results/warp_verdict.json", "fixed_vs_two_wave.ci_high", "{:.5f}"),
    ("WarpOracleDiff", "results/warp_verdict.json", "fixed_vs_oracle.mean_diff", "{:.5f}"),
    ("WarpOracleLo", "results/warp_verdict.json", "fixed_vs_oracle.ci_low", "{:.5f}"),
    ("WarpOracleHi", "results/warp_verdict.json", "fixed_vs_oracle.ci_high", "{:.5f}"),
    ("WarpHeadroom", "results/warp_verdict.json", "headroom_to_oracle", "{:.2f}"),
    ("NwidthOriginal", "results/comoving2.json", "spectrum_original.0.999", "{:d}"),
    ("NwidthSingle", "results/comoving.json", "levels_detail.0.5.spectrum.0.999", "{:d}"),
    ("NwidthTwoWaveA", "results/comoving2.json", "pairs_detail.0.10-0.90.spectrum.0.999", "{:d}"),
    ("NwidthTwoWaveB", "results/comoving2.json", "pairs_detail.0.05-0.95.spectrum.0.999", "{:d}"),
    ("GapMin", "results/comoving.json", "two_wave_gap.min", "{:.3f}"),
    ("GapMax", "results/comoving.json", "two_wave_gap.max", "{:.3f}"),
    ("MonoRawNrmse", "results/warp_monotone.json", "comparison.mean_a", "{:.5f}"),
    ("MonoProjNrmse", "results/warp_monotone.json", "comparison.mean_b", "{:.5f}"),
    ("MonoDiff", "results/warp_monotone.json", "comparison.mean_diff", "{:.5f}"),
    ("MonoLo", "results/warp_monotone.json", "comparison.ci_low", "{:.5f}"),
    ("MonoHi", "results/warp_monotone.json", "comparison.ci_high", "{:.5f}"),

    # ----------------------------------------------------------- the n-width
    ("NwidthExpC", "results/nwidth.json", "c.algebraic_exponent", "{:.2f}"),
    ("NwidthRtwoC", "results/nwidth.json", "c.algebraic_r2", "{:.4f}"),

    # ------------------------------------------------ the experimental anchor
    ("AnchorTfiftyExp", "results/lassitter_comparison.json", "experiment.t50_min", "{:.0f}"),
    ("AnchorTfiftyModel", "results/lassitter_comparison.json", "runs.k0.2_dp3mm_isothermal.t50_min", "{:.0f}"),
    ("AnchorPlateauExp", "results/lassitter_comparison.json", "experiment.plateau_150_250_frac", "{:.3f}"),
    ("AnchorPlateauModel", "results/lassitter_comparison.json", "runs.k0.2_dp3mm_isothermal.plateau_150_250_frac", "{:.3f}"),
    ("AnchorTfiveExp", "results/lassitter_comparison.json", "experiment.t05_min", "{:.0f}"),
    ("AnchorTfiveModel", "results/lassitter_comparison.json", "runs.k0.2_dp3mm_isothermal.t05_min", "{:.1f}"),
    ("AnchorNrmse", "results/lassitter_comparison.json", "runs.k0.2_dp3mm_isothermal.nrmse_vs_effluent", "{:.3f}"),

    # ------------------------ B53: the dispersion closure against the correlation it
    # truncates.  dispersion_check.py measures where in particle Peclet this study
    # actually sits; the anchor rows below are a LABELLED POST-HOC re-solve of the
    # anchor under the untruncated form, from compare_lassitter_posthoc.json.
    ("PePartMin", "results/dispersion_check.json", "pe_particle_interstitial.min", "{:.1f}"),
    ("PePartMed", "results/dispersion_check.json", "pe_particle_interstitial.median", "{:.0f}"),
    ("PePartMax", "results/dispersion_check.json", "pe_particle_interstitial.max", "{:.0f}"),
    ("PePartDecades", "results/dispersion_check.json", "pe_particle_interstitial.decades", "{:.2f}"),
    ("DispRatioMed", "results/dispersion_check.json", "dl_ratio_ours_over_er.median", "{:.2f}"),
    ("DispRatioMax", "results/dispersion_check.json", "dl_ratio_ours_over_er.max", "{:.2f}"),
    ("DispFracAboveTenPct", "results/dispersion_check.json", "frac_ratio_above_1p10", pct),
    ("DispFracAboveHalf", "results/dispersion_check.json", "frac_ratio_above_1p50", pct),
    ("DispWorstPe", "results/dispersion_check.json", "disagreement_peak.pe", "{:.1f}"),
    ("DispWorstRatio", "results/dispersion_check.json", "disagreement_peak.ratio", "{:.2f}"),
    ("AnchorPePart", "results/dispersion_check.json", "anchor.cases.dp3mm_primary.pe_particle", "{:.1f}"),
    ("AnchorDispRatio", "results/dispersion_check.json", "anchor.cases.dp3mm_primary.ratio_ours_over_er", "{:.2f}"),
    ("AnchorPeCol", "results/dispersion_check.json",
     "anchor.cases.dp3mm_primary.pe_column_ours_superficial", "{:.2f}"),
    ("AnchorPeColER", "results/dispersion_check.json",
     "anchor.cases.dp3mm_primary.pe_column_er_superficial", "{:.2f}"),

    # the labelled post-hoc re-solve of the anchor (compare_lassitter_posthoc.py)
    ("AnchorTninetyfiveExp", "results/lassitter_comparison.json", "experiment.t95_min", "{:.0f}"),
    ("AnchorTninetyfiveModel", "results/lassitter_comparison_posthoc.json",
     "runs.wakao_dp3mm_k0.2 (primary, for reference).t95_min", "{:.0f}"),
    ("AnchorTninetyfiveER", "results/lassitter_comparison_posthoc.json",
     "runs.edwards_richardson_k0.2.t95_min", "{:.0f}"),
    ("AnchorTninetyfiveBrug", "results/lassitter_comparison_posthoc.json",
     "runs.bruggeman_k0.2.t95_min", "{:.0f}"),
    ("AnchorNrmseER", "results/lassitter_comparison_posthoc.json",
     "runs.edwards_richardson_k0.2.nrmse_vs_effluent", "{:.3f}"),
    ("AnchorNrmseBrug", "results/lassitter_comparison_posthoc.json",
     "runs.bruggeman_k0.2.nrmse_vs_effluent", "{:.3f}"),
    ("AnchorPlateauER", "results/lassitter_comparison_posthoc.json",
     "runs.edwards_richardson_k0.2.plateau_150_250_frac", "{:.3f}"),

    # The anchor bed's conditions, as compare_lassitter.py runs them (anchor_bed.py).
    # These rode through build_paper inside \SI{}{}, which the gate stripped whole.
    ("AnchorBedLenMm", "results/anchor_bed.json", "bed_length_mm", "{:.2f}"),
    # counts that were typed as words (number_words.json OWED); each is now read
    ("LzeroNchecks", "verify_solver.json", "",
     lambda d: str(sum(1 for k in d if not k.startswith("_")))),
    ("IsoCCmaxErr", "results/validation.json",
     "by_gate.isotherm obeys Clausius-Clapeyron.values.max_rel_err", lambda x: f"{100 * x:.3f}"),
    ("LtwoNUshaped", "results/l2_v2_verdict.json", "families",
     lambda f: str(sum(1 for v in f.values() if v["shape"].startswith("U-SHAPED")))),
    # the legacy (48-material) depth sweep: d6 and d8 tie to 0.1 %, so "the optimum moved
    # two layers" overstated a coin flip; the prose now gives both (number_words OWED)
    ("LtwoLegacyDsix", "results/l2_results.json", "sweep", lambda rows, _l="d6": (lambda v: "{:.4f}".format(sum(v) / len(v)))([x["novel_material"]["c"] for x in next(r for r in rows if r["family"] == "mlp_depth" and r["label"] == _l)["seeds"].values()])),
    ("LtwoLegacyDeight", "results/l2_results.json", "sweep", lambda rows, _l="d8": (lambda v: "{:.4f}".format(sum(v) / len(v)))([x["novel_material"]["c"] for x in next(r for r in rows if r["family"] == "mlp_depth" and r["label"] == _l)["seeds"].values()])),
    # PREREG_WARP_v2 stage 1: why the warp cannot be re-measured on v2
    ("WarpScreenBoundaryMin", "results/warp_level_screen_bc.json", "B",
     lambda b: f"{100 * min(v['boundary_lo'] for v in b.values()):.0f}"),
    ("WarpScreenNfolds", "results/warp_level_screen_bc.json", "B", lambda b: str(len(b))),
    ("LtwoNconfigs", "results/l2_v2_verdict.json", "families",
     lambda f: str(sum(len(v["rows"]) for v in f.values()))),
    ("WarpMonoMaxDRtwo", "results/warp_monotone.json", "per_seed",
     lambda ps: f"{max(abs(x['r2_proj'][k] - x['r2_raw'][k]) for x in ps for k in ('lo', 'hi')):.1e}"),
    ("ComovingFloorPct", "results/comoving2.json", "",
     lambda d: f"{100 * d['pairs_detail']['0.20-0.80']['interp_floor'] / d['l5_fixed_frame_reference']:.0f}"),
    ("WarpNonmonoLo", "results/warp_monotone.json", "per_seed",
     lambda s: f"{100 * sum(x['nonmonotone_frac']['lo'] for x in s) / len(s):.0f}"),
    ("BtwentyfourRuns", "results/l3_results_B24_WITHDRAWN.json", "arms",
     lambda a: str(sum(len(x["seeds"]) for x in a))),
    ("BtwentyfourUntrained", "results/l3_results_B24_WITHDRAWN.json", "arms",
     lambda a: str(sum(1 for x in a for s in x["seeds"].values()
                       if isinstance(s, dict) and ("error" in s or s.get("early_stop", {}).get("best_step", 1) == 0)))),
    ("LoneLegacyXfloorMin", "results/l1_audit.json", "split_sensitivity.ratios", lambda r: f"{min(r):.0f}"),
    ("LoneLegacyXfloorMax", "results/l1_audit.json", "split_sensitivity.ratios", lambda r: f"{max(r):.0f}"),
    ("AnchorPelletsDeep", "results/dispersion_check.json",
     "anchor.cases.dp3mm_primary.pellets_deep", "{:.1f}"),
    ("AnchorTubeMm", "results/anchor_bed.json", "tube_diameter_mm", "{:.1f}"),
    ("AnchorRH", "results/anchor_bed.json", "rh_percent", "{:.1f}"),
    ("AnchorTK", "results/anchor_bed.json", "T_K", "{:.2f}"),
    ("AnchorRhoB", "results/anchor_bed.json", "bulk_density_kg_m3", "{:.1f}"),
    ("DataBedLenCm", "results/dataset_summary.json", "damkohler_floor.bed_length_m",
     lambda x: f"{100 * x:.0f}"),

    ("DaPelletForUnity", "results/dataset_summary.json", "damkohler_floor.d_p_for_Da_unity_mm", "{:.1f}"),
    ("DaPelletsAcross", "results/dataset_summary.json",
     "damkohler_floor.pellets_across_bed_at_that_d_p", "{:.0f}"),

    # ------------------------------------------- the amortised cost accounting
    ("CostSolveSec", "results/cost_accounting.json", "generation.worker_seconds_per_solve", "{:.1f}"),
    ("CostNSolves", "results/cost_accounting.json", "generation.n_solves", "{:d}"),
    ("CostGenWall", "results/cost_accounting.json", "generation.wall_s", lambda x: f"{x / 3600:.1f}"),
    ("CostWorkers", "results/cost_accounting.json", "generation.workers", "{:d}"),
    ("CostTrainSec", "results/cost_accounting.json", "training.median_seconds", "{:.0f}"),
    ("CostTrainEq", "results/cost_accounting.json", "training.solve_equivalents", "{:.1f}"),
    ("CostTrainSeeds", "results/cost_accounting.json", "training.seconds_per_seed",
     lambda v: f"{len(v):d}"),
    ("CostBreakEven", "results/cost_accounting.json",
     "headline.break_even_queries_lower_bound", "{:.0f}"),
    ("CostSmallSims", "results/cost_accounting.json",
     "frontier[0].n_train_sims_mean_over_folds", "{:.0f}"),
    ("CostSmallBreakEven", "results/cost_accounting.json",
     "frontier[0].break_even_queries_lower_bound", "{:.0f}"),
    ("CostLargeSims", "results/cost_accounting.json",
     "frontier[4].n_train_sims_mean_over_folds", "{:.0f}"),
    # the frontier's middle rows, so the table is built from the file rather than
    # from three macros and two typed numerals
    ("CostSimsB", "results/cost_accounting.json", "frontier[1].n_train_sims_mean_over_folds", "{:.0f}"),
    ("CostSimsC", "results/cost_accounting.json", "frontier[2].n_train_sims_mean_over_folds", "{:.0f}"),
    ("CostSimsD", "results/cost_accounting.json", "frontier[3].n_train_sims_mean_over_folds", "{:.0f}"),
    ("CostErrB", "results/cost_accounting.json", "frontier[1].held_out_nrmse", "{:.4f}"),
    ("CostErrC", "results/cost_accounting.json", "frontier[2].held_out_nrmse", "{:.4f}"),
    ("CostErrD", "results/cost_accounting.json", "frontier[3].held_out_nrmse", "{:.4f}"),
    ("CostBeB", "results/cost_accounting.json", "frontier[1].break_even_queries_lower_bound", "{:.0f}"),
    ("CostBeC", "results/cost_accounting.json", "frontier[2].break_even_queries_lower_bound", "{:.0f}"),
    ("CostBeD", "results/cost_accounting.json", "frontier[3].break_even_queries_lower_bound", "{:.0f}"),

    # ------------------------------------ the harness's own evidence (results/validation.json)
    ("Gates", "results/validation.json", "n_gates", "{:d}"),
    ("MassClosure", "results/validation.json", "by_gate.global mass balance closes.values.default", pct_sig),
    ("MassClosureMof", "results/validation.json", "by_gate.global mass balance closes.values.mof303", pct_sig),
    ("GridConv", "results/validation.json", "by_gate.solution is grid-converged.values.default.err", pct_sig),
    ("GridConvMof", "results/validation.json", "by_gate.solution is grid-converged.values.mof303.err", pct_sig),
    ("GridNz", "results/validation.json", "by_gate.solution is grid-converged.values.default.N_z", "{:d}"),

    # ------------------------------------------------- how far above the floor each arm sits
    ("LoneXfloor", "results/l1_v2_verdict.json", "folds.table.mlp.x_floor", "{:.0f}"),
    ("LtwoXfloor", "results/l2_v2_verdict.json", "families.mlp_depth.rows[6].x_floor", "{:.0f}"),

    # ------------------------------------------------- L2's post-hoc cross-comparisons (B43)
    ("LtwoVsLonePct", "results/l2_v2_verdict.json",
     "cross.comparisons.best (mlp_depth/d8) vs the L1 setting (mlp_depth/d3).relative_to_b.pct", "{:.1f}"),
    ("LtwoVsLoneLo", "results/l2_v2_verdict.json",
     "cross.comparisons.best (mlp_depth/d8) vs the L1 setting (mlp_depth/d3).relative_to_b.pct_ci_low", "{:.1f}"),
    ("LtwoVsLoneHi", "results/l2_v2_verdict.json",
     "cross.comparisons.best (mlp_depth/d8) vs the L1 setting (mlp_depth/d3).relative_to_b.pct_ci_high", "{:.1f}"),
    ("LtwoIdentity", "results/l2_v2_verdict.json",
     "cross.identity.mlp_depth/d3 vs mlp_width/w256.max_abs_per_sample_diff", "{:.2e}"),

    # ------------------------------------------------------------ the anchor's own reference
    ("AnchorNrmseComsol", "results/lassitter_comparison.json", "comsol_line.nrmse_vs_effluent", "{:.3f}"),

    # ------------------------------------------------- the superseded design, for contrast
    ("LsixLegacyBetweenSD", "results/l6_power_corrected.json", "between_sd", "{:.4f}"),
    ("LsixLegacyBase", "results/l6_power_corrected.json", "base", "{:.4f}"),

    # ---------------------------------------- the dataset, both denominators named (B63)
    ("DataNsamples", "results/dataset_summary.json", "n_samples", "{:d}"),
    ("DataNmaterials", "results/dataset_summary.json", "n_materials", "{:d}"),
    ("DataNconditions", "results/dataset_summary.json", "n_conditions", "{:d}"),
    ("DataNrejected", "results/dataset_summary.json", "n_rejected", "{:d}"),
    ("DataNheldout", "results/dataset_summary.json", "n_held_out_materials", "{:d}"),
    ("DaSampleMedian", "results/dataset_summary.json", "damkohler_per_sample.median", "{:.1f}"),
    ("DaSampleBand", "results/dataset_summary.json", "damkohler_per_sample.frac_in_band", pct),
    ("DaSampleMin", "results/dataset_summary.json", "damkohler_per_sample.min", "{:.1f}"),
    ("DaSampleMax", "results/dataset_summary.json", "damkohler_per_sample.max", "{:.0f}"),
    ("DaMatMedian", "results/dataset_summary.json", "damkohler_per_material.median", "{:.1f}"),
    ("DaMatBand", "results/dataset_summary.json", "damkohler_per_material.frac_in_band", pct),
    ("DaMatMin", "results/dataset_summary.json", "damkohler_per_material.min", "{:.1f}"),
    ("DaMatMax", "results/dataset_summary.json", "damkohler_per_material.max", "{:.0f}"),
    ("DaMatDecades", "results/dataset_summary.json", "damkohler_per_material.decades", "{:.2f}"),
    ("DaLegacyMedian", "results/dataset_summary_legacy.json", "damkohler_per_sample.median", "{:.1f}"),
    ("DaLegacyAbove", "results/dataset_summary_legacy.json", "frac_above_band_per_sample", pct),

    # ---------------------------------------- the correction ledger, counted not typed
    ("LedgerA", "results/ledger_counts.json", "n_part_a", "{:d}"),
    ("LedgerB", "results/ledger_counts.json", "n_part_b", "{:d}"),
    ("LedgerTotal", "results/ledger_counts.json", "n_total", "{:d}"),
    ("LedgerOwn", "results/ledger_counts.json", "n_own_error_phrase", "{:d}"),

    # ---------------------------------------------------------------- L4b-v2
    ("LfourbVerdictMaterial", "results/l4b_v2_verdict.json", "axes.material.verdict", "{}"),
    # L4b time axis (final: w1e-5 ties the twin, so the edge rule is satisfied there)
    ("LfourbTimeTwin", "results/l4b_v2_verdict.json", "axes.time.best_pi_vs_data_only.mean_a", "{:.4f}"),
    ("LfourbTimeBest", "results/l4b_v2_verdict.json", "axes.time.best_pi_vs_data_only.mean_b", "{:.4f}"),
    ("LfourbTimeLo", "results/l4b_v2_verdict.json", "axes.time.best_pi_vs_data_only.ci_low", "{:.5f}"),
    ("LfourbTimeHi", "results/l4b_v2_verdict.json", "axes.time.best_pi_vs_data_only.ci_high", "{:.5f}"),
    ("LfourbTimeMDE", "results/l4b_v2_verdict.json", "axes.time.mde",
     lambda m: f"{100 * next(v['mde_80'] for v in m.values()):.0f}"),
    ("LfourbTimeNmat", "results/l4b_v2_verdict.json", "axes.time.best_pi_vs_data_only.n_materials", "{:d}"),
    ("LfourbNeligible", "results/l4b_v2_verdict.json", "axes.time.eligible", lambda a: str(len(a))),
    ("LfourbNabandoned", "results/l4b_v2_verdict.json", "axes.time.abandoned", lambda a: str(len(a))),
    ("LfourbTimePolTwin", "results/l4b_v2_verdict.json", "axes.time.polish.comparison.mean_a", "{:.4f}"),
    ("LfourbTimePolBest", "results/l4b_v2_verdict.json", "axes.time.polish.comparison.mean_b", "{:.4f}"),
    ("LfourbTimePolLo", "results/l4b_v2_verdict.json", "axes.time.polish.comparison.ci_low", "{:.5f}"),
    ("LfourbTimePolHi", "results/l4b_v2_verdict.json", "axes.time.polish.comparison.ci_high", "{:.5f}"),
    ("LfourbTimeSeenRise", "results/l4b_v2_verdict.json", "refine.time/data_only.seen_change_pct", "{:.0f}"),
    ("LfourbVerdictTime", "results/l4b_v2_verdict.json", "axes.time.verdict", "{}"),
    # L4b material axis (final after the second edge extension: w1e-5 is interior,
    # bracketed by w1e-6 and w1e-4, so the edge rule is satisfied there)
    ("LfourbMatTwin", "results/l4b_v2_verdict.json", "axes.material.best_pi_vs_data_only.mean_a", "{:.4f}"),
    ("LfourbMatBest", "results/l4b_v2_verdict.json", "axes.material.best_pi_vs_data_only.mean_b", "{:.4f}"),
    ("LfourbMatLo", "results/l4b_v2_verdict.json", "axes.material.best_pi_vs_data_only.ci_low", "{:.5f}"),
    ("LfourbMatHi", "results/l4b_v2_verdict.json", "axes.material.best_pi_vs_data_only.ci_high", "{:.5f}"),
    ("LfourbMatNmat", "results/l4b_v2_verdict.json", "axes.material.best_pi_vs_data_only.n_materials", "{:d}"),
    ("LfourbMatBelow", "results/l4b_v2_verdict.json", "axes.material.table.pi_fixed_w1e-6.held", "{:.4f}"),
    ("LfourbMatAbove", "results/l4b_v2_verdict.json", "axes.material.table.pi_fixed_w1e-4.held", "{:.4f}"),
    ("LfourbMatPolTwin", "results/l4b_v2_verdict.json", "axes.material.polish.comparison.mean_a", "{:.4f}"),
    ("LfourbMatPolBest", "results/l4b_v2_verdict.json", "axes.material.polish.comparison.mean_b", "{:.4f}"),
    ("LfourbMatPolLo", "results/l4b_v2_verdict.json", "axes.material.polish.comparison.ci_low", "{:.5f}"),
    ("LfourbMatPolHi", "results/l4b_v2_verdict.json", "axes.material.polish.comparison.ci_high", "{:.5f}"),
]



# Quantities the manuscript quotes that are RATIOS of measured values. Each carries the
# formula it is computed from, so "43x above the floor" is auditable rather than typed.
# They are derived here rather than in the prose for the same reason every other number
# is: a ratio typed into LaTeX is a number with no script behind it (B43).
DERIVED = [
    ("LthreeBestKanDiff", "perceptron minus best KAN held-out error (both from audit_l3.py)",
     lambda r: r["LthreeBestKanMlp"] - r["LthreeBestKan"], "{:.4f}"),
    # number-words paid 2026-09-27 (paper/number_words.json OWED entries)
    ("AnchorAspect", "anchor bed length divided by tube diameter",
     lambda r: r["AnchorBedLenMm"] / r["AnchorTubeMm"], "{:.2f}"),
    ("LCexpRatio", "conditions-axis learning-curve exponent over the materials-axis one",
     lambda r: r["LCcondBeta"] / r["LCbeta"], "{:.2f}"),
    ("LthreeLrDecades", "decades between the Chebyshev and perceptron optimal learning rates",
     lambda r: __import__("math").log10(float(r["LthreeChebyLr"]) / float(r["LthreeMlpLr"])), "{:.1f}"),
    ("FloorDrop", "POD floor at p=8 divided by the floor at p=128",
     lambda r: r["LfiveFloorSmall"] / r["LfiveFloorLarge"], "{:.1f}"),
    ("FNOxFloor", "the best FNO divided by the POD floor at p=128",
     lambda r: r["LfiveFNO"] / r["LfiveFloor"], "{:.0f}"),
    ("ONetxFloor", "the best DeepONet found anywhere (the p=8 arm) divided by the POD floor at p=128",
     lambda r: r["LfiveONet"] / r["LfiveFloor"], "{:.0f}"),
    ("FNOgain", "the best DeepONet divided by the best FNO",
     lambda r: r["LfiveONet"] / r["LfiveFNO"], "{:.2f}"),
    # nwidth.py fits the RESIDUAL ENERGY -- 1 minus the cumulative explained-variance
    # ratio -- against n, so `algebraic_exponent` is an ENERGY exponent. The
    # Kolmogorov n-width is the residual NORM, the square root of that, so its
    # exponent is half. The prose used to quote the energy exponent and call it the
    # n-width while quoting a halving factor computed correctly from the norm, so
    # the two numbers in one sentence disagreed by a factor of two in the exponent
    # and anybody recomputing 2^(1/2.45) found the mismatch at once. The code was
    # right and both its own docstring and the prose were wrong.
    ("NwidthExpErr", "the n-width (error) exponent: half the fitted energy exponent",
     lambda r: r["NwidthExpC"] / 2.0, "{:.2f}"),
    ("NwidthHalving", "modes needed to halve the ERROR, 2^(1/|energy exponent / 2|)",
     lambda r: 2.0 ** (1.0 / abs(r["NwidthExpC"] / 2.0)), "{:.2f}"),
    ("LfiveCoefChangePct", "the coefficient-map error's change from p=8 to p=128, per cent",
     lambda r: 100.0 * abs(r["LfiveCoefLarge"] - r["LfiveCoefSmall"]) / r["LfiveCoefSmall"],
     "{:.1f}"),
    # WarpHeadroom (results/warp_verdict.json headroom_to_oracle) is the oracle
    # against the PREDICTED two-wave arm. The abstract's "buys ... under an oracle"
    # is necessarily relative to NOT applying the coordinate change at all, i.e. to
    # the fixed frame, which is a different denominator. Both are declared, and the
    # prose now names which one it means in each place.
    ("WarpHeadroomFixed", "the fixed frame divided by the oracle two-wave arm",
     lambda r: r["WarpFixed"] / r["WarpOracle"], "{:.2f}"),
    # How much of the anchor's shock-dispersion discrepancy the untruncated closure
    # removes. This was a bolded "roughly half" -- a hedge doing work two numbers
    # should do, and wrong in both of them (61 % on the arrival time, 18 % on the
    # error), in a limitations paragraph whose whole purpose is to quantify.
    ("AnchorTcutPct", "the share of the 95 % arrival-time EXCESS over experiment that "
                      "the untruncated dispersion closure removes",
     lambda r: 100.0 * (1.0 - (r["AnchorTninetyfiveER"] - r["AnchorTninetyfiveExp"])
                        / (r["AnchorTninetyfiveModel"] - r["AnchorTninetyfiveExp"])), "{:.0f}"),
    ("AnchorNrmseCutPct", "the share of the anchor nRMSE the untruncated closure removes",
     lambda r: 100.0 * (1.0 - r["AnchorNrmseER"] / r["AnchorNrmse"]), "{:.0f}"),
    # The flat-in-p null in RELATIVE terms. An absolute interval of +/- 0.005 on a
    # base of 0.0265 is not interpretable on sight, and "flat" is an elimination
    # claim in the abstract, so what the interval actually EXCLUDES has to be said.
    ("LfiveFlatImproveMax", "the largest improvement from p=8 to p=128 the interval admits, per cent",
     lambda r: 100.0 * r["LfiveFlatHi"] / r["LfiveFlatBase"], "{:.0f}"),
    ("LfiveFlatDegradeMax", "the largest degradation the interval admits, per cent",
     lambda r: 100.0 * abs(r["LfiveFlatLo"]) / r["LfiveFlatBase"], "{:.0f}"),
    ("LsixNoiseDrop", "the legacy between-material sd divided by v2's",
     lambda r: r["LsixLegacyBetweenSD"] / r["LsixBetweenSD"], "{:.1f}"),
    ("LsixLegacyBetweenOverBase", "the legacy between-material sd as a share of its base error",
     lambda r: 100.0 * r["LsixLegacyBetweenSD"] / r["LsixLegacyBase"], "{:.0f}"),
    ("GapRange", "the outlet separation of the two waves, max divided by min",
     lambda r: r["GapMax"] / r["GapMin"], "{:.0f}"),
    ("LCmaterialsForHalving", "materials needed to halve the error at the measured exponent",
     lambda r: 2.0 ** (1.0 / r["LCbeta"]), "{:.0f}"),
    ("CostDataRatio", "training simulations at 192 materials divided by those at 12",
     lambda r: r["CostLargeSims"] / r["CostSmallSims"], "{:.0f}"),
    ("CostGenCoreHours", "the training set's cost in core-hours: solves x worker-seconds",
     lambda r: r["CostNSolves"] * r["CostSolveSec"] / 3600.0, "{:.0f}"),
    ("LfourbMatGainPct", "L4b material axis: the best physics arm's error reduction, % of the twin's",
     lambda r: 100.0 * (r["LfourbMatTwin"] - r["LfourbMatBest"]) / r["LfourbMatTwin"], "{:.0f}"),
]

def dig(obj, path):
    """Resolve a dotted path, with [i] for list indices. Raises on any miss.

    Keys containing dots (`0.05`, `mlp vs klinkenberg`) are handled by trying the
    longest matching literal key at each step before splitting further — a plain
    `split('.')` would silently fail on both, and silently is the one thing a
    resolver may never do.
    """
    cur, rest = obj, path
    while rest:
        if rest.startswith("["):
            end = rest.index("]")
            cur = cur[int(rest[1:end])]
            rest = rest[end + 1:].lstrip(".")
            continue
        if isinstance(cur, dict):
            cand = [k for k in cur if rest == k or rest.startswith(k + ".") or rest.startswith(k + "[")]
            if not cand:
                raise KeyError(f"no key of {sorted(cur)[:6]}... matches {rest!r}")
            k = max(cand, key=len)
            cur = cur[k]
            rest = rest[len(k):].lstrip(".")
            continue
        raise KeyError(f"cannot descend into {type(cur).__name__} for {rest!r}")
    return cur


def resolve(verbose=False):
    cache, out, raw, failures, pending = {}, {}, {}, [], []
    for key, fname, path, fmt in SPEC:
        full = os.path.join(ROOT, fname)
        if fname not in cache:
            cache[fname] = json.load(open(full)) if os.path.exists(full) else None
        doc = cache[fname]
        if fname == "results/validation.json" and doc is not None:
            # The harness record is only a source if it is a clean, FULL run. Reading
            # n_pass let a failing or skipped gate shrink the reported harness instead
            # of stopping the build (audit_hygiene #4, #8).
            # The manuscript gate is EXCLUDED: it checks numbers.tex, which this script
            # writes, so requiring it here deadlocks the moment a macro is sourced from
            # validation.json (hit 2026-09-27 adding IsoCCmaxErr). build_paper.py runs the
            # identical checks on the regenerated numbers.tex, so nothing escapes.
            bad = [f"{g['gate']} [{g['state']}]" for g in doc.get("gates", [])
                   if g["state"] != "PASS" and g["gate"] != "the manuscript contains no hand-typed number"]
            if doc.get("only") is not None or bad or "n_gates" not in doc:
                failures.append(f"{key}: {fname} is not a clean full harness run "
                                f"(only={doc.get('only')!r}; not passing: {', '.join(bad) or 'none'}"
                                f"{'; no n_gates -- re-run validate.py --json' if 'n_gates' not in doc else ''})")
                continue
        if doc is None:
            if fname in PENDING:
                out[key] = PENDING_TEXT
                pending.append((key, fname, PENDING[fname]))
            else:
                failures.append(f"{key}: {fname} does not exist")
            continue
        if fname in PENDING:
            failures.append(f"{key}: {fname} is declared PENDING but EXISTS — "
                            f"remove it from PENDING and re-run")
            continue
        try:
            v = dig(doc, path)
        except Exception as e:
            failures.append(f"{key}: {fname}:{path} — {e}")
            continue
        if isinstance(v, float) and not math.isfinite(v):
            failures.append(f"{key}: {fname}:{path} is not finite ({v})")
            continue
        if key in GATED:
            mfile, marker, why = GATED[key]
            mpath = os.path.join(ROOT, mfile)
            done = os.path.exists(mpath) and marker in open(mpath, encoding="utf-8",
                                                             errors="replace").read()
            if not done:
                out[key] = PENDING_TEXT
                pending.append((key, fname, why))
                continue
        out[key] = tex_safe(key, fmt(v) if callable(fmt) else fmt.format(v))
        raw[key] = v
        if verbose:
            print(f"  {key:<26} {out[key]:<28} <- {fname}:{path}")

    for key, formula, fn, fmt in DERIVED:
        try:
            v = fn(raw)
        except Exception as e:
            failures.append(f"{key}: derived ({formula}) — {e}")
            continue
        if not math.isfinite(v):
            failures.append(f"{key}: derived ({formula}) is not finite")
            continue
        out[key] = tex_safe(key, fmt.format(v))
        raw[key] = v
        if verbose:
            print(f"  {key:<26} {out[key]:<28} <- derived: {formula}")
    return out, failures, pending


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    vals, failures, pending = resolve(verbose=args.list)
    print(f"\n{len(vals)}/{len(SPEC) + len(DERIVED)} keys resolved "
          f"({len(SPEC)} read from {len({s[1] for s in SPEC})} results files, "
          f"{len(DERIVED)} derived as declared ratios)")
    for key, fname, why in pending:
        print(f"  PENDING  {key:<26} <- {fname}  ({why})")
    for f in failures:
        print(f"  FAIL     {f}")
    if failures:
        print(f"\n{len(failures)} key(s) could not be resolved. The manuscript may not be built.")
        sys.exit(1)
    if args.check:
        print("\nall keys resolve" + (f"; {len(pending)} pending" if pending else ""))
        return

    os.makedirs(os.path.dirname(OUT_TEX), exist_ok=True)
    with open(OUT_TEX, "w", encoding="utf-8") as fh:
        fh.write("% GENERATED BY paper/numbers.py — DO NOT EDIT.\n"
                 "% Every value below is read from a results file; see SPEC in numbers.py\n"
                 "% for the file and path behind each one.\n")
        for key, _, _, _ in SPEC:
            fh.write(f"\\newcommand{{\\n{key}}}{{{vals[key]}}}\n")
        fh.write("% derived ratios — the formula behind each is in DERIVED in numbers.py\n")
        for key, formula, _, _ in DERIVED:
            fh.write(f"% {key}: {formula}\n")
            fh.write(f"\\newcommand{{\\n{key}}}{{{vals[key]}}}\n")
    prov = {k: {"file": f, "path": p} for k, f, p, _ in SPEC}
    prov.update({k: {"derived": formula} for k, formula, _, _ in DERIVED})
    json.dump({"values": vals, "provenance": prov,
               "pending": [{"key": k, "file": f, "why": w} for k, f, w in pending]},
              open(OUT_JSON, "w"), indent=2)
    print(f"\nwrote {os.path.relpath(OUT_TEX, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}"
          + (f"  ({len(pending)} PENDING — the manuscript is not final)" if pending else ""))


if __name__ == "__main__":
    main()
