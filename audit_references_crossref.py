"""Audit every DOI-bearing bibliography entry against its Crossref record.

Owner of audit_2026-10-04/reference_audit_crossref.json. For each entry in
paper/references.py with a DOI, fetch https://api.crossref.org/works/<doi> (no
personal data in the request) and compare, field by field, what the bibliography says
with what the registry says: title (normalised), first author's family name, year,
journal, volume, first page / article number. Every mismatch is listed; nothing is
changed automatically -- a mismatch is a finding to be read, not a value to copy.

    python audit_references_crossref.py
"""
import importlib.util
import json
import re
import time
import unicodedata
import urllib.request

OUT = "audit_2026-10-04/reference_audit_crossref.json"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\\[a-zA-Z]+|[{}$\\'\"`^~]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def crossref(doi):
    req = urllib.request.Request("https://api.crossref.org/works/" + doi,
                                 headers={"User-Agent": "reference-audit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]


def main():
    spec = importlib.util.spec_from_file_location("refs", "paper/references.py")
    refs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refs)
    rows, n_ok = {}, 0
    for key, state, kind, f, note, allow in refs.REFS:
        doi = f.get("doi")
        if not doi:
            rows[key] = {"status": "NO DOI", "state": state}
            continue
        try:
            m = crossref(doi)
        except Exception as e:
            rows[key] = {"status": f"FETCH FAILED: {e}", "doi": doi}
            continue
        problems = []
        ct = norm((m.get("title") or [""])[0])
        bt = norm(f.get("title", ""))
        if bt and ct and bt != ct and not (bt in ct or ct in bt):
            problems.append(f"title: bib '{f.get('title')}' vs crossref '{(m.get('title') or [''])[0]}'")
        auth = m.get("author") or []
        if auth and f.get("author"):
            cf = norm(auth[0].get("family", auth[0].get("name", "")))
            bf = norm(f["author"].split(" and ")[0]).split(" ")[-1] if f["author"] else ""
            if cf and bf and cf.split(" ")[-1] != bf:
                problems.append(f"first author: bib '{f['author'].split(' and ')[0]}' vs crossref "
                                f"'{auth[0].get('given', '')} {auth[0].get('family', '')}'")
        issued = (m.get("issued") or {}).get("date-parts", [[None]])[0][0]
        pub = (m.get("published-print") or m.get("published-online") or {}).get("date-parts", [[None]])[0][0]
        if f.get("year") and str(f["year"]) not in {str(issued), str(pub)}:
            problems.append(f"year: bib {f['year']} vs crossref issued {issued} / print {pub}")
        cj = norm((m.get("container-title") or [""])[0])
        bj = norm(f.get("journal", ""))
        if bj and cj and bj != cj and not (bj in cj or cj in bj):
            problems.append(f"journal: bib '{f.get('journal')}' vs crossref '{(m.get('container-title') or [''])[0]}'")
        if f.get("volume") and m.get("volume") and str(f["volume"]) != str(m["volume"]):
            problems.append(f"volume: bib {f['volume']} vs crossref {m['volume']}")
        bp = str(f.get("pages", "")).split("--")[0].split("-")[0].strip()
        cp = str(m.get("page", m.get("article-number", ""))).split("-")[0].strip()
        if bp and cp and norm(bp) != norm(cp):
            problems.append(f"first page: bib {bp} vs crossref {cp}")
        n_auth_cr = len(auth)
        n_auth_bib = len(f.get("author", "").split(" and ")) if f.get("author") else 0
        if "others" not in f.get("author", "") and n_auth_cr and n_auth_bib and n_auth_cr != n_auth_bib:
            problems.append(f"author count: bib {n_auth_bib} vs crossref {n_auth_cr}")
        rows[key] = {"doi": doi, "state": state, "status": "OK" if not problems else "MISMATCH",
                     "problems": problems}
        n_ok += not problems
        time.sleep(0.4)
    bad = {k: v for k, v in rows.items() if v["status"] not in ("OK", "NO DOI")}
    out = {"_what": __doc__.splitlines()[0], "n_entries": len(rows), "n_ok": n_ok,
           "n_flagged": len(bad), "rows": rows}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{len(rows)} entries: {n_ok} match Crossref, {len(bad)} flagged, "
          f"{sum(v['status'] == 'NO DOI' for v in rows.values())} without DOI")
    for k, v in bad.items():
        print(f"  {k}: {v['status']}")
        for p in v.get("problems", []):
            print(f"      {p}")


if __name__ == "__main__":
    main()
