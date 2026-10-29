# Born here: who was born in your town?

The most famous person born in every UK town and city, the towns that produce more notable people than their size suggests, what those people did, and the share of women, from Wikidata.

Interactive page: https://maps.tristanhotham.com/famous-births/
Paper: https://doi.org/10.5281/zenodo.23763157
Blog post: https://blog.tristanhotham.com/2026/10/29/famous-births/

**Read this first.** These are notable people, not everyone: people with a Wikidata entry and a birthplace, a sample that leans towards men, sport, politics and the professions. Since the mid 20th century most babies have been born in hospital, so "born in" a town often means born in its hospital. Birthplaces are matched to towns by coordinates, not by name.

## Headline results

- {{overview.n_people|int}} people in Wikidata were born in the UK; {{overview.n_placed|int}} are matched to {{overview.n_towns_with|int}} of {{overview.n_towns|int}} towns and cities with official populations ({{overview.n_coarse|int}} have a birthplace as coarse as "England" or a county).
- Notable births grow faster than population: across {{scaling.n_towns|int}} towns of 10,000 or more the log-log slope is {{scaling.slope|f2}}. London has {{london.share_births|pct}} of matched births and {{london.share_pop|pct}} of residents.
- Per 10,000 residents today: Scotland {{by_nation.Scotland.rate|f1}}, Wales {{by_nation.Wales.rate|f1}}, Northern Ireland {{by_nation.Northern Ireland.rate|f1}}, England {{by_nation.England.rate|f1}}. Among places of 50,000 or more, {{per_head.big.0.name}} leads ({{per_head.big.0.rate|f1}}).
- Before 1900 the leading towns of 10,000 to 50,000 per head are {{per_head_era.mid_pre1900.0.name}}, {{per_head_era.mid_pre1900.1.name}} and {{per_head_era.mid_pre1900.2.name}}; since 1950 they are {{per_head_era.mid_since1950.0.name}}, {{per_head_era.mid_since1950.1.name}} and {{per_head_era.mid_since1950.2.name}}, many of them hospital towns (rank correlation between eras {{era_rank_corr|f2}}).
- Births outside any counted town fall from {{page.rural_1800s|pct1}} in the 1800s to {{page.rural_1980|pct1}} since 1980.
- Most sitelinks: {{most_famous_overall.0.name}} ({{most_famous_overall.0.town}}), {{most_famous_overall.1.name}} ({{most_famous_overall.1.town}}), {{most_famous_overall.2.name}} ({{most_famous_overall.2.town}}). The town's most famous person is a sportsperson in {{page.top_sport_share|pct}} of towns and a woman in {{top_women.share|pct}}.
- Women are {{overview.share_female_known|pct}} of notable people: {{women_by_century.1700s|pct}} of those born in the 1700s, {{women_by_century.2000s|pct}} of those born since 2000.

## Files

- `index.html`: the interactive page (loads `data/page/*.json`). `header.png`: social card.
- `data/results.json`: every number used in the page, paper, blog and collage.
- `data/towns.csv`: every town and city with population and source, notable births (all, before 1900, since 1950), births per 10,000 residents, women, births by occupation group and century, the most famous person (most sitelinks) and the most read person (English Wikipedia page views).
- `data/centuries.csv`, `data/women_by_decade.csv`: births, women's share, London's share and occupation mix by century and decade.
- `data/page/`: compact files for the map (towns, place labels, outline).
- `code/`: the scripts, run in order (below). `release/`: paper, blog post and Zenodo files. `reddit/`: collage.

## How to rerun

Inputs (paths in `code/common.py`, changeable with environment variables): the Wikidata bundles and page views made by `code/00_gather.js` (run in a browser), the NRS and NISRA spreadsheets, ONS built-up areas and lookups with Census 2021 LSOA counts, OS Open Names as a tab separated file, and ONS local authority boundaries.

```
python3 code/01_prepare.py      # towns with populations; people; birthplaces matched to towns
python3 code/02_analyse.py      # all measures, data/results.json and CSVs
python3 code/03_page_data.py    # data/page/
python3 code/04_build_site.py   # index.html
FONT_DIR=... python3 code/05_header.py
FONT_DIR=... python3 code/06_figures.py
python3 code/07_paper.py        # xelatex
python3 code/08_release.py      # README, blog post, Zenodo folder
python3 reddit/collage.py
```

## Sources and licences

- Wikidata, CC0 1.0, queried through QLever (University of Freiburg) on {{meta.retrieved|date}}.
- English Wikipedia page views, {{meta.pv_days}} days to {{meta.pv_end|date}}, through the MediaWiki API (Wikimedia, CC0 1.0).
- Office for National Statistics: built-up areas 2022, Census 2021 TS001 usual residents by LSOA, LSOA and MSOA lookups to built-up areas, MSOA population-weighted centroids, local authority boundaries; Open Government Licence v3.0.
- National Records of Scotland: population estimates for settlements and localities in Scotland, mid-2020; © Crown copyright, Open Government Licence v3.0.
- NISRA: Census 2021 commissioned table CT0100, usual residents by settlement; © Crown copyright, Open Government Licence v3.0.
- OS Open Names, Ordnance Survey: contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0.

Code: MIT. Data, text and figures: CC BY 4.0 (keep the source credits above). See `LICENSE`. Related: [Has your surname left home?](https://maps.tristanhotham.com/surname-birthplaces/) uses the same Wikidata births to follow surnames.

## Citation

Hotham, T. (2026) Born Here: Notable Births, Fame and Population in UK Towns and Cities, from Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23763157

Dr Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
