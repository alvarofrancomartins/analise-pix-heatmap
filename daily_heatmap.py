"""Daily Pix heatmap: one cell per calendar day, count or value.

Each cell (day-of-month x month) shows either the number of Pix operations
settled in the SPI, or their total value, on that calendar date, for one
calendar year.

Script autocontido: lê data/pix_liquidados_atual.csv e escreve em output/.

Note: counts Pix settled in the SPI; it does not include on-us transactions.
Units: 'Total' is in THOUSANDS of R$ (multiplied by 1000 here). The colour scale
is linear, normalized to the busiest/biggest day of the year (not log).

Usage: python daily_heatmap.py [year] [count|value]
  year   defaults to the most recent complete year
  metric defaults to 'count'
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# --- CLI: [year] [metric] -------------------------------------------------
args = [a for a in sys.argv[1:]]
metric = "count"
if args and args[-1].lower() in ("count", "value", "quantidade", "total", "valor"):
    metric = "value" if args[-1].lower() in ("value", "total", "valor") else "count"
    args = args[:-1]
year_arg = int(args[0]) if args else None

daily = pd.read_csv(HERE / "data" / "pix_liquidados_atual.csv", parse_dates=["Data"])

if year_arg is not None:
    YEAR = year_arg
else:
    # Most recent year with all 12 months present (skip a partial current year).
    YEAR = daily.Data.dt.year.max()
    if daily[daily.Data.dt.year == YEAR].Data.dt.month.nunique() < 12:
        YEAR -= 1

sub = daily[daily["Data"].dt.year == YEAR]
if sub.empty:
    raise SystemExit(f"no SPI data for year {YEAR}")

if metric == "value":
    vals = sub["Total"] * 1000.0          # Total está em milhares de R$ -> R$
    div = 1e9
    noun = "valor (bilhões de R$)"
    lo, hi = "menor valor", "maior valor"
    fname = f"pix_daily_heatmap_value_{YEAR}.png"
else:
    vals = sub["Quantidade"]
    div = 1e6
    noun = "quantidade (milhões de Pix)"
    lo, hi = "menos Pix", "mais Pix"
    fname = f"pix_daily_heatmap_{YEAR}.png"

matrix = np.full((31, 12), np.nan)
for d, v in zip(sub["Data"], vals):
    matrix[d.day - 1, d.month - 1] = v

df = pd.DataFrame(matrix, index=range(1, 32), columns=MONTHS)

fig, ax = plt.subplots(figsize=(8, 10))
sns.heatmap(df, cmap="magma_r", linewidths=0,
            mask=df.isna(), ax=ax, cbar=False)
ax.set_ylabel("")
ax.set_xlabel("")
ax.xaxis.tick_top()
ax.tick_params(axis="x", rotation=0, bottom=False, top=True,
               labelbottom=False, labeltop=True, length=0, labelsize=14)
ax.tick_params(axis="y", rotation=0, length=0, labelsize=14)

cmap = plt.get_cmap("magma_r")
vmax = np.nanmax(df.values)
for day in range(1, 32):
    for col, month in enumerate(MONTHS):
        v = df.loc[day, month]
        if not np.isnan(v):
            r_, g_, b_, _ = cmap(v / vmax)
            luminance = 0.299 * r_ + 0.587 * g_ + 0.114 * b_
            color = "white" if luminance < 0.5 else "#2d2d2d"
            ax.text(col + 0.5, day - 0.5, f"{v / div:.0f}",
                    ha="center", va="center", color=color, fontsize=11)

# Horizontal gradient legend below the heatmap.
fig.subplots_adjust(bottom=0.18, top=0.84)
bbox = ax.get_position()
gap = 0.03
grad_h = 0.02
grad_bottom = bbox.y0 - gap - grad_h
legend_ax = fig.add_axes([bbox.x0, grad_bottom, bbox.width, grad_h])
grad = np.linspace(0, 1, 256).reshape(1, -1)
legend_ax.imshow(grad, aspect="auto", cmap="magma_r")
legend_ax.set_xticks([])
legend_ax.set_yticks([])
for spine in legend_ax.spines.values():
    spine.set_visible(False)

label_y = grad_bottom - 0.005
fig.text(bbox.x0, label_y, lo, ha="left", va="top", fontsize=16)
fig.text(bbox.x1, label_y, hi, ha="right", va="top", fontsize=16)

fig.suptitle(f"Pix por dia em {YEAR}: {noun}",
             fontsize=20, fontweight="bold", y=0.92)

out_path = HERE / "output" / fname
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"wrote {out_path} ({len(sub)} days, metric={metric})")
