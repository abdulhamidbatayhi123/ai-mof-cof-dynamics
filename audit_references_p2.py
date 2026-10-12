"""Audit every reference of paper2/stage1.tex against Crossref and arXiv.

Owner of audit_2026-10-12/reference_audit_p2.json. For each \\bibitem:
  * every DOI is fetched from https://api.crossref.org/works/<doi> and compared, field by
    field, with the entry: title (normalised), first author's family name, year, venue,
    volume, first page / article number;
  * every arXiv id is fetched from export.arxiv.org and compared on title and first author;
    if the arXiv record names a journal DOI (a published version), that DOI is fetched from
    Crossref too and reported, so the bibliography can cite the version of record.
Nothing is changed automatically: a mismatch is a finding to read, not a value to copy.
No personal data is sent (no mailto, no e-mail in the User-Agent).

    python audit_references_p2.py [path/to/stage1.tex]
"""
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TEX = sys.argv[1] if len(sys.argv) > 1 else "paper2/stage1.tex"
OUT = "audit_2026-10-12/reference_audit_p2.json"
UA = {"User-Agent": "reference-audit/1.0"}
ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"


def norm(s):
    s = unicodedata.normalize("NFKD", html.unescape(str(s or "")))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\\[a-zA-Z]+|[{}$\\'\"`^~]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 -- retried, then reported
            err = e
            time.sleep(3 * (attempt + 1))
    raise err


def crossref(doi):
    """Crossref record; DOIs registered with DataCite (e.g. Zenodo, 10.5281) are read from
    DataCite and mapped onto the same fields."""
    try:
        return json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))["message"]
    except Exception:  # noqa: BLE001 -- not in Crossref: try DataCite before reporting
        a = json.loads(get("https://api.datacite.org/dois/" + urllib.parse.quote(doi)))["data"]["attributes"]
        return {"title": [a["titles"][0]["title"]],
                "author": [{"family": c.get("familyName") or c["name"].split(",")[0]} for c in a["creators"]],
                "issued": {"date-parts": [[a.get("publicationYear")]]},
                "container-title": [a.get("publisher") if isinstance(a.get("publisher"), str)
                                    else (a.get("publisher") or {}).get("name", "")],
                "type": "datacite:" + a["types"].get("resourceTypeGeneral", ""), "version": a.get("version")}


def arxiv(aid):
    root = ET.fromstring(get("http://export.arxiv.org/api/query?id_list=" + aid))
    e = root.find(ATOM + "entry")
    if e is None or e.find(ATOM + "title") is None:
        raise ValueError("no arXiv entry")
    d = e.find(ARX + "doi")
    j = e.find(ARX + "journal_ref")
    return {"title": " ".join(e.find(ATOM + "title").text.split()),
            "first_author": e.find(ATOM + "author").find(ATOM + "name").text,
            "doi": d.text.strip() if d is not None else None,
            "journal_ref": " ".join(j.text.split()) if j is not None else None}


def parse(tex):
    body = tex.split(r"\begin{thebibliography}")[1].split(r"\end{thebibliography}")[0]
    out = []
    for m in re.finditer(r"\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem\{|\Z)", body, re.S):
        key, txt = m.group(1), " ".join(m.group(2).split())
        dois = re.findall(r"doi\.org/([^}\s]+)\}", txt)
        arx = re.findall(r"arxiv\.org/abs/([0-9.]+)", txt)
        out.append({"key": key, "text": txt, "dois": sorted(set(dois)), "arxiv": sorted(set(arx))})
    return out


def year_of(msg):
    for k in ("published-print", "published-online", "issued"):
        if msg.get(k, {}).get("date-parts"):
            return msg[k]["date-parts"][0][0]
    return None


