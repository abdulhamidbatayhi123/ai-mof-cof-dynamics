"""Audit every arXiv-identified bibliography entry against the arXiv registry.

For entries in paper/references.py with an `eprint` and no DOI: does the identifier
exist, do the title and first author match, and has the preprint since been published
(arXiv journal_ref / DOI) -- in which case the published version should be cited.
Prints findings; changes nothing.

    python audit_references_arxiv.py
"""
import importlib.util
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[{}$\\]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main():
    spec = importlib.util.spec_from_file_location("r", "paper/references.py")
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    entries = {k: f for k, st, kind, f, n, a in r.REFS if not f.get("doi") and f.get("eprint")}
    url = ("http://export.arxiv.org/api/query?id_list=" + ",".join(f["eprint"] for f in entries.values())
           + "&max_results=50")
    xml = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "reference-audit/1.0"}),
                                 timeout=60).read()
    got = {}
    for e in ET.fromstring(xml).findall("a:entry", NS):
        aid = re.sub(r"v\d+$", "", e.find("a:id", NS).text.rsplit("/", 1)[-1])
        jr, doi = e.find("arxiv:journal_ref", NS), e.find("arxiv:doi", NS)
        got[aid] = (" ".join(e.find("a:title", NS).text.split()),
                    [a.find("a:name", NS).text for a in e.findall("a:author", NS)],
                    jr.text if jr is not None else None, doi.text if doi is not None else None)
    for k, f in entries.items():
        if f["eprint"] not in got:
            print(f"MISSING  {k}: arXiv {f['eprint']} not found")
            continue
        t, auth, jref, doi = got[f["eprint"]]
        title_ok = norm(f["title"]) in norm(t) or norm(t) in norm(f["title"])
        fa = norm(f["author"].split(" and ")[0]).split()[-1]
        ca = norm(auth[0]).split()[-1]
        flag = "OK   " if title_ok and fa == ca else "CHECK"
        print(f"{flag} {k}: first author {auth[0]}{'' if fa == ca else ' (bib: ' + fa + ')'}"
              f"{'' if title_ok else ' | arXiv title: ' + t} | {len(auth)} authors"
              f" | journal_ref: {jref} | doi: {doi}")


if __name__ == "__main__":
    main()
