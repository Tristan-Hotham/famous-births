"""Step 2. All measures: notable births per town and per head, the most famous person born in each town, occupations,
centuries, women's share, and checks on place matching. Writes data/results.json and the CSV files in data/.

Fame: the number of Wikimedia sitelinks of the person's Wikidata item (mostly Wikipedia language editions: a person
with a page in 80 languages scores 80). Page views on English Wikipedia over 60 days (Wikimedia pageviews, via the
MediaWiki API) are a second measure, gathered for the three people with most sitelinks at each birthplace.
Run: python3 code/02_analyse.py
"""
import gzip, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

P = pd.read_pickle(os.path.join(WORK, "people.pkl"))
T = pd.read_pickle(os.path.join(WORK, "towns.pkl"))
PL = pd.read_pickle(os.path.join(WORK, "places.pkl"))
meta = json.load(open(os.path.join(WORK, "meta.json")))
pv = {}
if os.path.exists(PV):
    PVB = json.load(gzip.open(PV)); pv = {int(k): v for k, v in PVB["views"].items()}
    meta["pv_days"] = PVB["days"]; meta["pv_start"], meta["pv_end"] = PVB["window"]; meta["pv_n"] = len(pv)
else:
    meta.update(pv_days=30, pv_start="", pv_end="2026-10-28", pv_n=0)
# page views: total over the window (days without data are counted as missing, not zero)
P["pv"] = P.pid.map(lambda q: pv[q][0] if q in pv else np.nan)
R = {"meta": meta}
r1 = lambda x: round(float(x), 1); r3 = lambda x: round(float(x), 3)


def century(y):
    if pd.isna(y): return "unknown"
    y = int(y)
    return "before 1600" if y < 1600 else "1600s" if y < 1700 else "1700s" if y < 1800 else "1800s" if y < 1900 else "1900s" if y < 2000 else "2000s"
CENTS = ["before 1600", "1600s", "1700s", "1800s", "1900s", "2000s"]
P["cent"] = P.year.map(century)

# ---------- overview and coverage ----------
placed = P[P.tid >= 0]
inbox = P.in_uk_box.fillna(False).astype(bool)
ov = dict(n_people=len(P), n_placed=len(placed), share_placed=r3(len(placed) / len(P)),
          n_coarse=int(P.coarse.sum()), n_nocoord=int(P.nocoord.sum()),
          n_rural=int(((P.tid < 0) & ~P.coarse & ~P.nocoord & inbox).sum()),
          n_outside=int(((P.tid < 0) & ~P.coarse & ~P.nocoord & ~inbox).sum()),
          n_towns=len(T), n_towns_with=int(placed.tid.nunique()), pop_total=int(T["pop"].sum()),
          n_multi_birthplace=meta["n_multi_birthplace"], n_hospital=int(P.hospital.fillna(0).astype(bool).sum()),
          n_female=int((P.sex == "f").sum()), n_male=int((P.sex == "m").sum()), n_sex_other=int((P.sex == "o").sum()), n_sex_missing=int((P.sex == "").sum()),
          n_year_missing=int(P.year.isna().sum()), n_with_enwiki=int((P.enwiki != "").sum()),
          sitelinks_median=int(P.sl.median()), n_sl20=int((P.sl >= 20).sum()), n_sl50=int((P.sl >= 50).sum()),
          rate_uk=r1(len(placed) / T["pop"].sum() * 1e4))
ov["share_female_known"] = r3(ov["n_female"] / (ov["n_female"] + ov["n_male"]))
R["overview"] = ov
R["towns_by_nation"] = {n: dict(n=int(g.shape[0]), pop=int(g["pop"].sum()), src=g.pop_src.iloc[0]) for n, g in T.groupby("nation")}
R["coarse_top"] = P[P.coarse].pl_label.value_counts().head(8).to_dict()

