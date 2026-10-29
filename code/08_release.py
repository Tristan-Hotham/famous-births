"""Step 8. README, blog post and metadata, and the Zenodo folder.
Writes README.md, release/blog/post.html and meta.json, release/zenodo/ (paper, key data files, code-and-data zip, meta.json).
Run after 07_paper.py: python3 code/08_release.py
"""
import importlib.util, json, os, re, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
SLUG, DOI, PDF = "famous-births", "10.5281/zenodo.23763157", "Hotham_Born_Here_Notable_Births.pdf"
nodash = lambda s: "—" not in s and "–" not in s and "--" not in s
fill = lambda t: re.sub(r"\{\{(?!IMG\|)([^}]+)\}\}", b.f, t)
rd = fill(open(os.path.join(HERE, "README_template.md")).read())
open(os.path.join(ROOT, "README.md"), "w").write(rd)
blog = os.path.join(ROOT, "release", "blog")
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^{}]+)\}\}", b.f, t)          # numbers inside IMG placeholders first
t = fill(t)
for img in re.findall(r"\{\{IMG\|([^|]+)\|", t): assert os.path.exists(os.path.join(blog, img)), img
assert "{{" not in re.sub(r"\{\{IMG\|[^}]*\}\}", "", t)
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
assert nodash(vis)
open(os.path.join(blog, "post.html"), "w").write(t)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = dict(title="Born here: the most famous person from every UK town", slug=SLUG,
            excerpt=f"I matched {R['overview']['n_placed']:,} notable people in Wikidata to the UK towns and cities they were born in: the most famous person from each, the towns that punch above their weight, and why so many of them are hospital towns.",
            seo_description="The most famous person born in every UK town, notable births per head, occupations and women's share, mapped from Wikidata.",
            tags=["famous people", "birthplaces", "Wikidata", "maps", "towns", "Wikipedia", "open data", "United Kingdom"],
            header_alt="Social card reading 'Who was born in your town?' beside a map of the United Kingdom dotted with towns coloured by notable births per head, labelled with famous names such as William Shakespeare at Stratford-upon-Avon, John Lennon at Liverpool and Adam Smith at Kirkcaldy.")
assert len(meta["seo_description"]) < 160
json.dump(meta, open(os.path.join(blog, "meta.json"), "w"), indent=1, ensure_ascii=False)
print("post.html words", words)

z = os.path.join(ROOT, "release", "zenodo")
if os.path.exists(z): shutil.rmtree(z)
os.makedirs(z)
shutil.copy(os.path.join(ROOT, "release", PDF), os.path.join(z, PDF))
for fn in ["towns.csv", "centuries.csv", "women_by_decade.csv", "results.json"]:
    shutil.copy(os.path.join(DATA, fn), os.path.join(z, fn))
zp = os.path.join(z, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in ["code", "data"]:
        for dp, _, fs in os.walk(os.path.join(ROOT, base)):
            for fn in fs:
                if fn.endswith(".pyc") or "__pycache__" in dp: continue
                p = os.path.join(dp, fn); zf.write(p, os.path.relpath(p, ROOT))
    for fn in ["README.md", "LICENSE"]: zf.write(os.path.join(ROOT, fn), fn)
tex = open(os.path.join(ROOT, "release", "paper", PDF.replace(".pdf", ".tex"))).read()
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}(.*?)\\textbf\{Keywords", tex, re.S).group(1).strip()
ab = ab.replace("\\%", "%").replace("~", " ").replace("\\&", "&")
title = re.search(r"pdftitle=\{(.*?)\},pdfauthor", tex).group(1)
zmeta = dict(title=title,
             description_html=f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/{SLUG}/. Data and code: https://github.com/Tristan-Hotham/{SLUG}. Blog post: to follow.</p>",
             keywords=["Wikidata", "notable people", "birthplaces", "fame", "Wikipedia page views", "urban scaling", "hospital births", "United Kingdom", "towns", "open data"],
             licence="cc-by-4.0",
             related=[dict(identifier=f"https://github.com/Tristan-Hotham/{SLUG}", relation="issupplementedby", resource_type="software"),
                      dict(identifier=f"https://maps.tristanhotham.com/{SLUG}/", relation="issupplementedby", resource_type="other"),
                      dict(identifier="https://www.wikidata.org/", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://www.ons.gov.uk/", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://www.nrscotland.gov.uk/publications/population-estimates-for-settlements-and-localities-in-scotland-mid-2020/", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://www.nisra.gov.uk/publications/ct0100-usual-resident-population-settlement-lgd2014-code-and-lgd2014-name-settlement", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset")])
for v in (zmeta["title"], zmeta["description_html"], json.dumps(meta, ensure_ascii=False), rd): assert nodash(v)
json.dump(zmeta, open(os.path.join(z, "meta.json"), "w"), indent=1, ensure_ascii=False)
for fn in sorted(os.listdir(z)): print(fn, os.path.getsize(os.path.join(z, fn)))
