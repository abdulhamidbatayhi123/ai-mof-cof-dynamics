"""Re-run, live, the negative searches behind Paper 2's novelty sentence, plus searches for
work that appeared since the literature review (2026-09/10).

The Stage-1 Introduction says three fetched database searches (two OpenAlex, one arXiv)
found no adsorption-KINETICS discovery study other than Santana et al. 2023. This script
re-runs those exact queries and adds targeted ones, and lists every hit so each can be read.
No personal data is sent.

    python lit_recheck_p2.py   -> audit_2026-10-12/lit_recheck_p2.json
"""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT = "audit_2026-10-12/lit_recheck_p2.json"
UA = {"User-Agent": "lit-recheck/1.0"}
A = "{http://www.w3.org/2005/Atom}"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def openalex(q, n=25, since=None):
    p = {"search": q, "per-page": n}
    if since:
        p["filter"] = f"from_publication_date:{since}"
    d = json.loads(get("https://api.openalex.org/works?" + urllib.parse.urlencode(p)))
    return [{"title": w.get("title"), "year": w.get("publication_year"), "doi": w.get("doi"),
             "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
             "date": w.get("publication_date")} for w in d["results"]]


def arxiv(q, n=40):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "max_results": n, "sortBy": "submittedDate", "sortOrder": "descending"})
    root = ET.fromstring(get(url))
    out = []
    for e in root.findall(A + "entry"):
        out.append({"title": " ".join(e.find(A + "title").text.split()),
                    "id": e.find(A + "id").text.rsplit("/", 1)[-1],
                    "published": e.find(A + "published").text[:10]})
    return out


QUERIES = [
    ("openalex", "sparse identification nonlinear dynamics adsorption", None),          # original 1
    ("openalex", "symbolic regression adsorption kinetics", None),                      # original 2
    ("arxiv", 'all:adsorption AND (all:SINDy OR all:"symbolic regression" OR all:"equation discovery" OR all:"sparse identification")', None),  # original 3
    ("openalex", "equation discovery breakthrough curve fixed bed", None),
    ("openalex", "universal differential equation adsorption column kinetics", None),
    ("openalex", "linear driving force rate law discovery machine learning", "2025-06-01"),
    ("openalex", "identifiability mass transfer coefficient breakthrough local equilibrium", "2025-06-01"),
    ("openalex", "metal-organic framework water adsorption kinetics machine learning discovery", "2025-06-01"),
    ("arxiv", 'all:"breakthrough curve" AND (all:"machine learning" OR all:"neural")', None),
    ("arxiv", 'all:"equation discovery" AND all:identifiability', None),
]


def main():
    res = {"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "queries": []}
    for src, q, since in QUERIES:
        try:
            hits = openalex(q, since=since) if src == "openalex" else arxiv(q)
        except Exception as ex:  # noqa: BLE001
            hits = [{"error": str(ex)}]
        res["queries"].append({"source": src, "query": q, "since": since, "hits": hits})
        print(f"\n## {src}: {q}" + (f" (since {since})" if since else ""))
        for h in hits:
            print("  -", h.get("year") or h.get("published"), "|", (h.get("title") or "")[:120],
                  "|", h.get("doi") or h.get("id") or h.get("error"))
        time.sleep(3.1)
    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