# ---------- per town ----------
g = placed.groupby("tid")
T["n"] = g.size().reindex(T.tid).fillna(0).astype(int).values
T["n_sl20"] = placed[placed.sl >= 20].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values
T["sl_sum"] = g.sl.sum().reindex(T.tid).fillna(0).astype(int).values
T["n_f"] = placed[placed.sex == "f"].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values
T["n_mf"] = placed[placed.sex.isin(["f", "m"])].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values
T["rate"] = T.n / T["pop"] * 1e4
T["n_pre1900"] = placed[placed.year < 1900].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values
T["n_since1950"] = placed[placed.year >= 1950].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values
T["rate_pre1900"] = T.n_pre1900 / T["pop"] * 1e4
T["rate_since1950"] = T.n_since1950 / T["pop"] * 1e4
T["rate20"] = T.n_sl20 / T["pop"] * 1e5
# most famous: most sitelinks (ties: more page views, then earlier birth)
top = placed.assign(pvz=placed.pv.fillna(-1)).sort_values(["sl", "pvz", "year"], ascending=[False, False, True]).groupby("tid").head(1).set_index("tid")
topv = placed.dropna(subset=["pv"]).sort_values(["pv", "sl"], ascending=False).groupby("tid").head(1).set_index("tid")
for c in ["name", "year", "sl", "group", "enwiki", "pid", "pv", "sex"]:
    T["top_" + c] = T.tid.map(top[c])
for c in ["name", "pv", "enwiki", "pid"]:
    T["topv_" + c] = T.tid.map(topv[c])
for gname in GROUPS + ["other"]:
    T["g_" + gname] = placed[placed.group == gname].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values
for c in CENTS + ["unknown"]:
    T["c_" + c] = placed[placed.cent == c].groupby("tid").size().reindex(T.tid).fillna(0).astype(int).values

# ---------- per head ----------
def tlist(df, k=10, cols=("name", "nation", "pop", "n", "rate", "n_pre1900", "rate_pre1900", "n_since1950", "rate_since1950")):
    out = []
    for r in df.head(k).itertuples():
        d = {c: (int(getattr(r, c)) if c in ("pop", "n", "n_sl20", "n_pre1900", "n_since1950") else r1(getattr(r, c)) if c.startswith("rate") else getattr(r, c)) for c in cols}
        d["top"] = r.top_name; out.append(d)
    return out
big = T[T["pop"] >= 50000].sort_values("rate", ascending=False)
mid = T[(T["pop"] >= 10000) & (T["pop"] < 50000)].sort_values("rate", ascending=False)
small = T[(T["pop"] >= 2000) & (T["pop"] < 10000) & (T.n >= 10)].sort_values("rate", ascending=False)
R["per_head"] = dict(big=tlist(big), big_low=tlist(big.sort_values("rate")), mid=tlist(mid), small=tlist(small),
                     n_big=len(big), n_mid=len(mid), big_median=r1(big.rate.median()), mid_median=r1(mid.rate.median()),
                     famous20=tlist(T[T["pop"] >= 20000].sort_values("rate20", ascending=False), 10, ("name", "nation", "pop", "n_sl20", "rate20")))
# the same ranking by era: before 1900 most births were at home; since 1950 most were in hospital
R["per_head_era"] = dict(mid_pre1900=tlist(mid.sort_values("rate_pre1900", ascending=False)), mid_since1950=tlist(mid.sort_values("rate_since1950", ascending=False)),
                         big_pre1900=tlist(big.sort_values("rate_pre1900", ascending=False)), big_since1950=tlist(big.sort_values("rate_since1950", ascending=False)),
                         small_since1950=tlist(small.sort_values("rate_since1950", ascending=False)))
