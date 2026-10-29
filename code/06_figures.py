"""Step 6. Static figures for the blog (release/blog/b_*.png, 1520 px wide) and the paper (release/paper/f_*.png),
from data/ files only. Fonts: FONT_DIR as in step 5 (falls back to DejaVu).
Run: FONT_DIR=/path/to/fonts python3 code/06_figures.py
"""
import json, math, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FD = os.environ.get("FONT_DIR", "")
SER, MONO, DISP = "DejaVu Serif", "DejaVu Sans Mono", "DejaVu Serif"
if FD:
    for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "FrauncesVar.ttf"):
        if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
    SER, MONO, DISP = "Source Serif 4", "IBM Plex Mono", "Fraunces"
BG, FG, MUT, RULE, LAND, ACC, GOLD = "#F7F3EC", "#1E1B18", "#615A51", "#DDD4C4", "#E7DFD0", "#A8322B", "#B8862B"
Q = ["#F1E3B8", "#E6BC6E", "#D58A45", "#B5452F", "#6E2140"]
GCOL = {"footballer": "#2E7D4F", "sport": "#45A090", "politics": "#2C4A7C", "science": "#4F8FC0", "writing": "#7A3E7A", "acting": "#B5372E",
        "music": "#D9822B", "art": "#C9A227", "military": "#6B6B2E", "religion": "#8A5A3C", "business": "#5E6B78", "other": "#A39E95"}
GSHORT = {"footballer": "Footballers", "sport": "Other sport", "politics": "Politics and law", "science": "Science and scholarship", "writing": "Writing",
          "acting": "Acting", "music": "Music", "art": "Visual arts", "military": "Military", "religion": "Religion", "business": "Business", "other": "Other"}
plt.rcParams.update({"font.family": MONO, "font.size": 15, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "axes.spines.top": False, "axes.spines.right": False})
OUT = os.path.join(ROOT, "release", "blog"); os.makedirs(OUT, exist_ok=True)
PAP = os.path.join(ROOT, "release", "paper"); os.makedirs(PAP, exist_ok=True)
R = json.load(open(os.path.join(DATA, "results.json")))
TJ = json.load(open(os.path.join(DATA, "page", "towns.json"))); C = {c: i for i, c in enumerate(TJ["cols"])}
OL = json.load(open(os.path.join(DATA, "page", "outline.json")))
K = math.cos(math.radians(54.5))
GN = GROUPS + ["other"]


def save(fig, name, paper=None):
    fig.savefig(os.path.join(OUT, name), dpi=152); 
    if paper: fig.savefig(os.path.join(PAP, paper), dpi=110)
    plt.close(fig); print(name)


def land(ax, lw=.6):
    g = OL["land"]
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = np.array(poly[0]); ax.add_patch(Polygon(np.c_[ring[:, 0] * K, ring[:, 1]], closed=True, fc=LAND, ec="#CBBFAB", lw=lw, zorder=1))


rows = [r for r in TJ["rows"] if r[C["n"]]]
br = R["page"]["breaks"]["all"]
qc = lambda v: Q[sum(v >= b for b in br)]

