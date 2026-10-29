"""r/dataisbeautiful collage: who was born in your town? Run from anywhere: python3 reddit/collage.py
Reads data/results.json and data/page/ only. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono)."""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
F = os.environ.get("FONT_DIR", "/dev/shm/fbfonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    if os.path.exists(os.path.join(F, f)): fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, EDGE, ACC, GOLD = "#F8F2E7", "#1E1B18", "#6A6258", "#E9E0CF", "#CDBFA8", "#A8322B", "#B8862B"
Q = ["#F1E3B8", "#E6BC6E", "#D58A45", "#B5452F", "#6E2140"]
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
TJ = json.load(open(os.path.join(ROOT, "data", "page", "towns.json"))); C = {c: i for i, c in enumerate(TJ["cols"])}
OL = json.load(open(os.path.join(ROOT, "data", "page", "outline.json")))
K = math.cos(math.radians(54.5))
rows = [r for r in TJ["rows"] if r[C["n"]]]
br = R["page"]["breaks"]["all"]; qc = lambda v: Q[sum(v >= b for b in br)]
halo = [pe.withStroke(linewidth=3.2, foreground=BG)]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(.04, .968, "Who was born in your town?", fontproperties=DISP, fontsize=50, color=FG, va="top")
ov = R["overview"]
fig.text(.04, .918, f"{ov['n_placed']:,} notable people in Wikidata, matched to the {ov['n_towns_with']:,} UK towns and cities they were born in.\nNames: the person from each place with the most Wikipedia language editions.", family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.38)

# hero map
ax = fig.add_axes([.0, .265, .6, .625]); ax.set_aspect("equal"); ax.axis("off")
g = OL["land"]
for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
    ring = np.array(poly[0]); ax.add_patch(Polygon(np.c_[ring[:, 0] * K, ring[:, 1]], closed=True, fc=LAND, ec=EDGE, lw=.5, zorder=1))
rs = sorted(rows, key=lambda r: -r[C["n"]])
ax.scatter([r[C["lon"]] * K for r in rs], [r[C["lat"]] for r in rs], s=[min(700, max(2, .5 * r[C["n"]])) for r in rs],
           c=[qc(r[C["n"]] / r[C["pop"]] * 1e4) for r in rs], edgecolors=BG, linewidths=.35, alpha=.92, zorder=3)
ax.set_xlim(-8.25 * K, 1.85 * K); ax.set_ylim(49.85, 59.4)
fig.canvas.draw(); tr = ax.transData; boxes = []; n = 0
for r in sorted(rows, key=lambda r: -(r[C["top_sl"]] or 0)):
    x, y = tr.transform((r[C["lon"]] * K, r[C["lat"]]))
    if not (ax.get_window_extent().x0 + 40 < x < ax.get_window_extent().x1 - 40 and ax.get_window_extent().y0 + 110 < y < ax.get_window_extent().y1 - 10): continue
    big = n < 6; fs = 15 if big else 11.5
    w = max(len(r[C["top"]]) * fs * 1.25, len(r[C["name"]]) * 15) / 2 + 10; bx = (x - w, y - (fs * 2.9 + 50), x + w, y - 10)
    if any(bx[0] < b[2] and bx[2] > b[0] and bx[1] < b[3] and bx[3] > b[1] for b in boxes): continue
    boxes.append(bx)
    ax.annotate(r[C["top"]], (r[C["lon"]] * K, r[C["lat"]]), xytext=(0, -6), textcoords="offset points", ha="center", va="top", fontsize=fs, family=SER, weight="semibold", color=FG, zorder=6, path_effects=halo)
    ax.annotate(r[C["name"]], (r[C["lon"]] * K, r[C["lat"]]), xytext=(0, -7 - fs * 1.25), textcoords="offset points", ha="center", va="top", fontsize=9.5, family=MONO, color=MUT, zorder=6, path_effects=halo)
    n += 1
    if n >= 30: break
# legend
lx, ly = .62, .275
fig.text(lx, ly + .03, "Notable births per 10,000 residents today", family=MONO, fontsize=10.5, color=FG)
for i, c in enumerate(Q): fig.patches.append(plt.Rectangle((lx + i * .05, ly + .012), .05, .012, color=c, transform=fig.transFigure, figure=fig))
for i, b in enumerate(br): fig.text(lx + (i + 1) * .05, ly + .006, f"{b:g}", family=MONO, fontsize=9.5, color=MUT, ha="center", va="top")
fig.text(lx + .27, ly + .018, "circle area:\nnotable births", family=MONO, fontsize=9.5, color=MUT, va="center")

# headline numbers
bell_post = round(R["page"]["bellshill_post"] * 100)
nums = [(f"{round(R['london']['share_births'] * 100)}%", ACC, f"of the births are in London, home to\n{round(R['london']['share_pop'] * 100)}% of the people in these towns today."),
        (f"x{R['page']['scaling_factor']:.1f}", GOLD, "notable births when a town's population\ndoubles: bigger places punch harder."),
        (f"{bell_post}%", ACC, f"of Bellshill's {R['page']['bellshill_n']} notable births are since 1950.\nIn the hospital era, born in a town often\nmeans born in its maternity ward."),
        (f"{round(R['women_by_century']['1700s'] * 100)}% to {round(R['women_by_century']['2000s'] * 100)}%", GOLD, "women's share of notable births, born\nin the 1700s against born since 2000.")]
for i, (big, col, small) in enumerate(nums):
    y = .855 - i * .148
    fig.text(.62, y, big, fontproperties=DISP, fontsize=40, color=col, va="top")
    fig.text(.62, y - .052, small, family=SER, fontsize=13, color=FG, va="top", linespacing=1.3)

# small multiples
pre = R["per_head_era"]["mid_pre1900"][:6]; post = R["per_head_era"]["mid_since1950"][:6]
for j, (L, key, col, title) in enumerate(((pre, "rate_pre1900", Q[1], "Born before 1900"), (post, "rate_since1950", Q[3], "Born since 1950"))):
    a = fig.add_axes([.09 + j * .3, .095, .17, .12], facecolor=BG)
    vals = [x[key] for x in L][::-1]; a.barh(range(len(vals)), vals, color=col, height=.7)
    a.set_yticks(range(len(vals))); a.set_yticklabels([x["name"] for x in L][::-1], family=SER, fontsize=11)
    for i, v in enumerate(vals): a.text(v + max(vals) * .03, i, f"{v:.0f}", va="center", family=MONO, fontsize=9.5, color=FG)
    a.set_xlim(0, max(vals) * 1.25); a.set_xticks([]); [s.set_visible(False) for s in a.spines.values()]; a.tick_params(length=0)
    fig.text(.01 + j * .3, .235, title, family=SER, weight="semibold", fontsize=13.5, color=FG)
    fig.text(.01 + j * .3, .222, "towns of 10k to 50k, births per 10,000", family=MONO, fontsize=9.5, color=MUT)
# women line
a = fig.add_axes([.67, .1, .3, .115], facecolor=BG)
wd = [(int(k), v["share"]) for k, v in R["women_by_decade"].items() if v["n"] >= 200]
a.plot([d for d, _ in wd], [s * 100 for _, s in wd], color=ACC, lw=2.2)
a.set_ylim(0, 35); a.set_xlim(1700, 2015); a.set_yticks([0, 10, 20, 30]); a.set_yticklabels(["0%", "10%", "20%", "30%"], family=MONO, fontsize=9.5)
a.set_xticks([1700, 1800, 1900, 2000]); a.set_xticklabels(["1700s", "1800s", "1900s", "2000s"], family=MONO, fontsize=9.5)
for s in ("top", "right"): a.spines[s].set_visible(False)
a.tick_params(colors=MUT); [a.spines[s].set_color(MUT) for s in ("left", "bottom")]
fig.text(.62, .235, "Women's share, by decade of birth", family=SER, weight="semibold", fontsize=13.5, color=FG)
fig.text(.62, .222, "notable births with a recorded sex", family=MONO, fontsize=9.5, color=MUT)

fig.text(.04, .078, f"Caveats: notable people only (Wikidata), so the sample leans to men, sport and the professions. Births in every century are set\nagainst today's population. {ov['n_coarse']:,} people born simply in 'England', a county or similar are not placed.",
         family=MONO, fontsize=8.6, color=MUT, va="top", linespacing=1.25)
fig.text(.04, .047, "Sources: Wikidata (CC0) via QLever, 29 Oct 2026; Wikimedia page views; ONS built-up areas and Census 2021; NRS localities,\nmid-2020; NISRA Census 2021 settlements; OS Open Names (all OGL v3). Population figures: ONS, NRS, NISRA.",
         family=MONO, fontsize=8.6, color=MUT, va="top", linespacing=1.25)
fig.text(.04, .016, "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/famous-births", family=MONO, fontsize=8.6, color=FG, va="top")
fig.savefig(os.path.join(HERE, "born_here.png"), dpi=200, facecolor=BG)
print("born_here.png")