nat_share = (placed.year >= 1950).sum() / placed.year.notna().sum()
hs = T[(T.n >= 50) & (T["pop"] < 50000)].assign(s50=lambda d: d.n_since1950 / d.n)
R["since1950_share"] = dict(national=r3(nat_share), top=[dict(name=r.name, pop=int(r["pop"]) if False else int(getattr(r, "pop")), n=int(r.n), share=r3(r.s50)) for r in hs.sort_values("s50", ascending=False).head(12).itertuples()])
# rank correlation between the two eras for towns of 10,000 to 50,000
R["era_rank_corr"] = round(float(mid[["rate_pre1900", "rate_since1950"]].corr(method="spearman").iloc[0, 1]), 2)
R["by_nation"] = {n: dict(n=int(gg.n.sum()), pop=int(gg["pop"].sum()), rate=r1(gg.n.sum() / gg["pop"].sum() * 1e4),
                          share_women=r3(gg.n_f.sum() / gg.n_mf.sum())) for n, gg in T.groupby("nation")}
lon = T[T.code == "LONDON"].iloc[0]
R["london"] = dict(n=int(lon.n), pop=int(lon["pop"]), rate=r1(lon.rate), share_births=r3(lon.n / len(placed)), share_pop=r3(lon["pop"] / T["pop"].sum()))
# London's share by century of birth
lc = {}
for c in CENTS:
    sub = placed[placed.cent == c]
    lc[c] = dict(n=len(sub), london=r3((sub.tid == lon.tid).mean()))
R["london"]["by_century"] = lc
# correlation of births with population (log-log) for towns of 10k+
m = T[(T["pop"] >= 10000) & (T.n > 0)]
b1, b0 = np.polyfit(np.log(m["pop"]), np.log(m.n), 1)
R["scaling"] = dict(n_towns=len(m), slope=round(float(b1), 2), r=round(float(np.corrcoef(np.log(m["pop"]), np.log(m.n))[0, 1]), 2))

# ---------- most famous per town ----------
fam = T[T.n > 0].sort_values("top_sl", ascending=False)
R["most_famous_overall"] = [dict(name=r.top_name, town=r.name, sl=int(r.top_sl), year=None if pd.isna(r.top_year) else int(r.top_year), group=r.top_group) for r in fam.head(12).itertuples()]
cities = T[T["pop"] >= 150000].sort_values("pop", ascending=False)
R["most_famous_cities"] = [dict(town=r.name, name=r.top_name, sl=int(r.top_sl), year=None if pd.isna(r.top_year) else int(r.top_year), viewed=r.topv_name if isinstance(r.topv_name, str) else None) for r in cities.itertuples()]
tg = T[T.n > 0].top_group.value_counts()
R["top_group_share"] = {k: r3(v / tg.sum()) for k, v in tg.items()}
R["top_group_n"] = {k: int(v) for k, v in tg.items()}
tp = T[T.n > 0]
R["top_women"] = dict(n=int((tp.top_sex == "f").sum()), share=r3((tp.top_sex == "f").mean()))
both = tp.dropna(subset=["topv_name"])
R["pv_agree"] = dict(n=len(both), same=int((both.top_name == both.topv_name).sum()), share=r3((both.top_name == both.topv_name).mean()) if len(both) else 0.0)
# which kinds of people each fame measure picks, in towns where both are available
gp = P.set_index("pid"); bb = both.copy(); bb["g1"] = bb.top_pid.map(gp.group); bb["g2"] = bb.topv_pid.astype(int).map(gp.group)
bb["y1"] = bb.top_pid.map(gp.year); bb["y2"] = bb.topv_pid.astype(int).map(gp.year)
R["fame_compare"] = {k: dict(sport=r3(bb[c].isin(["sport", "footballer"]).mean()), acting=r3((bb[c] == "acting").mean()), science=r3((bb[c] == "science").mean()),
                             since1950=r3((bb[y] >= 1950).mean())) for k, c, y in (("sl", "g1", "y1"), ("pv", "g2", "y2"))}
tc = tp.top_year.map(century).value_counts()
R["top_century"] = {k: int(tc.get(k, 0)) for k in CENTS + ["unknown"]}
# towns whose most famous person was born since 1950
R["top_since1950"] = int((tp.top_year >= 1950).sum())

