"""Step 1. Build the town list with populations, read the Wikidata people, and place each birthplace in a town.

Towns (the denominators):
  England and Wales: ONS built-up areas 2022 (BUA22) with Census 2021 usual residents, as assembled for the
    Beeching cuts project (centre, equal-area radius, population). The 33 London borough built-up areas are merged
    into one London (most Wikidata birthplaces in London are recorded simply as "London").
  Scotland: NRS localities with mid-2020 population estimates, placed by matching the locality name to a Scottish
    built-up area of the same name (centre and radius) or, failing that, to an OS Open Names city, town or village.
  Northern Ireland: NISRA Census 2021 settlements (500 or more residents), placed by matching the name to a Wikidata
    settlement in Northern Ireland.
  Where no area is known the radius comes from the size and area relation fitted on England and Wales.

Birthplaces: each Wikidata birthplace with coordinates goes to the town whose circle (radius plus a margin) contains it,
choosing the town with the smallest distance relative to its radius. Birthplaces that are the UK, its nations,
counties or council areas (without also being a settlement) are too coarse to place and are dropped and counted.
Outputs (temporary): WORK/people.pkl, WORK/towns.pkl, WORK/places.pkl, WORK/meta.json
"""
import csv, gzip, json, os, re, sys
import numpy as np, pandas as pd, openpyxl
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SETTLE = {515, 3957, 532, 486972, 1549591, 18511725, 5084, 1357964, 1021711, 10270157, 1137272, 188509, 123705}


def norm(s):
    s = s.lower().replace("&", "and").replace("st.", "st").replace("'", "")
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^a-z]+", " ", s).strip()


# ---------- towns ----------
G = json.load(open(ONSGEO))
bua = {r["BUA22CD"]: r for r in G["bua22_gb"]}
lsoa_bua = {r["LSOA21CD"]: (r["BUA22CD"], r["LAD22CD"]) for r in json.load(open(LSOABUA)) if r["BUA22CD"]}
popl = {}
for r in csv.DictReader(open(TS001, encoding="utf-8")):
    popl[r["geography code"]] = int(r["Residence type: Total; measures: Value"])
bpop, blad = {}, {}
for l, (b, lad) in lsoa_bua.items():
    bpop[b] = bpop.get(b, 0) + popl.get(l, 0); blad.setdefault(b, lad)
LONDON_LAD = lambda lad: lad.startswith("E09")
T = []
for b, p in bpop.items():
    r = bua.get(b)
    if not r or p <= 0: continue
    T.append(dict(code=b, name=r["BUA22NM"].strip(), nation="Wales" if b.startswith("W") else "England",
                  region="London" if LONDON_LAD(blad[b]) else "", lat=r["LAT"], lon=r["LONG"],
                  r_km=float(np.sqrt(r["Shape__Area"] / np.pi) / 1000), pop=p, pop_src="ONS Census 2021 (LSOAs best-fitted to BUA22)"))
ew = pd.DataFrame(T)
# size and area relation for towns without an area
fit = np.polyfit(np.log(ew["pop"]), np.log(ew["r_km"]), 1)
rad = lambda p: float(np.exp(np.polyval(fit, np.log(p))))
lon_rows = ew[ew.region == "London"]
ew = ew[ew.region != "London"]
london = dict(code="LONDON", name="London", nation="England", region="London", lat=51.5074, lon=-0.1278, r_km=0.0,
              pop=int(lon_rows["pop"].sum()), pop_src="ONS Census 2021 (sum of the %d London borough built-up areas)" % len(lon_rows))
# MSOA population-weighted centroids and their best-fit built-up area (for irregular towns)
msoa_b = {r["MSOA21CD"]: r["BUA22CD"] for r in G["msoa21_bua22_lookup"]}
MS = pd.DataFrame([(r["MSOA21CD"], r["_y"], r["_x"], msoa_b.get(r["MSOA21CD"])) for r in G["msoa21_pwc"]], columns=["msoa", "lat", "lon", "bua"])

# Scotland
sc_bua = {}
for r in G["bua22_gb"]:
    if r["BUA22CD"].startswith("S"):
        sc_bua.setdefault(norm(r["BUA22NM"]), []).append((r["LAT"], r["LONG"], float(np.sqrt(r["Shape__Area"] / np.pi) / 1000)))
