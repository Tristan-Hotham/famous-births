"""Step 3. Compact files for the interactive map in data/page/.
  towns.json    every town or city with its population, notable births (all, before 1900, since 1950), births per head,
                the most famous person born there (most sitelinks) and the most viewed (English Wikipedia, 60 days),
                births by occupation group and century, and women's share
  names.json    cities, towns and villages from OS Open Names (Great Britain) and NISRA settlements (Northern Ireland)
                for map labels and the place search
  outline.json  land and nation borders (simplified) from ONS local authority district boundaries
Only the most famous and the most viewed person per town are named; nothing else about individuals is published.
Run: python3 code/03_page_data.py
"""
import csv, json, os, sys
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

OUT = os.path.join(DATA, "page"); os.makedirs(OUT, exist_ok=True)
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
T = pd.read_pickle(os.path.join(WORK, "towns_out.pkl"))
NAT = ["England", "Scotland", "Wales", "Northern Ireland"]
GN = GROUPS + ["other"]
CENTS = ["before 1600", "1600s", "1700s", "1800s", "1900s", "2000s", "unknown"]
iv = lambda v: None if pd.isna(v) else int(v)
sv = lambda v: v if isinstance(v, str) and v else None
rows = []
for r in T.sort_values("pop", ascending=False).itertuples():
    rows.append([r.name, NAT.index(r.nation), round(r.lat, 4), round(r.lon, 4), int(r.pop), int(r.n), int(r.n_pre1900), int(r.n_since1950), int(r.n_f), int(r.n_mf),
                 sv(r.top_name), iv(r.top_year), iv(r.top_sl), GN.index(r.top_group) if isinstance(r.top_group, str) else None, sv(r.top_enwiki),
                 sv(r.topv_name), iv(r.topv_pv), sv(r.topv_enwiki) if hasattr(r, "topv_enwiki") else None,
                 [int(getattr(r, "g_" + g)) for g in GN], [int(getattr(r, "c_" + c.replace(" ", "_"))) if False else int(T.at[r.Index, "c_" + c]) for c in CENTS],
                 GN.index(r.sig_group) if isinstance(r.sig_group, str) else None, int(r.n_sl20)])
cols = ["name", "nation", "lat", "lon", "pop", "n", "pre1900", "since1950", "women", "women_men", "top", "top_year", "top_sl", "top_group", "top_wiki",
        "viewed", "viewed_pv", "viewed_wiki", "groups", "centuries", "sig", "n_sl20"]
json.dump(dict(cols=cols, nations=NAT, groups=GN, centuries=CENTS, rows=rows), open(os.path.join(OUT, "towns.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# labels: OS Open Names cities, towns and villages; NISRA settlement places for Northern Ireland
MAJOR = {"London", "Birmingham", "Manchester", "Glasgow", "Edinburgh", "Cardiff", "Leeds", "Newcastle upon Tyne", "Bristol", "Liverpool", "Sheffield",
         "Aberdeen", "Inverness", "Norwich", "Plymouth", "Southampton", "Nottingham", "Leicester", "York", "Dundee", "Swansea", "Kingston upon Hull",
         "Carlisle", "Exeter", "Cambridge", "Oxford", "Lincoln", "Truro", "Belfast", "Derry/Londonderry"}
lab = []
with open(OSNAMES, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["type"] == "populatedPlace" and r["local_type"] in ("City", "Town", "Village"):
            k = {"City": 4, "Town": 3, "Village": 1}[r["local_type"]]
            if r["name1"] in MAJOR and k >= 3: k = 5
            lab.append((r["name1"], float(r["lat"]), float(r["lon"]), k, r["county"] or r["district"]))
for r in T[T.nation == "Northern Ireland"].itertuples():
    k = 5 if r.name in MAJOR else 4 if r.pop >= 20000 else 3 if r.pop >= 4000 else 1
    lab.append((r.name, r.lat, r.lon, k, "Northern Ireland"))
lab = pd.DataFrame(lab, columns=["n", "la", "lo", "r", "a"]).drop_duplicates(["n", "a"])
json.dump(dict(n=lab.n.tolist(), la=(lab.la * 1e4).round().astype(int).tolist(), lo=(lab.lo * 1e4).round().astype(int).tolist(), r=lab.r.tolist(),
               a=[a.split(" - ")[-1] for a in lab.a]), open(os.path.join(OUT, "names.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# outline
def rnd(geom, tol):
    return shapely.set_precision(shapely.simplify(geom, tol, preserve_topology=True), 0.0001)
lj = json.load(open(LTLA)); parts = {"E": [], "W": [], "S": [], "N": []}
for f in lj["features"]:
    p = f["properties"]
    if p.get("end") is None: parts[p["areacd"][0]].append(shapely.make_valid(shape(f["geometry"])).buffer(0))
nat = {k: unary_union(v) for k, v in parts.items()}
land = unary_union(list(nat.values()))
borders = unary_union([nat["E"].boundary.intersection(nat["W"].buffer(0.002)), nat["E"].boundary.intersection(nat["S"].buffer(0.002))])
json.dump(dict(land=mapping(rnd(land, 0.004)), borders=mapping(rnd(borders, 0.002))), open(os.path.join(OUT, "outline.json"), "w"), separators=(",", ":"))
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)))
