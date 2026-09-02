"""Digitise Fig. 10 of Lassitter et al. (2024), Chem. Eng. Sci. 285:119430.

The figure — "Experimental Breakthrough Curve (points) and COMSOL model (line)" —
is the only published MOF-303 packed-bed breakthrough curve whose operating
conditions are fully on record (SI Table S8; see CITATIONS.md): bed height
6.35 mm in a 38.1 mm tube, 670.8 cm3/min of ambient air at 32.8 % RH and 298.15 K,
3.11 g of binder-free pellets, bulk density 429.58 kg/m3, bed porosity 0.4
(estimated). It shows the two-wave breakthrough of section 6c in a real bed: a
Henry-branch leak to a ~9 % RH plateau, then the cooperative shock to the inlet.

Input: a PNG of the figure extracted from the main-text PDF (page 10, xref 214)
and kept locally under refs/ (copyrighted; not committed). Output: the digitised
series as CSV (committed) and a QA overlay so the digitisation can be checked by
eye. Nothing here is fitted; it is a measurement of the published figure.

Method: the plot frame's corners are the axis limits (0-600 min, 0-35 % RH), as
drawn by the authors' plotting software; the red model line is picked by colour;
the open markers are connected components of dark pixels off the frame,
classified square (inlet) vs circle (effluent) by whether their bounding-box
corners are inked.

    python digitise_lassitter.py --png refs/Lassitter2024_fig10.png
"""
from __future__ import annotations

import argparse
import csv
import os

import numpy as np
from PIL import Image
from scipy import ndimage

XLIM, YLIM = (0.0, 600.0), (0.0, 35.0)       # axis limits = frame corners


