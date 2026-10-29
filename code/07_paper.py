"""Step 7. Fill code/paper_template.tex from data/results.json and compile with xelatex (figures from step 6).
Writes release/paper/ (tex and figures) and release/Hotham_Born_Here_Notable_Births.pdf. Run: python3 code/07_paper.py
"""
import importlib.util, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
OUT = os.path.join(ROOT, "release", "paper"); os.makedirs(OUT, exist_ok=True)
NAME = "Hotham_Born_Here_Notable_Births"
tex = lambda s: str(s).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
def sub(m):
    path, _, fm = m.group(1).partition("|"); v = b.get(path.strip())
    if fm == "pct": return f"{round(v * 100)}\\%"
    if fm == "pct1": return f"{v * 100:.1f}\\%"
    if fm in ("int", "f0", "f1", "f2", "date"): return b.f(m)
    return tex(v)
R["meta"]["sc_unmatched_pop"] = R["meta"]["sc_unmatched_pop"]
rows = "".join(f"{n} & {v['n']:,} & {v['pop']:,} & {R['by_nation'][n]['n']:,} & {R['by_nation'][n]['rate']:.1f} & {round(R['by_nation'][n]['share_women'] * 100)}\\%\\\\\n"
               for n, v in R["towns_by_nation"].items())
T_N = ("\\begin{table}[H]\\centering\\small\\caption{Towns and placed notable births by nation: number of towns, residents, placed births, births per 10,000 residents, and women's share of births with a recorded sex. Populations: Census 2021 (England, Wales, Northern Ireland) and NRS mid-2020 estimates (Scotland).}\\label{tab:nations}"
       "\\begin{tabular}{lrrrrr}\\toprule Nation & Towns & Residents & Births & Per 10,000 & Women\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(c['town'])} & {tex(c['name'])} & {c['sl']} & {tex(c['viewed']) if c['viewed'] and c['viewed'] != c['name'] else 'same'}\\\\\n" for c in R["most_famous_cities"])
T_C = ("\\begin{table}[H]\\centering\\small\\caption{The most famous person born in each UK city of 150,000 or more: most sitelinks, and most read on English Wikipedia among the three people with most sitelinks at each birthplace.}\\label{tab:cities}"
       "\\begin{tabular}{l>{\\raggedright\\arraybackslash}p{4.6cm}r>{\\raggedright\\arraybackslash}p{4.6cm}}\\toprule City & Most sitelinks & Sitelinks & Most read in English\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
GS = {"footballer": "Footballers", "sport": "Other sport", "politics": "Politics and law", "science": "Science and scholarship", "writing": "Writing", "acting": "Acting",
      "music": "Music", "art": "Visual arts", "military": "Military", "religion": "Religion", "business": "Business"}
rows = "".join(f"{GS[g]} & {R['groups'][g]['n']:,} & " + tex("; ".join(f"{x['name']} ({x['rate']:.0f})" for x in R["group_capitals"][g][:3])) + "\\\\\n" for g in GROUPS)
T_G = ("\\begin{table}[H]\\centering\\small\\caption{Occupation groups: people in each group and the three towns of 20,000 or more with most births in the group per 100,000 residents (at least five births).}\\label{tab:caps}"
       "\\begin{tabular}{lr>{\\raggedright\\arraybackslash}p{9.2cm}}\\toprule Group & People & Capitals (births per 100,000)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = t.replace("{{TABLE_NATIONS}}", T_N).replace("{{TABLE_CITIES}}", T_C).replace("{{TABLE_CAPS}}", T_G)
t = re.sub(r"\{\{([^}]+)\}\}", sub, t)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
for ext in [".aux", ".log", ".out", ".pdf"]:
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
print("paper written", r.returncode)