osn, osn_all = {}, {}
with open(OSNAMES, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["type"] == "populatedPlace" and r["local_type"] in ("City", "Town", "Village", "Suburban Area"):
            rec = (float(r["lat"]), float(r["lon"]), r["district"] or r["county"], r["local_type"])
            osn_all.setdefault(norm(r["name1"]), []).append(rec)
            if r["country"] == "Scotland": osn.setdefault(norm(r["name1"]), []).append(rec)
wb = openpyxl.load_workbook(NRS, read_only=True)
loc_ca = {}
for i, r in enumerate(wb["Table_1.2"].iter_rows(values_only=True)):
    if i > 3 and r[1]: loc_ca.setdefault(r[1], r[4])
sc, sc_un = [], []
for i, r in enumerate(wb["Table_2.2"].iter_rows(values_only=True)):
    if i <= 3 or not r[1] or r[2] != "All": continue
    nm, code, pop = r[0].strip(), r[1], int(r[3])
    ca = loc_ca.get(code, "")
    keys = [norm(nm)]
    m = re.search(r"\((.*?)\)", nm)
    if m: keys.insert(0, norm(m.group(1)))
    keys.append(norm(re.split(r" and |,", nm)[0]))
    k = next((x for x in keys if x in sc_bua or x in osn), keys[0])
    hit = None
    if k in sc_bua and len(sc_bua[k]) == 1:
        la, lo, rr = sc_bua[k][0]; hit = (la, lo, rr, "Scottish built-up area of the same name (centre and area)")
    elif k in osn:
        c = [x for x in osn[k] if norm(x[2]) == norm(ca)] or (osn[k] if len(osn[k]) == 1 else [])
        if c:
            la, lo = c[0][0], c[0][1]
            hit = (la, lo, rad(pop), "OS Open Names place of the same name in the same council area")
    if hit:
        if "(" in nm: nm = re.search(r"\((.*?)\)", nm).group(1)   # Gaelic name (English name): use the English
        sc.append(dict(code=code, name=nm, nation="Scotland", region="Scotland", lat=hit[0], lon=hit[1], r_km=hit[2], pop=pop,
                       pop_src="NRS mid-2020 locality estimate", loc_src=hit[3]))
    else:
        sc_un.append((nm, pop))

# Northern Ireland
NB = json.load(gzip.open(NI))
nis = {}
for q, lab, la, lo, ty in NB["ni_settlements"]:
    nis.setdefault(norm(lab), []).append((la, lo, ty, q))
    if "," in lab: nis.setdefault(norm(lab.split(",")[0]), []).append((la, lo, ty, q))
TYPE_RANK = {1549591: 0, 515: 0, 3957: 1, 18511725: 1, 532: 2, 486972: 3, 188509: 4, 123705: 4, 5084: 5, 1115575: 6}
wb = openpyxl.load_workbook(NISRA, read_only=True)
ni_pop = {}
for i, r in enumerate(wb["CT0100"].iter_rows(values_only=True)):
    if i <= 5 or not r[1] or not str(r[1]).startswith("N11"): continue
    d = ni_pop.setdefault(r[1], [r[0], 0]); d[1] += int(r[4])
# fallback: a birthplace in the Wikidata people bundle with the same name inside Northern Ireland
_WB = json.load(gzip.open(WD))["places"]
for q, v in _WB.items():
    if v[0] is not None and 54.0 <= v[0] <= 55.35 and -8.2 <= v[1] <= -5.4 and v[2]:
        nis.setdefault(norm(v[2].split(",")[0]), []).append((v[0], v[1], 486972, int(q)))
del _WB
ni, ni_un = [], []
NI_ALIAS = {"belfast metropolitan urban area": "belfast", "metropolitan castlereagh": "castlereagh", "metropolitan lisburn": "lisburn",
            "metropolitan newtownabbey": "newtownabbey", "derry": "derry", "londonderry": "derry"}
for code, (nm, pop) in ni_pop.items():
    if nm.upper() == "ELSEWHERE IN NI": continue
    k = norm(nm.title()); k = NI_ALIAS.get(k, k)
    k = re.sub(r" (city|town|urban area.*)$", "", k); k = k.split("  ")[0]
    if k not in nis and " " in k: k = re.split(r" ", nm.lower().split("/")[0].strip())[0] if "/" in nm else k
    k = norm(k)
    cand = nis.get(k) or nis.get(k.replace("derry", "londonderry")) or (nis.get("derry") if k == "derry" else None)
    if cand:
        c = sorted(cand, key=lambda x: TYPE_RANK.get(x[2], 9))[0]
        nice = re.sub(r" (City|Town|Urban Area.*)$", "", nm.title().replace("Metropolitan ", "")).split(" / ")[0].replace("Londonderry", "Derry/Londonderry") if nm.upper() != "DERRY CITY" else "Derry/Londonderry"
        extra = []
        if k == "craigavon":   # Craigavon Urban Area takes in Lurgan and Portadown
            extra = [sorted(nis[x], key=lambda y: TYPE_RANK.get(y[2], 9))[0][:2] for x in ("lurgan", "portadown") if x in nis]
        ni.append(dict(extra=extra, code=code, name=nice, nation="Northern Ireland", region="Northern Ireland", lat=c[0], lon=c[1], r_km=rad(pop),
                       pop=pop, pop_src="NISRA Census 2021 (settlement)", loc_src="Wikidata settlement of the same name (Q%d)" % c[3]))
    else:
        ni_un.append((nm, pop))

# NISRA lists e.g. LISBURN CITY and METROPOLITAN LISBURN separately: merge settlements that share a cleaned name
_m = {}
for d in ni:
    if d["name"] in _m: _m[d["name"]]["pop"] += d["pop"]; _m[d["name"]]["r_km"] = rad(_m[d["name"]]["pop"]); _m[d["name"]]["code"] += "+" + d["code"]
    else: _m[d["name"]] = d
ni = list(_m.values())
ew["loc_src"] = "ONS BUA22 centre and area; MSOA population-weighted centroids"
ew["extra"] = [[] for _ in range(len(ew))]
sc_df = pd.DataFrame(sc); sc_df["extra"] = [[] for _ in range(len(sc_df))]
# extra centre: an OS Open Names city, town or village of the same name within 5 km of the area centre
# (built-up area centres are geometric centroids, often well away from the historic town centre)
def add_extra(df):
    n = 0
    for i, r in df.iterrows():
        for la, lo, _, kind in osn_all.get(norm(r["name"]), []):
            if km(r.lat, r.lon, la, lo) <= 5.0:
                r.extra.append((la, lo)); n += 1
    return n
print("extra centres", add_extra(ew), add_extra(sc_df))
sc = sc_df.to_dict("records")
towns = pd.concat([ew, pd.DataFrame([london]), pd.DataFrame(sc), pd.DataFrame(ni)], ignore_index=True)
towns.loc[towns.code == "LONDON", "loc_src"] = "Charing Cross; London borough built-up areas merged"
towns["tid"] = towns.index
# drop a bracketed qualifier when the plain name is unique, e.g. "Cambridge (Cambridge)"
_plain = towns.name.str.replace(r"\s*\(.*?\)$", "", regex=True)
_cnt = _plain.value_counts()
_same = towns.name.str.extract(r"^(.*?)\s*\((.*?)\)$")
towns["name"] = np.where((_plain.map(_cnt) == 1) | (_same[0] == _same[1]), _plain, towns.name)
print("towns", towns.groupby("nation").agg(n=("pop", "size"), pop=("pop", "sum")))
print("unmatched Scotland", len(sc_un), sum(p for _, p in sc_un), sorted(sc_un, key=lambda x: -x[1])[:15])
print("unmatched NI", len(ni_un), sum(p for _, p in ni_un), sorted(ni_un, key=lambda x: -x[1])[:15])

# ---------- people and birthplaces ----------
B = json.load(gzip.open(WD))
P = pd.DataFrame(B["rows"], columns=["pid", "pl", "npl", "year", "sex", "sl", "enwiki", "label", "occ"])
places = {int(k): v for k, v in B["places"].items()}
pl = pd.DataFrame([(k, v[0], v[1], v[2], v[3], v[4], v[5]) for k, v in places.items()],
                  columns=["pl", "lat", "lon", "pl_label", "hospital", "p31", "p131"])
pl["coarse"] = pl.apply(lambda r: r.pl not in (84, 23306) and 211690 not in r.p31 and (r.pl in COARSE_QIDS or (bool(set(r.p31) & COARSE_TYPES) and not (set(r.p31) & SETTLE))), axis=1)
pl["nocoord"] = pl.lat.isna()

# assign each birthplace to a town
# (1) circle test: within the town's equal-area radius plus a margin (30 per cent of the radius, at least 1 km);
#     the town with the smallest distance relative to its radius wins; London boroughs count as London;
# (2) England and Wales: otherwise, the built-up area of the nearest MSOA population-weighted centroid within 2 km.
LON_TID = int(towns.index[towns.code == "LONDON"][0])
cand = towns[towns.code != "LONDON"][["tid", "lat", "lon", "r_km", "extra"]].copy()
rows = [cand]
rows.append(lon_rows.assign(tid=LON_TID)[["tid", "lat", "lon", "r_km"]])
ex = [(r.tid, la, lo, r.r_km) for r in cand.itertuples() if isinstance(r.extra, list) for la, lo in r.extra]
if ex: rows.append(pd.DataFrame(ex, columns=["tid", "lat", "lon", "r_km"]))
cand = pd.concat(rows, ignore_index=True)
tree = cKDTree(xy(cand.lat, cand.lon))
code2tid = {c: t for c, t in zip(towns.code, towns.tid)}
for c in lon_rows.code: code2tid[c] = LON_TID
MS["tid"] = MS.bua.map(code2tid)
MSv = MS.dropna(subset=["tid"]).reset_index(drop=True)
mtree = cKDTree(xy(MS.lat, MS.lon))
ok = ~pl.coarse & ~pl.nocoord
pts = xy(pl.lat[ok], pl.lon[ok])
R = cand.r_km.values; TID = cand.tid.values
best_t, how = [], []
for p in pts:
    bt, bs = -1, 9e9
    for i in tree.query_ball_point(p, 30.0):
        d = float(np.hypot(*(tree.data[i] - p))); m = max(1.0, 0.3 * R[i])
        if d <= R[i] + m:
            s_ = d / (R[i] + m)
            if s_ < bs: bt, bs = TID[i], s_
    h = "circle" if bt >= 0 else ""
    if bt < 0:
        d, j = mtree.query(p)
        if d <= 2.0 and pd.notna(MS.tid[j]): bt, h = int(MS.tid[j]), "msoa"
    best_t.append(int(bt)); how.append(h)
pl["tid"] = -1; pl["how"] = ""
pl.loc[ok, "tid"] = best_t; pl.loc[ok, "how"] = how
pl["in_uk_box"] = pl.lat.between(49.8, 61.0) & pl.lon.between(-8.7, 2.0)
pl.to_pickle(os.path.join(WORK, "places.pkl"))

# occupation group
cats = {k: set(v) for k, v in B["occupation_categories"].items()}
# "art" was gathered as everything under "artist", which also holds writers, musicians and actors: keep the rest
cats["art"] = cats["art"] - cats["music"] - cats["acting"] - cats["writing"]
def group(occ):
    """The group with most of the person's occupations; ties go to the earlier group in ORDER."""
    best, bn = "other", 0
    for g in ORDER:
        n = sum(1 for o in (occ or []) if o in cats[g])
        if n > bn: best, bn = g, n
    return best
P["group"] = P.occ.map(group)
P["groups"] = P.occ.map(lambda o: [g for g in GROUPS if set(o or []) & cats[g]])
P = P.merge(pl[["pl", "tid", "hospital", "coarse", "nocoord", "in_uk_box", "lat", "lon", "pl_label"]], on="pl", how="left")
P["name"] = np.where(P.label == "=", P.enwiki.str.replace("_", " "), P.label)
P.loc[P.name.isna() | (P.name == ""), "name"] = P.enwiki.str.replace("_", " ")
P.to_pickle(os.path.join(WORK, "people.pkl"))
towns.to_pickle(os.path.join(WORK, "towns.pkl"))
meta = dict(retrieved=B["retrieved"], n_people=len(P), n_birthplaces=len(pl), n_coarse_people=int(P.coarse.sum()),
            n_nocoord_people=int(P.nocoord.sum()), n_multi_birthplace=int((P.npl > 1).sum()),
            n_in_town=int((P.tid >= 0).sum()), n_hospital_people=int(P.hospital.fillna(0).astype(int).sum()),
            sc_unmatched=len(sc_un), sc_unmatched_pop=sum(p for _, p in sc_un), ni_unmatched=len(ni_un), ni_unmatched_pop=sum(p for _, p in ni_un),
            radius_fit=list(fit))
json.dump(meta, open(os.path.join(WORK, "meta.json"), "w"), indent=1)
print(meta)
