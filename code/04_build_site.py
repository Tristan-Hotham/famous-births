"""Step 4. Fill code/page_template.html with numbers from data/results.json to make index.html.

A few page-level numbers derived from results.json are stored under "page" first, so that results.json holds every
number on the page. Facts the text states in words are checked against the data here.
Run: python3 code/04_build_site.py
"""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RP = os.path.join(DATA, "results.json")
R = json.load(open(RP))
T = pd.read_pickle(os.path.join(WORK, "towns_out.pkl"))
GN = GROUPS + ["other"]
GROUP_SHORT = {"footballer": "Footballers", "sport": "Other sport", "politics": "Politics and law", "science": "Science", "writing": "Writing",
               "acting": "Acting", "music": "Music", "art": "Visual arts", "military": "Military", "religion": "Religion", "business": "Business", "other": "Other"}
GROUP_COL = {"footballer": "#2E7D4F", "sport": "#45A090", "politics": "#2C4A7C", "science": "#4F8FC0", "writing": "#7A3E7A", "acting": "#B5372E",
             "music": "#D9822B", "art": "#C9A227", "military": "#6B6B2E", "religion": "#8A5A3C", "business": "#5E6B78", "other": "#A39E95"}
NEW_TOWNS = {"Corby", "Bracknell", "Milton Keynes", "Cumbernauld", "Washington", "Telford", "Harlow", "Basildon", "Stevenage", "Livingston", "Crawley",
             "East Kilbride", "Craigavon", "Glenrothes", "Redditch", "Runcorn", "Skelmersdale", "Peterborough", "Northampton", "Warrington", "Hemel Hempstead"}

ph = R["per_head"]
low = [x for x in ph["big_low"] if x["name"] in NEW_TOWNS][:4]
assert len(low) >= 3, ph["big_low"]
bell = T[T.name == "Bellshill"].iloc[0]
rb = R["rural_by_era"]
lon_n = int(re.search(r"sum of the (\d+)", T[T.code == "LONDON"].pop_src.iloc[0]).group(1))
stars = "".join(f'<span><i>&#9733;</i><b>{x["name"]}</b>{x["town"]}</span>' for x in R["most_famous_overall"][:4])
R["page"] = dict(
    hero_stars=stars, top_sport_share=R["top_group_share"].get("sport", 0) + R["top_group_share"].get("footballer", 0),
    scaling_factor=2 ** R["scaling"]["slope"], rural_1800s=rb["1800s"]["share_rural"], rural_1980=rb["1980 on"]["share_rural"],
    bellshill_n=int(bell.n), bellshill_pop=int(bell["pop"]), bellshill_post=float(bell.n_since1950 / bell.n),
    w_footballer=R["women_by_group"]["footballer"], n_london_bua=lon_n,
    low_text=", ".join(f'{x["name"]} ({x["rate"]:.1f})' for x in low[:-1]) + f' and {low[-1]["name"]} ({low[-1]["rate"]:.1f})')
# colour breaks: quintiles of births per head among towns of 5,000 or more with any births in the view
def qbreaks(v):
    v = np.asarray(v, float); v = v[v > 0]
    qs = np.quantile(v, [.2, .4, .6, .8])
    nice = lambda x: float(f"{x:.2g}") if x < 10 else int(round(x / (5 if x < 100 else 10)) * (5 if x < 100 else 10))
    out = []
    for q in qs:
        b = nice(q)
        if not out or b > out[-1]: out.append(b)
    return out
t5 = T[T["pop"] >= 5000]
breaks = {"all": qbreaks(t5.n / t5["pop"] * 1e4), "pre": qbreaks(t5.n_pre1900 / t5["pop"] * 1e4), "post": qbreaks(t5.n_since1950 / t5["pop"] * 1e4)}
gbreaks = [qbreaks(t5["g_" + g] / t5["pop"] * 1e5) for g in GN]
w = T[T.n_mf >= 20]; wbreaks = [round(float(x), 2) for x in np.quantile(w.n_f / w.n_mf, [.2, .4, .6, .8])]
R["page"].update(breaks=breaks, gbreaks=gbreaks, wbreaks=wbreaks)
json.dump(R, open(RP, "w"), indent=1, ensure_ascii=False)

