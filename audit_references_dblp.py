"""For arXiv-only bibliography entries: has the work been published, per DBLP?

Searches DBLP's public API by title; prints every DBLP record with a venue other than
CoRR (arXiv), next to what the bibliography currently says (booktitle/journal/author
count). Changes nothing.

    python audit_references_dblp.py
"""
import importlib.util
import json
import re
import time
import urllib.parse
import urllib.request


def main():
    spec = importlib.util.spec_from_file_location("r", "paper/references.py")
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    for k, st, kind, f, n, a in r.REFS:
        if f.get("doi") or not f.get("eprint"):
            continue
        title = re.sub(r"[{}]", "", f["title"])
        q = urllib.parse.quote(title)
        url = f"https://dblp.org/search/publ/api?q={q}&format=json&h=10"
        try:
            hits = json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "reference-audit/1.0"}), timeout=30))
            hits = hits["result"]["hits"].get("hit", [])
        except Exception as e:
            print(f"{k}: DBLP failed ({e})")
            continue
        bib_venue = f.get("booktitle") or f.get("journal") or "(none)"
        n_auth = len(f["author"].split(" and "))
        print(f"== {k} [{kind}] bib venue: {bib_venue} | bib authors: {n_auth}"
              f"{' (et al.)' if 'others' in f['author'] else ''}")
        for h in hits:
            info = h["info"]
            if info.get("venue") == "CoRR":
                continue
            au = info.get("authors", {}).get("author", [])
            au = au if isinstance(au, list) else [au]
            print(f"     DBLP: {info.get('venue')} {info.get('year')} | {len(au)} authors | "
                  f"{info.get('title', '')[:80]} | doi {info.get('doi')}")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
