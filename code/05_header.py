"""Step 5. Render header.png (1200x630 social card) with Playwright Chromium.

A map of UK towns as circles sized by notable births, with the most famous person born in some of the larger places.
Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf
(from github.com/google/fonts); otherwise system serif is used.
Run: FONT_DIR=/path/to/fonts python3 code/05_header.py
"""
import json, math, os, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = json.load(open(os.path.join(DATA, "results.json")))
TJ = json.load(open(os.path.join(DATA, "page", "towns.json"))); C = {c: i for i, c in enumerate(TJ["cols"])}
OL = json.load(open(os.path.join(DATA, "page", "outline.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -8.3 * K, 1.9 * K, -60.9, -49.85
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)
pr = lambda lat, lon: ((lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh)
land = ""
g = OL["land"]
for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
    ring = poly[0]
    if len(ring) < 12: continue
    land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
rows = sorted([r for r in TJ["rows"] if r[C["n"]]], key=lambda r: -r[C["n"]])
br = R["page"]["breaks"]["all"]; Q = ["#F1E3B8", "#E6BC6E", "#D58A45", "#B5452F", "#6E2140"]
qc = lambda v: Q[sum(v >= b for b in br)]
dots = "".join(f'<circle cx="{pr(r[C["lat"]], r[C["lon"]])[0]:.1f}" cy="{pr(r[C["lat"]], r[C["lon"]])[1]:.1f}" r="{min(26, max(1.4, .2 * math.sqrt(r[C["n"]]))):.1f}" fill="{qc(r[C["n"]] / r[C["pop"]] * 1e4)}" fill-opacity=".85" stroke="#F7F3EC" stroke-width=".5"/>' for r in rows)
LAB = {"Liverpool": (-14, 0, "end"), "Stratford-upon-Avon": (0, 14, "middle"), "Kirkcaldy and Dysart": (14, 0, "start"), "Belfast": (0, 18, "middle"), "Shrewsbury": (-12, 4, "end"), "Portsmouth": (0, 18, "middle")}
lab = ""
for nm, (dx, dy, an) in LAB.items():
    r = next(r for r in rows if r[C["name"]] == nm); x, y = pr(r[C["lat"]], r[C["lon"]])
    lab += f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{an}" class="w">{r[C["top"]]}</text><text x="{x + dx:.1f}" y="{y + dy + 12:.1f}" text-anchor="{an}" class="t">{nm}</text>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
ov = R["overview"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 45%,#FFFDF8 0%,#F7F3EC 52%,#EBE2D2 100%);color:#1E1B18;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:58px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#615A51;display:flex;gap:12px;align-items:center}}
.k b{{background:#1E1B18;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:96px;margin:0;font:900 86px/.94 Fraunces,Georgia,serif;letter-spacing:-.02em;width:700px}}
h1 em{{font-style:normal;color:#A8322B}}
p{{position:absolute;left:70px;top:330px;width:560px;margin:0;font-size:25px;line-height:1.36}}
p b{{color:#A8322B}}
.f{{position:absolute;left:70px;bottom:44px;font:400 15px/1 'IBM Plex Mono',monospace;color:#615A51}}
svg{{position:absolute;right:24px;top:10px}}
.w{{font:700 13px Fraunces,Georgia,serif;fill:#1E1B18;paint-order:stroke;stroke:#F7F3EC;stroke-width:3px}}
.t{{font:400 10px 'IBM Plex Mono',monospace;fill:#615A51;paint-order:stroke;stroke:#F7F3EC;stroke-width:3px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Notable births · United Kingdom</span></div>
<h1>Who was <em>born</em> in your town?</h1>
<p><b>{ov['n_placed']:,}</b> notable people in Wikidata, matched to {ov['n_towns_with']:,} towns and cities: the most famous person born in each, and the places that punch above their weight.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E7DFD0" stroke="#CBBFAB" stroke-width="1"/>{dots}{lab}</svg>
</body></html>"""
tmp = os.path.join(WORK, "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