# words in the text, checked against the data
mf = R["most_famous_overall"]
assert [m["name"] for m in mf[:3]] == ["William Shakespeare", "Isaac Newton", "Charles Darwin"], mf[:3]
assert mf[2]["town"] == "Shrewsbury"
assert R["per_head_era"]["mid_since1950"][0]["name"] == "Bellshill" and R["page"]["bellshill_post"] > .6
assert R["by_nation"]["Scotland"]["rate"] == max(v["rate"] for v in R["by_nation"].values())
assert R["by_nation"]["Scotland"]["share_women"] == min(v["share_women"] for v in R["by_nation"].values())
assert R["by_nation"]["England"]["share_women"] == max(v["share_women"] for v in R["by_nation"].values())
assert R["group_capitals"]["military"][0]["name"] == "Greenock" and {"Edinburgh", "Oxford", "Cambridge", "Aberdeen"} <= {x["name"] for x in R["group_capitals"]["science"][:4]}
_lon = next(c for c in R["most_famous_cities"] if c["town"] == "London"); assert _lon["name"] == "Charlie Chaplin" and _lon["viewed"] == "Harry Kane"
fc = R["fame_compare"]; assert fc["sl"]["sport"] > fc["pv"]["sport"] and fc["sl"]["science"] > fc["pv"]["science"] and fc["pv"]["acting"] > fc["sl"]["acting"] and fc["pv"]["since1950"] > fc["sl"]["since1950"]
wc = R["women_by_century"]; assert wc["1700s"] < .12 and .25 <= wc["2000s"] < .3
gbc = R["group_by_century"]; assert gbc["1700s"]["military"] > gbc["1900s"]["military"] and gbc["1700s"]["religion"] > gbc["1900s"]["religion"] and gbc["1900s"]["sport"] > gbc["1800s"]["sport"]


def get(path):
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def f(m):
    path, _, fm = m.group(1).partition("|")
    v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}%"
    if fm == "pct1": return f"{v * 100:.1f}%"
    if fm == "f0": return f"{v:.0f}"
    if fm == "f1": return f"{v:.1f}"
    if fm == "f2": return f"{v:.2f}"
    if fm == "date":
        y, mo, dd = map(int, v.split("-")); return f"{dd} {['January','February','March','April','May','June','July','August','September','October','November','December'][mo - 1]} {y}"
    return str(v)


def embed():
    rank = {}
    for size in ("mid", "big"):
        for era, key in (("all", "rate"), ("pre", "rate_pre1900"), ("post", "rate_since1950")):
            src = ph[size] if era == "all" else R["per_head_era"][f"{size}_{'pre1900' if era == 'pre' else 'since1950'}"]
            rank[f"{size}_{era}"] = [[x["name"], x["top"], x[key], x["n" if era == "all" else ("n_pre1900" if era == "pre" else "n_since1950")]] for x in src]
    cities = [[c["town"], c["name"], c["year"], c["sl"], c["viewed"]] for c in R["most_famous_cities"]]
    caps = [[GN.index(g), R["group_capitals"][g][0]["name"], R["group_capitals"][g][0]["n"], R["group_capitals"][g][0]["rate"]] for g in GROUPS]
    return dict(groups=GN, group_labels=GROUP_LABEL, group_short=GROUP_SHORT, group_colours=[GROUP_COL[g] for g in GN],
                nations=["England", "Scotland", "Wales", "Northern Ireland"], centuries=["before 1600", "1600s", "1700s", "1800s", "1900s", "2000s", "unknown"],
                breaks=breaks, gbreaks=gbreaks, wbreaks=wbreaks, rank=rank,
                rural=[[k, v["share_rural"], v["n"]] for k, v in R["rural_by_era"].items()], gbc=R["group_by_century"],
                women_dec=[[int(k), v["share"], v["n"]] for k, v in R["women_by_decade"].items() if v["n"] >= 200],
                cities=cities, caps=caps, quick=["Liverpool", "Edinburgh", "Stratford-upon-Avon", "Bellshill", "Clitheroe", "Swansea", "Belfast", "Oxford"],
                start_town="Liverpool", pv_days=R["meta"]["pv_days"], nat_post=R["since1950_share"]["national"])


if __name__ == "__main__":
    t = open(os.path.join(HERE, "page_template.html")).read()
    t = re.sub(r"\{\{([^}]+)\}\}", f, t)
    t = t.replace("/*R*/", json.dumps(embed(), ensure_ascii=False, separators=(",", ":")))
    snip = open("/home/claude/hist/_brief/fullscreen_snippet.html").read() if os.path.exists("/home/claude/hist/_brief/fullscreen_snippet.html") else open(os.path.join(HERE, "fullscreen_snippet.html")).read()
    t = t.replace("</body>", snip + "\n</body>")
    assert "{{" not in t
    vis = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S))
    for bad in ("—", "–", "--"): assert bad not in vis, bad
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", len(t))