def find_frame(dark):
    """Longest dark horizontal/vertical runs -> (x0, x1, y0, y1) in pixels."""
    h, w = dark.shape
    col = dark.sum(0); row = dark.sum(1)
    xs = np.where(col > 0.6 * h)[0]; ys = np.where(row > 0.6 * w)[0]
    if xs.size < 2 or ys.size < 2:
        raise RuntimeError("frame not found — is the crop the whole figure?")
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def px_to_data(x, y, frame):
    x0, x1, y0, y1 = frame
    t = XLIM[0] + (x - x0) / (x1 - x0) * (XLIM[1] - XLIM[0])
    rh = YLIM[1] - (y - y0) / (y1 - y0) * (YLIM[1] - YLIM[0])
    return t, rh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", default="refs/Lassitter2024_fig10.png")
    ap.add_argument("--out", default="refs/Lassitter2024_fig10_digitised.csv")
    ap.add_argument("--qa", default="figures/qa_lassitter_fig10_digitised.png")
    args = ap.parse_args()

    im = np.asarray(Image.open(args.png).convert("RGB")).astype(int)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    dark = (R < 110) & (G < 110) & (B < 110)
    red = (R > 150) & (G < 110) & (B < 110)
    frame = find_frame(dark)
    x0, x1, y0, y1 = frame
    print(f"frame px: x {x0}-{x1}, y {y0}-{y1}")

    def in_legend(t, rh):
        return t > 420 and 2.0 < rh < 13.0        # the legend box, lower right

    # ── model line: per-column median of red pixels inside the frame ──────────
    # The legend's red line sample is excluded by position, not by colour.
    model = []
    for x in range(x0 + 1, x1):
        ys = np.where(red[y0:y1, x])[0]
        if ys.size:
            keep = [y for y in ys if not in_legend(*px_to_data(x, y0 + y, frame))]
            if keep:
                model.append(px_to_data(x, y0 + np.median(keep), frame))
    model = np.array(model)

    # ── markers sitting ON the bottom axis line (effluent at 0 % RH) ─────────
    # These straddle the frame line, so the frame mask below would cut them in
    # half. Detect the upper arc in the strip just above the line, wide and flat,
    # and record them at RH = 0 with a flag. Inward tick marks are narrow (≤ 3 px)
    # and are rejected by the width test.
    strip = dark[y1 - 12:y1 - 2, x0 + 4:x1 - 4].copy()
    lab_s, n_s = ndimage.label(strip)
    on_axis = []
    for k, sl in enumerate(ndimage.find_objects(lab_s), start=1):
        comp = lab_s[sl] == k
        hh, ww = comp.shape
        if ww >= 6 and hh <= 10 and comp.sum() >= 8:
            cx = sl[1].start + ndimage.center_of_mass(comp)[1] + x0 + 4
            on_axis.append((px_to_data(cx, y1, frame)[0], 0.0, int(comp.sum()), 0.0))

    # ── markers: dark components off the frame lines and tick marks ──────────
    mask = dark.copy()
    m = 3
    mask[:, max(0, x0 - m):x0 + m + 1] = False; mask[:, max(0, x1 - m):x1 + m + 1] = False
    mask[max(0, y0 - m):y0 + m + 1, :] = False; mask[max(0, y1 - m):y1 + m + 1, :] = False
    mask[:y0, :] = False; mask[y1:, :] = False; mask[:, :x0] = False; mask[:, x1:] = False
    lab, n = ndimage.label(mask)
    objs = ndimage.find_objects(lab)
    inlet, effluent, rejected = [], [], []
    for k, sl in enumerate(objs, start=1):
        comp = lab[sl] == k
        area = int(comp.sum())
        hh, ww = comp.shape
        if not (12 <= area <= 600) or not (5 <= hh <= 24 and 5 <= ww <= 24):
            continue
        cy, cx = ndimage.center_of_mass(comp)
        cy += sl[0].start; cx += sl[1].start
        t, rh = px_to_data(cx, cy, frame)
        # the legend sits in the lower right; its sample markers are not data
        if in_legend(t, rh):
            rejected.append((t, rh, "legend")); continue
        c = 3
        corners = [comp[:c, :c].mean(), comp[:c, -c:].mean(), comp[-c:, :c].mean(), comp[-c:, -c:].mean()]
        square = np.mean(corners) > 0.45
        (inlet if square else effluent).append((t, rh, area, float(np.mean(corners))))
    # on-axis circles only where no off-axis effluent point exists yet
    first_eff = min((p[0] for p in effluent), default=XLIM[1])
    on_axis = [p for p in on_axis if p[0] < first_eff - 5]
    effluent += on_axis
    inlet.sort(); effluent.sort()
    print(f"components: {n}; inlet squares {len(inlet)}, effluent circles {len(effluent)} "
          f"(of which {len(on_axis)} on the axis line at RH 0), legend-rejected {len(rejected)}")
    # markers overlapping after the shock (inlet and effluent both at ~32-33 %) are
    # flagged: the square/circle classification is unreliable when two markers merge
    overlap_t = 330.0

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["series", "t_min", "rh_percent", "note"])
        for t, rh, a, cf in inlet:
            w.writerow(["inlet_square", f"{t:.2f}", f"{rh:.3f}",
                        f"area={a};corner_ink={cf:.2f}" + (";markers_overlap" if t > overlap_t else "")])
        for t, rh, a, cf in effluent:
            w.writerow(["effluent_circle", f"{t:.2f}", f"{rh:.3f}",
                        f"area={a};corner_ink={cf:.2f}" + (";on_axis_line_rh_set_to_0" if rh == 0.0 else "")
                        + (";markers_overlap" if t > overlap_t else "")])
        for t, rh in model:
            w.writerow(["comsol_model_line", f"{t:.2f}", f"{rh:.3f}", ""])
    print(f"wrote {args.out}")

    # ── QA overlay ────────────────────────────────────────────────────────────
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.imshow(np.asarray(Image.open(args.png)))
    for t, rh, *_ in inlet:
        x = x0 + (t - XLIM[0]) / (XLIM[1] - XLIM[0]) * (x1 - x0); y = y0 + (YLIM[1] - rh) / (YLIM[1] - YLIM[0]) * (y1 - y0)
        a1.plot(x, y, "s", ms=4, mfc="none", mec="tab:blue")
    for t, rh, *_ in effluent:
        x = x0 + (t - XLIM[0]) / (XLIM[1] - XLIM[0]) * (x1 - x0); y = y0 + (YLIM[1] - rh) / (YLIM[1] - YLIM[0]) * (y1 - y0)
        a1.plot(x, y, "o", ms=4, mfc="none", mec="tab:green")
    a1.set_title("detected markers over the source figure"); a1.axis("off")
    if len(inlet):
        a2.plot([p[0] for p in inlet], [p[1] for p in inlet], "s", ms=4, mfc="none", label="inlet (digitised)")
    a2.plot([p[0] for p in effluent], [p[1] for p in effluent], "o", ms=4, mfc="none", label="effluent (digitised)")
    if len(model):
        a2.plot(model[:, 0], model[:, 1], "r-", lw=1.2, label="COMSOL line (digitised)")
    a2.set_xlim(*XLIM); a2.set_ylim(*YLIM); a2.set_xlabel("time (min)"); a2.set_ylabel("% RH")
    a2.legend(fontsize=8); a2.set_title("digitised series, Lassitter 2024 Fig. 10")
    os.makedirs(os.path.dirname(args.qa) or ".", exist_ok=True)
    fig.savefig(args.qa, dpi=160, bbox_inches="tight")
    print(f"wrote {args.qa}")


if __name__ == "__main__":
    main()