# ---------- occupations ----------
GN = GROUPS + ["other"]
R["groups"] = {gname: dict(n=int((P.group == gname).sum()), share=r3((P.group == gname).mean()), label=GROUP_LABEL[gname]) for gname in GN}
occ = {}
for gname in GROUPS:
    t = T[(T["pop"] >= 20000)].copy(); t["gr"] = t["g_" + gname] / t["pop"] * 1e5
    t["lq"] = (t["g_" + gname] / t.n.clip(lower=1)) / (len(placed[placed.group == gname]) / len(placed))
    tt = t[t["g_" + gname] >= 5].sort_values("gr", ascending=False)
    occ[gname] = [dict(name=r.name, n=int(getattr(r, "g_" + gname)), rate=r1(r.gr), pop=int(r["pop"]) if False else int(getattr(r, "pop"))) for r in tt.head(5).itertuples()]
R["group_capitals"] = occ
# what the top "other sport" town's sportspeople played: the commonest occupation label among them
_B = json.load(gzip.open(WD)); _lab = _B["occupation_labels"]; del _B
_t = T[T.name == occ["sport"][0]["name"]].tid.iloc[0]; _s = placed[(placed.tid == _t) & (placed.group == "sport")]
_c = pd.Series([_lab.get(str(o), str(o)) for oc in _s.occ for o in (oc or [])]).value_counts()
R["sport_capital_top_occ"] = dict(town=occ["sport"][0]["name"], occupation=_c.index[0], n=int(_c.iloc[0]), of=len(_s))
# signature group per town: largest location quotient among towns with 30+ births
sig = {}
base = {gname: (placed.group == gname).mean() for gname in GROUPS}
for r in T[T.n >= 30].itertuples():
    lqs = {gname: (getattr(r, "g_" + gname) / r.n) / base[gname] for gname in GROUPS if getattr(r, "g_" + gname) >= 5}
    if lqs: k = max(lqs, key=lqs.get); sig[r.tid] = (k, lqs[k])
T["sig_group"] = T.tid.map(lambda t: sig.get(t, (None, None))[0]); T["sig_lq"] = T.tid.map(lambda t: sig.get(t, (None, None))[1])
sg = T.sig_group.value_counts()
R["signature_counts"] = {k: int(v) for k, v in sg.items()}; R["n_signature_towns"] = int(sg.sum())
# group mix by century
R["group_by_century"] = {c: {gname: r3((P[P.cent == c].group == gname).mean()) for gname in GN} for c in CENTS}
R["n_by_century"] = {c: int((P.cent == c).sum()) for c in CENTS + ["unknown"]}

