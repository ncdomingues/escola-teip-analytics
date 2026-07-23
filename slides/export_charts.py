# -*- coding: utf-8 -*-
"""Renders the chart images used by the slide deck. Run before build_deck.py."""
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import analysis as an  # noqa: E402
import style  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)
style.apply_mpl_style()

df = an.load_data()


def savefig(fig, name):
    # pure white, not style.SURFACE - these get embedded straight onto a white slide,
    # and the off-white chart surface would show as a faint box around the image.
    fig.savefig(ASSETS / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# 1. PT vs Estrangeira donut
ratio = an.pt_vs_estrangeira(df)
pct = (ratio / ratio.sum() * 100).round(1)
fig, ax = plt.subplots(figsize=(5, 5))
ax.pie(
    ratio, labels=[f"{i}\n{p}%" for i, p in zip(ratio.index, pct)],
    colors=[style.PORTUGUESA, style.ESTRANGEIRA], startangle=90,
    wedgeprops={"linewidth": 3, "edgecolor": style.SURFACE},
    textprops={"fontsize": 13, "color": style.INK_PRIMARY},
)
ax.set_title("")
savefig(fig, "chart_nationality_ratio.png")

# 2. Nationalities represented
nat = an.nationality_breakdown(df, top_n=7)
colors = (style.CATEGORICAL * 2)[: len(nat)]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(nat.index[::-1], nat.values[::-1], color=colors[::-1], height=0.65)
ax.set_xlabel("Nº de alunos")
ax.grid(axis="x")
ax.grid(axis="y", visible=False)
for i, v in enumerate(nat.values[::-1]):
    ax.text(v + 3, i, str(v), va="center", color=style.INK_SECONDARY, fontsize=11)
plt.tight_layout()
savefig(fig, "chart_nationalities.png")

# 3. ASE by grade
ase = an.rate_by_group(df, "ase")
fig, ax = plt.subplots(figsize=(7.5, 4))
ax.bar(ase.index, ase.values, color=style.CATEGORICAL[0], width=0.6)
ax.set_ylabel("% com ASE")
for i, v in enumerate(ase.values):
    ax.text(i, v + 1, f"{v}%", ha="center", color=style.INK_SECONDARY, fontsize=10)
plt.tight_layout()
savefig(fig, "chart_ase_by_grade.png")

# 4. Digital access
pc = an.yn_overall_rate(df, "tem_pc")
net = an.yn_overall_rate(df, "tem_internet")
fig, ax = plt.subplots(figsize=(6.5, 4))
labels = ["Tem PC", "Tem Internet"]
sim_vals = [pc.get("Sim", 0), net.get("Sim", 0)]
nao_vals = [pc.get("Não", 0), net.get("Não", 0)]
x = range(len(labels))
ax.bar(x, sim_vals, color=style.SIM, label="Sim", width=0.5)
ax.bar(x, nao_vals, bottom=sim_vals, color=style.NAO, label="Não", width=0.5)
ax.set_xticks(list(x), labels)
ax.set_ylabel("%")
ax.legend(frameon=False, loc="upper right")
plt.tight_layout()
savefig(fig, "chart_digital_access.png")

# 5. Missing data
missing = an.missing_data_rates(df)
fig, ax = plt.subplots(figsize=(7.5, 5))
missing.plot(kind="barh", ax=ax, color=style.CATEGORICAL[6])
ax.set_xlabel("%")
ax.grid(axis="x")
ax.grid(axis="y", visible=False)
plt.tight_layout()
savefig(fig, "chart_missing_data.png")

print("Charts exported to", ASSETS)
