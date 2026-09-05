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
PENDING = {
    "results/l4b_v2_verdict.json": "L4b-v2 is still running",
}
PENDING_TEXT = r"\textbf{[PENDING]}"


def pct(x):
    return f"{100 * x:.1f}"


def sig(x, n=3):
    if x == 0:
        return "0"
    d = max(0, n - 1 - int(math.floor(math.log10(abs(x)))))
    return f"{x:.{d}f}"


# key -> (file, dotted path, formatter). The dotted path may index lists with [i].
SPEC = [
    # ---------------------------------------------------------------- L0
    ("LzeroTracer", "verify_solver.json", "tracer_van_genuchten.max_abs_err_vs_third_type", "{:.2e}"),
    ("LzeroTracerFront", "verify_solver.json", "tracer_van_genuchten.front_rel_err", pct),
    ("LzeroTracerPe", "verify_solver.json", "tracer_van_genuchten.Pe", "{:.0f}"),
    ("LzeroBCdiff", "verify_solver.json", "tracer_van_genuchten.bc_difference_max", pct),
    ("LzeroRetarded", "verify_solver.json", "retarded_front.rel_err", pct),
    ("LzeroRetardedR", "verify_solver.json", "retarded_front.R", "{:.0f}"),
    ("LzeroThermal", "verify_solver.json", "thermal_wave.rel_err", pct),
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
    ("LthreeBestKanMlp", "results/l3_final_pair.json", "mlp", "{:.4f}"),
    ("LthreeBestKan", "results/l3_final_pair.json", "rbf_g4", "{:.4f}"),
    ("LthreeBestKanDiff", "results/l3_final_pair.json", "diff", "{:.4f}"),
    ("LthreeBestKanLo", "results/l3_final_pair.json", "ci[0]", "{:.4f}"),
    ("LthreeBestKanHi", "results/l3_final_pair.json", "ci[1]", "{:.4f}"),

    # ------------------------------------------------------------- L5 (legacy)
    ("LfiveFNO", "results/l5_fno_verdict.json", "fno_best.mean", "{:.4f}"),
    ("LfiveFNOmodes", "results/l5_fno_verdict.json", "fno_best.modes", "{:d}"),
    ("LfiveFNOwidth", "results/l5_fno_verdict.json", "fno_best.width", "{:d}"),
    ("LfiveONet", "results/l5_fno_verdict.json", "deeponet_best", "{:.4f}"),
    ("LfiveOKAN", "results/l5_fno_verdict.json", "deepokan_best", "{:.4f}"),
    ("LfiveFloor", "results/l5_fno_verdict.json", "pod_floor_p128", "{:.2e}"),
    ("LfiveONetFNOdiff", "results/l5_fno_verdict.json", "deeponet_vs_fno.mean_diff", "{:.5f}"),
    ("LfiveONetFNOlo", "results/l5_fno_verdict.json", "deeponet_vs_fno.ci_low", "{:.5f}"),
    ("LfiveONetFNOhi", "results/l5_fno_verdict.json", "deeponet_vs_fno.ci_high", "{:.5f}"),
    ("LfiveFlatDiff", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.mean_diff", "{:.5f}"),
    ("LfiveFlatLo", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.ci_low", "{:.5f}"),
    ("LfiveFlatHi", "results/l5_merged.json", "paired_vs_smallest_p.deeponet_p128.ci_high", "{:.5f}"),
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


    # ------------------------------------ the harness's own evidence (results/validation.json)
    ("Gates", "results/validation.json", "n_pass", "{:d}"),
    ("MassClosure", "results/validation.json", "by_gate.global mass balance closes.values.default", pct),
    ("MassClosureMof", "results/validation.json", "by_gate.global mass balance closes.values.mof303", pct),
    ("GridConv", "results/validation.json", "by_gate.solution is grid-converged.values.default.err", pct),
    ("GridConvMof", "results/validation.json", "by_gate.solution is grid-converged.values.mof303.err", pct),
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

    # ---------------------------------------- the correction ledger, counted not typed
    ("LedgerA", "results/ledger_counts.json", "n_part_a", "{:d}"),
    ("LedgerB", "results/ledger_counts.json", "n_part_b", "{:d}"),
    ("LedgerTotal", "results/ledger_counts.json", "n_total", "{:d}"),
    ("LedgerOwn", "results/ledger_counts.json", "n_own_error_phrase", "{:d}"),

    # ---------------------------------------------------------------- L4b-v2
    ("LfourbVerdictMaterial", "results/l4b_v2_verdict.json", "axes.material.verdict", "{}"),
    ("LfourbVerdictTime", "results/l4b_v2_verdict.json", "axes.time.verdict", "{}"),
]



# Quantities the manuscript quotes that are RATIOS of measured values. Each carries the
# formula it is computed from, so "43x above the floor" is auditable rather than typed.
# They are derived here rather than in the prose for the same reason every other number
# is: a ratio typed into LaTeX is a number with no script behind it (B43).
DERIVED = [
    ("FloorDrop", "POD floor at p=8 divided by the floor at p=128",
     lambda r: r["LfiveFloorSmall"] / r["LfiveFloorLarge"], "{:.1f}"),
    ("FNOxFloor", "the best FNO divided by the POD floor at p=128",
     lambda r: r["LfiveFNO"] / r["LfiveFloor"], "{:.0f}"),
    ("ONetxFloor", "the best DeepONet divided by the POD floor at p=128",
     lambda r: r["LfiveONet"] / r["LfiveFloor"], "{:.0f}"),
    ("FNOgain", "the best DeepONet divided by the best FNO",
     lambda r: r["LfiveONet"] / r["LfiveFNO"], "{:.2f}"),
    ("NwidthHalving", "modes needed to halve the error, 2^(1/|algebraic exponent|)",
     lambda r: 2.0 ** (1.0 / abs(r["NwidthExpC"] / 2.0)), "{:.2f}"),
    ("LsixNoiseDrop", "the legacy between-material sd divided by v2's",
     lambda r: r["LsixLegacyBetweenSD"] / r["LsixBetweenSD"], "{:.1f}"),
    ("LsixLegacyBetweenOverBase", "the legacy between-material sd as a share of its base error",
     lambda r: 100.0 * r["LsixLegacyBetweenSD"] / r["LsixLegacyBase"], "{:.0f}"),
    ("GapRange", "the outlet separation of the two waves, max divided by min",
     lambda r: r["GapMax"] / r["GapMin"], "{:.0f}"),
    ("LCmaterialsForHalving", "materials needed to halve the error at the measured exponent",
     lambda r: 2.0 ** (1.0 / r["LCbeta"]), "{:.0f}"),
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
        out[key] = fmt(v) if callable(fmt) else fmt.format(v)
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
        out[key] = fmt.format(v)
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
