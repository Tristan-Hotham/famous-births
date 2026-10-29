// Step 0. How the inputs were gathered (run in a browser console; retrieved 29 October 2026).
// Wikidata through the QLever SPARQL endpoint (CORS-open) and English Wikipedia page views through the MediaWiki API.
// Results were reduced in the browser and saved as gzipped JSON bundles:
//   famous_births_wd.json.gz         people, birthplaces, occupations and occupation groups
//   famous_births_ni_types.json.gz   Northern Ireland settlements (for placing NISRA settlements) and birthplace type labels
//   famous_births_pageviews.json.gz  page views for the three people with most sitelinks at each birthplace
// Spreadsheets downloaded as published:
//   NRS, Population estimates for settlements and localities in Scotland, mid-2020, data tables:
//     https://www.nrscotland.gov.uk/media/wtwjdfuo/data-tables.xlsx  (Open Government Licence v3.0)
//   NISRA, Census 2021 commissioned table CT0100, usual residents by settlement:
//     https://www.nisra.gov.uk/system/files/statistics/census-2021-commissioned-table-ct0100.xlsx  (Open Government Licence v3.0)
const P = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wikibase: <http://wikiba.se/ontology#> PREFIX schema: <http://schema.org/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ';
const ql = async q => (await fetch('https://qlever.cs.uni-freiburg.de/api/wikidata?query=' + encodeURIComponent(P + q), { headers: { Accept: 'text/tab-separated-values' } })).text();
const UK = 'VALUES ?cty { wd:Q145 wd:Q174193 wd:Q179876 wd:Q230791 wd:Q161885 }';
const BASE = `{ SELECT DISTINCT ?pl WHERE { ?p wdt:P31 wd:Q5 ; wdt:P19 ?pl . ?pl wdt:P17 ?cty . ${UK} } }`;
const Q = {
  // one row per person: a sampled birthplace, number of birthplaces, earliest birth year, sex, sitelinks, English article, English label
  people: `SELECT ?p (SAMPLE(?pl0) AS ?pl) (COUNT(DISTINCT ?pl0) AS ?npl) (MIN(?y0) AS ?y) (SAMPLE(?s) AS ?sx) (SAMPLE(?sl0) AS ?sl) (SAMPLE(?en0) AS ?en) (SAMPLE(?lab0) AS ?lab) WHERE {
    ?p wdt:P31 wd:Q5 ; wdt:P19 ?pl0 . ?pl0 wdt:P17 ?cty . ${UK}
    OPTIONAL { ?p wdt:P569 ?d . BIND(YEAR(?d) AS ?y0) } OPTIONAL { ?p wdt:P21 ?s } OPTIONAL { ?p wikibase:sitelinks ?sl0 }
    OPTIONAL { ?en0 schema:about ?p ; schema:isPartOf <https://en.wikipedia.org/> } OPTIONAL { ?p rdfs:label ?lab0 . FILTER(LANG(?lab0)="en") } } GROUP BY ?p`,
  occupations: `SELECT DISTINCT ?p ?oc WHERE { ?p wdt:P31 wd:Q5 ; wdt:P19 ?pl0 . ?pl0 wdt:P17 ?cty . ${UK} ?p wdt:P106 ?oc . }`,
  // occupation groups: every occupation that is a subclass (P279*) of the roots below
  places: `SELECT ?pl (SAMPLE(?c0) AS ?c) (SAMPLE(?l0) AS ?l) (SAMPLE(?h0) AS ?h) WHERE { ${BASE} OPTIONAL { ?pl wdt:P625 ?c0 } OPTIONAL { ?pl rdfs:label ?l0 . FILTER(LANG(?l0)="en") } OPTIONAL { ?pl wdt:P31/wdt:P279* wd:Q16917 . BIND(1 AS ?h0) } } GROUP BY ?pl`,
  place_types: `SELECT DISTINCT ?pl ?t WHERE { ${BASE} ?pl wdt:P31 ?t . }`,
  place_admin: `SELECT DISTINCT ?pl ?a WHERE { ${BASE} ?pl wdt:P131 ?a . }`,
  ni_settlements: `SELECT ?s (SAMPLE(?l0) AS ?l) (SAMPLE(?c0) AS ?c) (SAMPLE(?ty0) AS ?ty) WHERE { ?s wdt:P131+ wd:Q26 ; wdt:P625 ?c0 ; wdt:P31 ?ty0 .
    VALUES ?ty0 { wd:Q515 wd:Q3957 wd:Q532 wd:Q486972 wd:Q1549591 wd:Q18511725 wd:Q188509 wd:Q123705 wd:Q5084 wd:Q1115575 } ?s rdfs:label ?l0 . FILTER(LANG(?l0)="en") } GROUP BY ?s`,
};
const ROOTS = { footballer: [937857], sport: [2066131, 50995749], music: [639669, 177220, 36834, 753110], acting: [33999, 2405480, 245068],
  writing: [36180, 1930187, 4964182], politics: [82955, 372436, 16533, 40348], science: [901, 170790, 81096, 39631, 1622272],
  art: [1028181, 1281618, 33231, 42973, 483501], military: [47064], religion: [2259532, 250867], business: [43845] };
const groupQuery = ids => `SELECT DISTINCT ?oc WHERE { VALUES ?r { ${ids.map(i => 'wd:Q' + i).join(' ')} } ?oc wdt:P279* ?r . }`;
// Page views: for each birthplace, the three people with most sitelinks who have an English Wikipedia article;
// POST action=query&prop=pageviews&pvipdays=30&redirects=1&titles=(50 at a time), following "continue" until done,
// summing daily views (days without data are skipped and counted). Queries were spaced 10 to 20 s apart on QLever.
async function pageviews(titles) {
  const out = {};
  for (let k = 0; k < titles.length; k += 50) {
    let cont = {};
    for (;;) {
      const body = new URLSearchParams({ action: 'query', prop: 'pageviews', pvipdays: '30', format: 'json', formatversion: '2', origin: '*', redirects: '1', titles: titles.slice(k, k + 50).join('|'), ...cont });
      const j = await (await fetch('https://en.wikipedia.org/w/api.php', { method: 'POST', body })).json();
      for (const p of j.query.pages) if (p.pageviews) { let s = 0, nd = 0; for (const v of Object.values(p.pageviews)) if (v !== null) { s += v; nd++; } out[p.title] = [s, nd]; }
      if (j.continue) cont = { ...j.continue }; else break;
    }
  }
  return out;
}
