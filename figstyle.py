"""One visual style for every figure in the paper.

Imported by every fig_*.py (and the anchor scripts) so the figures read as one set:
the same fonts and sizes, the same axis treatment, the same colours for the same
arms, and readable names instead of code identifiers. Panel titles are sentence-case
statements without dashes; numbers in titles or notes are read from results files by
the calling script, never typed here.

    import figstyle; figstyle.apply()
    figstyle.name("rbf_kan")  -> "Gaussian-RBF KAN"
"""
import matplotlib as mpl

# Okabe-Ito-derived, colour-blind-safe, consistent across figures
C = {
    "blue": "#3b6ea5", "orange": "#e08a35", "red": "#b5423f", "green": "#5f9a4a",
    "grey": "#8a8a8a", "dark": "#2b2b2b", "purple": "#7a5195", "teal": "#2a9d8f",
}
ARM_COLOUR = {
    "mlp": C["blue"], "xgb": C["orange"], "rf": C["green"], "ridge": C["red"],
    "rbf_kan": C["orange"], "cheby_kan": C["red"],
    "deeponet": C["blue"], "deepokan": C["red"], "fno": C["green"], "pod_reg": C["orange"],
    "floor": C["dark"], "gp": C["purple"],
}
NAMES = {
    "mlp": "MLP", "xgb": "gradient boosting", "rf": "random forest", "ridge": "ridge",
    "rbf_kan": "Gaussian-RBF KAN", "cheby_kan": "Chebyshev KAN",
    "deeponet": "DeepONet", "deepokan": "DeepOKAN", "fno": "Fourier neural operator",
    "gp": "Gaussian process", "pod_reg": "POD + gradient boosting",
}


def name(key):
    return NAMES.get(key, key)


def apply():
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.titleweight": "normal",
        "axes.titlelocation": "left",
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.8,
        "ytick.labelsize": 7.8,
        "legend.fontsize": 7.6,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#e6e6e6",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "lines.linewidth": 1.6,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,          # editable text in the PDF, as journals ask
        "ps.fonttype": 42,
        "mathtext.default": "regular",
    })
