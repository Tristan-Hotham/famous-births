# Reddit post

## Title

[OC] Who was born in your town? The most famous person born in UK towns and cities, from 166,586 notable people in Wikidata, with births per head

## Body (optional)

I matched every person in Wikidata whose birthplace is in the UK to the town or city they were born in (166,586 placed in 3,869 towns), and set them against today's population. Bigger places punch harder: double a town's size and you get about 2.5 times as many notable births, and London has 26% of the births but 14% of the people. The biggest surprise was hospitals: for people born since 1950 the top small towns per head are places like Bellshill, where 74% of its 292 notable births are since 1950. Caveat: these are notable people only, so the sample leans to men, sport and the professions. Explore the map and search your town: https://maps.tristanhotham.com/famous-births/

## Source comment

Source: Wikidata (CC0 1.0), every human with a place of birth (P19) in the UK, queried through the QLever SPARQL endpoint on 29 October 2026; fame from Wikimedia sitelinks, and English Wikipedia page views (30 days to 28 October 2026) through the MediaWiki API. Populations: ONS built-up areas 2022 and Census 2021 (England and Wales), NRS settlements and localities mid-2020 (Scotland), NISRA Census 2021 settlements (Northern Ireland); place names from OS Open Names. All Open Government Licence v3.0; contains OS data © Crown copyright and database right 2026.

Tools: Python (pandas, NumPy, SciPy, matplotlib), Leaflet for the interactive map.

Interactive map: https://maps.tristanhotham.com/famous-births/
Blog post: https://blog.tristanhotham.com/2026/10/29/famous-births/
Paper, data and code: https://doi.org/10.5281/zenodo.23763157
