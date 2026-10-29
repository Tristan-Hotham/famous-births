"""Shared paths and helpers for the famous births study.

Inputs (read in place; override with environment variables):
  SRC       folder with the gathered bundles (code/00_gather.js):
            famous_births_wd.json.gz      Wikidata people born in the UK, their birthplaces and occupations (CC0)
            famous_births_ni_types.json.gz Wikidata Northern Ireland settlements and birthplace type labels (CC0)
            famous_births_pageviews.json.gz Wikimedia pageviews for the leading candidates in each town (CC0)
            nrs_settlements_2020.xlsx     NRS settlements and localities, mid-2020 (Open Government Licence v3.0)
            nisra_ct0100_settlements.xlsx NISRA Census 2021 table CT0100, settlements (Open Government Licence v3.0)
  ONSGEO, LSOABUA, TS001  ONS built-up areas 2022 (centres, areas), MSOA population-weighted centroids and lookups,
            and Census 2021 usual residents by LSOA (all OGL v3.0), shared files read in place
  OSNAMES   OS Open Names, Great Britain (OGL v3.0), tab separated
Temporary files go to WORK (default /dev/shm/famous-births-work), outside the repository.
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
SRC = os.environ.get("SRC", "/home/claude/hist/_data18/famous-births")
WD = os.path.join(SRC, "famous_births_wd.json.gz")
NI = os.path.join(SRC, "famous_births_ni_types.json.gz")
PV = os.path.join(SRC, "famous_births_pageviews.json.gz")
NRS = os.path.join(SRC, "nrs_settlements_2020.xlsx")
NISRA = os.path.join(SRC, "nisra_ct0100_settlements.xlsx")
ONSGEO = os.environ.get("ONSGEO", "/home/claude/hist/_data8/ons_geo.json")          # BUA22 centres and areas, MSOA21 centroids and MSOA21 to BUA22
LSOABUA = os.environ.get("LSOABUA", "/home/claude/hist/_data8/lsoa21_bua22_lookup.json")  # LSOA21 to BUA22 best fit
TS001 = os.environ.get("TS001", "/home/claude/hist/_data8/census/census2021-ts001-lsoa.csv")  # Census 2021 usual residents
OSNAMES = os.environ.get("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
WORK = os.environ.get("WORK", "/dev/shm/famous-births-work")
os.makedirs(DATA, exist_ok=True); os.makedirs(WORK, exist_ok=True)

# broad occupation groups (Wikidata occupation P106 and its subclasses); a person goes to the group holding most of
# their occupations, ties going to the earlier group in ORDER
GROUPS = ["footballer", "sport", "politics", "science", "writing", "acting", "music", "art", "military", "religion", "business"]
ORDER = ["footballer", "sport", "politics", "music", "acting", "writing", "science", "art", "military", "religion", "business"]
GROUP_LABEL = {"footballer": "Footballers", "sport": "Other sport", "politics": "Politics, law and public life", "music": "Music",
               "acting": "Acting and screen", "writing": "Writing and journalism", "science": "Science, scholarship and medicine",
               "art": "Visual arts, film-making and dance", "military": "Military", "religion": "Religion", "business": "Business",
               "other": "Other or not recorded"}

# birthplaces too coarse to place: the UK and its nations, and counties
COARSE_QIDS = {145, 21, 22, 25, 26, 23666, 174193, 161885, 179876, 230791}
COARSE_TYPES = {180673, 1138494, 1857731, 769603, 769628, 1350181, 6256, 3336843, 15060255, 1136601, 15979307, 1187580, 149621, 1754946, 1002812, 1137272}


def xy(lat, lon):
    import numpy as np
    lat = np.asarray(lat, float); lon = np.asarray(lon, float)
    return np.c_[lon * 111.32 * math.cos(math.radians(54.5)), lat * 110.57]


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(min(1, a)))