# 1. the map: births per head, with the most famous person in the best-known places
fig = plt.figure(figsize=(10, 13.2)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_aspect("equal"); ax.axis("off")
land(ax)
rs = sorted(rows, key=lambda r: -r[C["n"]])
ax.scatter([r[C["lon"]] * K for r in rs], [r[C["lat"]] for r in rs], s=[min(1400, max(3, .9 * r[C["n"]])) for r in rs],
           c=[qc(r[C["n"]] / r[C["pop"]] * 1e4) for r in rs], edgecolors=BG, linewidths=.4, alpha=.9, zorder=3)
ax.set_xlim(-8.3 * K, 2.0 * K); ax.set_ylim(49.85, 60.95)
# labels: most sitelinks first, skipping overlaps
lab = sorted(rows, key=lambda r: -(r[C["top_sl"]] or 0)); boxes = []; n = 0
fig.canvas.draw(); tr = ax.transData
for r in lab:
    x, y = tr.transform((r[C["lon"]] * K, r[C["lat"]])); w = max(len(r[C["top"]]) * 8.3, len(r[C["name"]]) * 6.8); bx = (x - w / 2, y - 34, x + w / 2, y - 4)
    if any(bx[0] < b[2] and bx[2] > b[0] and bx[1] < b[3] and bx[3] > b[1] for b in boxes): continue
    if bx[0] < 5 or bx[2] > fig.bbox.width - 5 or bx[1] < 8: continue
    boxes.append(bx)
    ax.annotate(r[C["top"]], (r[C["lon"]] * K, r[C["lat"]]), xytext=(0, -12), textcoords="offset points", ha="center", va="top", fontsize=11.5, family=SER, weight="semibold", color=FG, zorder=5,
                path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=3, foreground=BG)])
    ax.annotate(r[C["name"]], (r[C["lon"]] * K, r[C["lat"]]), xytext=(0, -26), textcoords="offset points", ha="center", va="top", fontsize=8.5, color=MUT, zorder=5,
                path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=3, foreground=BG)])
    n += 1
    if n >= 34: break
lx, ly = .64, .965
fig.text(lx, ly, "Notable births per 10,000\nresidents today", fontsize=13, color=FG, va="top")
for i, c in enumerate(Q):
    fig.patches.append(plt.Rectangle((lx + i * .062, ly - .062), .062, .014, color=c, transform=fig.transFigure, figure=fig))
for i, b in enumerate(br):
    fig.text(lx + (i + 1) * .062, ly - .07, f"{b:g}", fontsize=11, color=MUT, ha="center", va="top")
fig.text(lx, ly - .095, "Circle area: number of notable births.\nNames: the person with most\nWikipedia language editions.", fontsize=11, color=MUT, va="top")
save(fig, "b_map.png", "f_map.png")

# 2. per head ranking: towns of 10,000 to 50,000, all time against born since 1950 and before 1900
fig, axs = plt.subplots(1, 2, figsize=(10, 7.2), gridspec_kw=dict(wspace=.75))
for ax, key, era, col, title in ((axs[0], "mid_pre1900", "rate_pre1900", Q[1], "Born before 1900"), (axs[1], "mid_since1950", "rate_since1950", Q[3], "Born since 1950")):
    L = R["per_head_era"][key][:10][::-1]
    ax.barh(range(len(L)), [x[era] for x in L], color=col, height=.68)
    ax.set_yticks(range(len(L))); ax.set_yticklabels([x["name"] for x in L], fontsize=13.5, family=SER)
    for i, x in enumerate(L): ax.text(x[era] + 1, i, f'{x[era]:.0f}', va="center", fontsize=12)
    ax.set_title(title, loc="left", fontsize=16, family=SER, weight="semibold", color=FG, pad=10)
    ax.set_xlabel("per 10,000 residents", fontsize=12); ax.tick_params(axis="y", length=0); ax.set_xlim(0, max(x[era] for x in L) * 1.2)
fig.subplots_adjust(left=.2, right=.97, top=.92, bottom=.1)
save(fig, "b_rank.png", "f_rank.png")

# 3. the hospital effect: births outside counted towns by era
fig, ax = plt.subplots(figsize=(10, 5.2))
rb = R["rural_by_era"]; ks = list(rb)
ax.bar(range(len(ks)), [rb[k]["share_rural"] * 100 for k in ks], color=Q[2], width=.62)
for i, k in enumerate(ks): ax.text(i, rb[k]["share_rural"] * 100 + .4, f'{rb[k]["share_rural"] * 100:.1f}%', ha="center", fontsize=13)
ax.set_xticks(range(len(ks))); ax.set_xticklabels([k.replace("1900 to 1949", "1900 to\n1949").replace("1950 to 1979", "1950 to\n1979") for k in ks], fontsize=13)
ax.set_ylabel("% born outside any counted town", fontsize=13); ax.set_ylim(0, max(rb[k]["share_rural"] for k in ks) * 118)
fig.subplots_adjust(left=.1, right=.98, top=.95, bottom=.18)
save(fig, "b_rural.png", "f_rural.png")