# ---------- women ----------
dec = P[(P.year >= 1700) & P.sex.isin(["f", "m"])].copy(); dec["dec"] = (dec.year // 10 * 10).astype(int)
wd = dec.groupby("dec").agg(n=("sex", "size"), f=("sex", lambda s: (s == "f").sum()))
R["women_by_decade"] = {int(k): dict(n=int(v.n), share=r3(v.f / v.n)) for k, v in wd.iterrows() if k <= 2010}
R["women_by_century"] = {c: r3((P[(P.cent == c) & P.sex.isin(["f", "m"])].sex == "f").mean()) for c in CENTS}
R["women_by_group"] = {gname: r3((P[(P.group == gname) & P.sex.isin(["f", "m"])].sex == "f").mean()) for gname in GN}
wt = T[T.n_mf >= 100].assign(ws=lambda d: d.n_f / d.n_mf).sort_values("ws", ascending=False)
R["women_towns"] = dict(n_towns=len(wt), top=[dict(name=r.name, n=int(r.n_mf), share=r3(r.ws)) for r in wt.head(8).itertuples()],
                        bottom=[dict(name=r.name, n=int(r.n_mf), share=r3(r.ws)) for r in wt.tail(5).itertuples()], median=r3(wt.ws.median()))
w20 = P[(P.sl >= 50) & P.sex.isin(["f", "m"])]
R["women_famous"] = dict(n=len(w20), share=r3((w20.sex == "f").mean()))

# ---------- place matching checks ----------
lab = PL[~PL.coarse & ~PL.nocoord & (PL.pl_label != "")]
dup = lab.groupby("pl_label").pl.nunique(); dupl = set(dup[dup > 1].index)
amb = P[P.pl_label.isin(dupl) & (P.tid >= 0)]
R["ambiguous"] = dict(n_labels=len(dupl), n_people=len(amb), share=r3(len(amb) / len(placed)),
                      examples=[x for x in ["Newport", "Richmond", "Bangor", "Newcastle", "Gillingham", "Boston"] if x in dupl])
# where a birthplace sits outside towns, by era (hospital births grew in the 20th century)
nonc = P[~P.coarse & ~P.nocoord & inbox & P.year.notna()].copy()
nonc["era"] = pd.cut(nonc.year, [-1e9, 1799, 1899, 1949, 1979, 3000], labels=["before 1800", "1800s", "1900 to 1949", "1950 to 1979", "1980 on"])
R["rural_by_era"] = {str(k): dict(n=int(len(v)), share_rural=r3((v.tid < 0).mean())) for k, v in nonc.groupby("era", observed=True)}
R["hospital_items"] = dict(n=ov["n_hospital"], examples=P[P.hospital.fillna(0).astype(bool)].pl_label.value_counts().head(5).to_dict())
big10 = T.sort_values("pop", ascending=False).head(10)
R["big10_share"] = dict(births=r3(big10.n.sum() / len(placed)), pop=r3(big10["pop"].sum() / T["pop"].sum()))

# ---------- save ----------
from urllib.parse import quote
for c in ("top_enwiki", "topv_enwiki"):   # Wikipedia titles, percent-encoded so they are safe as URLs
    T[c] = T[c].map(lambda t: quote(t, safe="()_,'!*:.") if isinstance(t, str) and t else t)
T.to_pickle(os.path.join(WORK, "towns_out.pkl"))
cols = ["code", "name", "nation", "lat", "lon", "pop", "pop_src", "loc_src", "n", "rate", "n_pre1900", "n_since1950", "n_sl20", "n_f", "n_mf", "top_name", "top_year", "top_sl", "top_group", "top_enwiki",
        "topv_name", "topv_pv", "sig_group"] + ["g_" + x for x in GN] + ["c_" + x for x in CENTS + ["unknown"]]
out = T[cols].copy(); out["rate"] = out.rate.round(2); out["lat"] = out.lat.round(4); out["lon"] = out.lon.round(4)
out = out.rename(columns={"n": "notable_births", "rate": "per_10k_residents", "n_sl20": "births_20plus_sitelinks", "n_f": "women", "n_mf": "women_and_men",
                          "top_name": "most_famous", "top_year": "most_famous_born", "top_sl": "most_famous_sitelinks", "top_group": "most_famous_group",
                          "top_enwiki": "most_famous_enwiki", "topv_name": "most_viewed", "topv_pv": "most_viewed_pageviews_60d", "sig_group": "signature_group"})
out.sort_values("pop", ascending=False).to_csv(os.path.join(DATA, "towns.csv"), index=False)
pd.DataFrame([dict(century=c, notable_births=R["n_by_century"][c], women_share=R["women_by_century"][c], london_share=lc[c]["london"],
                   **{"share_" + gname: R["group_by_century"][c][gname] for gname in GN}) for c in CENTS]).to_csv(os.path.join(DATA, "centuries.csv"), index=False)
pd.DataFrame([dict(decade=k, women_and_men=v["n"], women_share=v["share"]) for k, v in R["women_by_decade"].items()]).to_csv(os.path.join(DATA, "women_by_decade.csv"), index=False)
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({k: R[k] for k in ["overview", "per_head", "by_nation", "london", "scaling", "pv_agree", "top_group_share", "women_famous", "ambiguous", "rural_by_era", "big10_share"]}, indent=0, default=str)[:6000])