def check_doi(entry, doi):
    m = crossref(doi)
    title = (m.get("title") or [""])[0]
    fam = (m.get("author") or [{}])[0].get("family", "")
    venue = (m.get("container-title") or [""])[0]
    vol, page = m.get("volume"), m.get("page") or m.get("article-number")
    t = norm(entry["text"])
    issues = []
    if norm(title) not in t:
        issues.append(f"title: registry '{title}'")
    if fam and norm(fam) not in t:
        issues.append(f"first author: registry '{fam}'")
    y = year_of(m)
    if y and str(y) not in entry["text"]:
        issues.append(f"year: registry {y}")
    if venue and norm(venue) not in t:
        issues.append(f"venue: registry '{venue}'")
    if vol and not re.search(r"(?<![0-9])" + re.escape(str(vol)) + r"(?![0-9])", entry["text"]):
        issues.append(f"volume: registry {vol}")
    if page:
        first = str(page).split("-")[0]
        if first not in entry["text"]:
            issues.append(f"page/article: registry {page}")
    return {"doi": doi, "registry": {"title": title, "first_author": fam, "year": y, "venue": venue,
                                     "volume": vol, "page": page, "type": m.get("type")},
            "issues": issues}


def main():
    entries = parse(open(TEX, encoding="utf-8").read())
    rows, n_issue = {}, 0
    for e in entries:
        row = {"dois": [], "arxiv": [], "published_version": None}
        for d in e["dois"]:
            try:
                row["dois"].append(check_doi(e, d))
            except Exception as ex:  # noqa: BLE001
                row["dois"].append({"doi": d, "issues": [f"FETCH FAILED: {ex}"]})
            time.sleep(0.5)
        for a in e["arxiv"]:
            try:
                r = arxiv(a)
                iss = []
                if norm(r["title"]) not in norm(e["text"]):
                    iss.append(f"title: arXiv '{r['title']}'")
                last = r["first_author"].split()[-1]
                if norm(last) not in norm(e["text"]):
                    iss.append(f"first author: arXiv '{r['first_author']}'")
                row["arxiv"].append({"id": a, "record": r, "issues": iss})
                if r["doi"] and r["doi"].lower() not in [d.lower() for d in e["dois"]]:
                    try:
                        row["published_version"] = check_doi(e, r["doi"])
                    except Exception as ex:  # noqa: BLE001
                        row["published_version"] = {"doi": r["doi"], "issues": [f"FETCH FAILED: {ex}"]}
            except Exception as ex:  # noqa: BLE001
                row["arxiv"].append({"id": a, "issues": [f"FETCH FAILED: {ex}"]})
            time.sleep(3.1)  # arXiv API etiquette
        if e["arxiv"] and not e["dois"] and row["published_version"] is None:
            # arXiv names no journal DOI: ask Crossref for a work with the same title and
            # first author. Only an exact normalised-title match is reported, as a candidate.
            rec = next((x["record"] for x in row["arxiv"] if "record" in x), None)
            if rec:
                q = urllib.parse.urlencode({"query.bibliographic": rec["title"],
                                            "query.author": rec["first_author"], "rows": 5})
                try:
                    items = json.loads(get("https://api.crossref.org/works?" + q))["message"]["items"]
                    hits = [it for it in items if norm((it.get("title") or [""])[0]) == norm(rec["title"])
                            and it.get("type") != "posted-content"]
                    if hits:
                        it = hits[0]
                        row["crossref_candidate"] = {
                            "doi": it["DOI"], "title": it["title"][0],
                            "venue": (it.get("container-title") or [""])[0], "year": year_of(it),
                            "type": it.get("type")}
                except Exception as ex:  # noqa: BLE001
                    row["crossref_candidate"] = {"error": str(ex)}
                time.sleep(0.5)
        if not e["dois"] and not e["arxiv"]:
            row["note"] = "no identifier"
        bad = [i for x in row["dois"] + row["arxiv"] for i in x["issues"]]
        row["status"] = "ISSUES" if bad else ("NO-ID" if row.get("note") else "OK")
        n_issue += bool(bad)
        rows[e["key"]] = row
        pv, cc = row["published_version"], row.get("crossref_candidate")
        print(f"{e['key']:18s} {row['status']:6s}", "; ".join(bad)[:200],
              f"| PUBLISHED: {pv['doi']} {pv.get('registry', {}).get('venue', '')}" if pv else "",
              f"| CANDIDATE: {cc.get('doi')} {cc.get('venue')} {cc.get('year')} {cc.get('type')}" if cc else "")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump({"source": TEX, "fetched_utc": stamp, "n_entries": len(entries),
               "n_with_issues": n_issue, "entries": rows},
              open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\n{len(entries)} entries, {n_issue} with issues -> {OUT}")


if __name__ == "__main__":
    main()
