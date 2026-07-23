# -*- coding: utf-8 -*-
"""Shared chart styling — one palette, used by the notebook, the dashboard and the slides."""

# Fixed-order categorical palette (validated for colorblind-safe adjacent contrast).
# Always assign by position in this list — never cycle or reorder per-chart.
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

# Fixed binary mapping for every Sim/Não-style chart in the project.
SIM = CATEGORICAL[0]   # blue
NAO = CATEGORICAL[1]   # orange

# Fixed mapping for the nationality split.
PORTUGUESA = CATEGORICAL[0]
ESTRANGEIRA = CATEGORICAL[1]

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"

FONT_FAMILY = "Segoe UI"

MAX_CATEGORIES_ON_CHART = 7  # beyond this, fold the smallest into "Outras"


def apply_mpl_style():
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRIDLINE,
        "axes.labelcolor": INK_SECONDARY,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRIDLINE,
        "grid.linewidth": 0.8,
        "text.color": INK_PRIMARY,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK_PRIMARY,
        "font.size": 10.5,
    })