# 4. what they did, by century
fig, ax = plt.subplots(figsize=(10, 6.6))
cents = ["before 1600", "1600s", "1700s", "1800s", "1900s", "2000s"]
gbc = R["group_by_century"]
for j, c in enumerate(cents):
    acc = 0
    for g in GN:
        v = gbc[c][g]; ax.barh(j, v * 100, left=acc * 100, color=GCOL[g], height=.7, edgecolor=BG, linewidth=.6)
        if v >= .07: ax.text(acc * 100 + v * 50, j, f"{v * 100:.0f}", ha="center", va="center", fontsize=11, color="white")
        acc += v
ax.set_yticks(range(len(cents))); ax.set_yticklabels([f"{c}\n({R['n_by_century'][c]:,})" for c in cents], fontsize=12); ax.invert_yaxis()
ax.set_xlim(0, 100); ax.set_xlabel("% of each century's notable births", fontsize=12); ax.tick_params(axis="y", length=0)
hs = [plt.Rectangle((0, 0), 1, 1, color=GCOL[g]) for g in GN]
ax.legend(hs, [GSHORT[g] for g in GN], ncol=4, loc="upper center", bbox_to_anchor=(.45, -.13), frameon=False, fontsize=11.5, handlelength=1, columnspacing=1.2)
fig.subplots_adjust(left=.17, right=.98, top=.97, bottom=.3)
save(fig, "b_groups.png", "f_groups.png")

# 5. women's share by decade
fig, ax = plt.subplots(figsize=(10, 5.2))
wd = [(int(k), v["share"], v["n"]) for k, v in R["women_by_decade"].items() if v["n"] >= 200]
ax.plot([d for d, _, _ in wd], [s * 100 for _, s, _ in wd], color=ACC, lw=2.8, marker="o", ms=5)
ax.set_ylim(0, 40); ax.set_xlim(1695, 2015); ax.grid(axis="y", color=RULE); ax.set_ylabel("% women", fontsize=13)
ax.set_xlabel("decade of birth", fontsize=12)
fig.subplots_adjust(left=.09, right=.98, top=.96, bottom=.16)
save(fig, "b_women.png", "f_women.png")

# 6. scaling: notable births against population (paper and blog)
fig, ax = plt.subplots(figsize=(10, 6.4))
m = [r for r in rows if r[C["pop"]] >= 10000]
ax.scatter([r[C["pop"]] for r in m], [r[C["n"]] for r in m], s=14, color=Q[3], alpha=.45, edgecolors="none")
ax.set_xscale("log"); ax.set_yscale("log"); ax.grid(color=RULE, lw=.6)
xs = np.array([1e4, 9e6]); sl = R["scaling"]["slope"]
lp = np.log([r[C["pop"]] for r in m]); ln = np.log([r[C["n"]] for r in m]); b0 = np.mean(ln) - sl * np.mean(lp)
ax.plot(xs, np.exp(b0) * xs ** sl, color=FG, lw=1.4, ls="--")
for nm in ["London", "Glasgow", "Edinburgh", "Liverpool", "Birmingham", "Milton Keynes", "Bellshill", "Oxford", "Corby", "Carmarthen"]:
    r = next((r for r in m if r[C["name"]] == nm), None)
    if r: ax.annotate(nm, (r[C["pop"]], r[C["n"]]), xytext=(5, 3), textcoords="offset points", fontsize=11.5, family=SER)
ax.set_xlabel("residents today (log scale)", fontsize=12); ax.set_ylabel("notable births (log scale)", fontsize=12)
fig.subplots_adjust(left=.11, right=.97, top=.96, bottom=.12)
save(fig, "b_scaling.png", "f_scaling.png")
