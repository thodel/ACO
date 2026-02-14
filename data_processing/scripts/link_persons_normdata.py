#!/usr/bin/env python3
"""Link person index entries to GND and Wikidata.

Outputs:
  - output/person_normdata_links.json
  - output/person_normdata_missing.csv
  - output/person_normdata_ambiguous.csv

Uses lobid GND API and Wikidata wbsearchentities.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

BASE = "/Users/TH_1/Documents/Repo/ACO/data_processing"
REGISTER_PATH = os.path.join(BASE, "output", "register.json")
OUTPUT_LINKS = os.path.join(BASE, "output", "person_normdata_links.json")
OUTPUT_MISSING = os.path.join(BASE, "output", "person_normdata_missing.csv")
OUTPUT_AMBIGUOUS = os.path.join(BASE, "output", "person_normdata_ambiguous.csv")
CACHE_PATH = os.path.join(BASE, "output", "person_normdata_cache.json")

GND_SEARCH_URL = "https://lobid.org/gnd/search"
GND_ENTITY_URL = "https://lobid.org/gnd/{id}.json"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"

USER_AGENT = "ACO-Normdata-Linker/1.0"
REQUEST_DELAY_GND = 0.2
REQUEST_DELAY_WD = 1.1
MAX_RETRIES = 5
BACKOFF_BASE = 1.0

AUTO_SCORE_THRESHOLD = 0.92
AUTO_GAP_THRESHOLD = 0.07


def norm(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    t = t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = re.sub(r"[\[\]\(\)\{\}“”„\"'’]", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def build_name_variants(label: str) -> List[str]:
    base = label.strip()
    # remove parenthetical annotations
    base = re.sub(r"\s*\(.*?\)", "", base).strip()
    variants = {base}

    # remove trailing descriptors after comma
    if "," in base:
        variants.add(base.split(",", 1)[0].strip())

    # von -> of/from
    if " von " in base:
        variants.add(base.replace(" von ", " of "))
        variants.add(base.replace(" von ", " from "))

    # der -> the
    if " der " in base:
        variants.add(base.replace(" der ", " the "))

    # normalize whitespace
    return [v for v in {re.sub(r"\s+", " ", v).strip() for v in variants} if v]


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def http_get_json(url: str, params: Dict[str, str] | None = None, delay: float = 0.0) -> Dict:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if delay:
                time.sleep(delay)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt <= MAX_RETRIES:
                retry_after = e.headers.get("Retry-After")
                sleep_for = float(retry_after) if retry_after and retry_after.isdigit() else BACKOFF_BASE * (2 ** (attempt - 1))
                time.sleep(sleep_for)
                continue
            raise


def gnd_search(name: str, cache: Dict) -> List[Dict]:
    cache_key = f"gnd::{name}"
    if cache_key in cache:
        return cache[cache_key]

    q = f'preferredName:"{name}" OR variantName:"{name}"'
    params = {
        "q": q,
        "filter": "type:Person",
        "format": "json",
        "size": "10",
    }
    data = http_get_json(GND_SEARCH_URL, params, delay=REQUEST_DELAY_GND)
    members = data.get("member", [])
    results = []
    for m in members:
        gnd_id = m.get("gndIdentifier") or m.get("id")
        preferred = m.get("preferredName")
        variant = m.get("variantName")
        same_as = m.get("sameAs", [])
        wikidata_id = None
        for s in same_as:
            uri = s.get("id") or s
            if isinstance(uri, str) and "wikidata.org/entity/" in uri:
                wikidata_id = uri.rsplit("/", 1)[-1]
        results.append(
            {
                "gnd_id": gnd_id,
                "preferredName": preferred,
                "variantName": variant,
                "uri": m.get("id") or (f"https://d-nb.info/gnd/{gnd_id}" if gnd_id else None),
                "wikidata": wikidata_id,
                "raw": m,
            }
        )
    cache[cache_key] = results
    return results


def wikidata_search(name: str, cache: Dict, lang: str = "de") -> List[Dict]:
    cache_key = f"wd::{lang}::{name}"
    if cache_key in cache:
        return cache[cache_key]

    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": lang,
        "format": "json",
        "limit": "10",
        "type": "item",
    }
    data = http_get_json(WIKIDATA_SEARCH_URL, params, delay=REQUEST_DELAY_WD)
    results = []
    for r in data.get("search", []):
        results.append(
            {
                "id": r.get("id"),
                "label": r.get("label"),
                "description": r.get("description"),
                "aliases": r.get("aliases"),
                "match": r.get("match"),
                "url": r.get("url"),
            }
        )
    cache[cache_key] = results
    return results


def rank_gnd_candidates(label: str, candidates: List[Dict]) -> List[Dict]:
    ranked = []
    for c in candidates:
        pref = c.get("preferredName") or ""
        variants = c.get("variantName") or []
        if isinstance(variants, str):
            variants = [variants]
        best = max([similarity(label, pref)] + [similarity(label, v) for v in variants], default=0.0)
        c2 = dict(c)
        c2["match_score"] = round(best, 4)
        ranked.append(c2)
    ranked.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return ranked


def rank_wd_candidates(label: str, candidates: List[Dict]) -> List[Dict]:
    ranked = []
    for c in candidates:
        label_c = c.get("label") or ""
        aliases = c.get("aliases") or []
        best = max([similarity(label, label_c)] + [similarity(label, a) for a in aliases], default=0.0)
        c2 = dict(c)
        c2["match_score"] = round(best, 4)
        ranked.append(c2)
    ranked.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return ranked


def auto_select(ranked: List[Dict]) -> Tuple[str, Optional[Dict]]:
    if not ranked:
        return "no_match", None
    if len(ranked) == 1:
        return ("match" if ranked[0]["match_score"] >= AUTO_SCORE_THRESHOLD else "ambiguous", ranked[0])
    best = ranked[0]
    second = ranked[1]
    if best["match_score"] >= AUTO_SCORE_THRESHOLD and (best["match_score"] - second["match_score"]) >= AUTO_GAP_THRESHOLD:
        return "match", best
    return "ambiguous", best


def main() -> None:
    with open(REGISTER_PATH, "r", encoding="utf-8") as f:
        register = json.load(f)

    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    persons = register.get("registerData", {}).get("Personen", [])
    results = []
    missing = []
    ambiguous = []

    for entry in persons:
        label = entry.get("label")
        variants = build_name_variants(label)
        gnd_candidates = []
        for v in variants:
            gnd_candidates.extend(gnd_search(v, cache))
        # de-dup by gnd_id
        uniq = {}
        for c in gnd_candidates:
            gid = c.get("gnd_id") or c.get("uri")
            if gid and gid not in uniq:
                uniq[gid] = c
        gnd_ranked = rank_gnd_candidates(label, list(uniq.values()))
        gnd_status, gnd_selected = auto_select(gnd_ranked)

        wd_candidates = []
        for v in variants:
            wd_candidates.extend(wikidata_search(v, cache, lang="de"))
            if not wd_candidates:
                wd_candidates.extend(wikidata_search(v, cache, lang="en"))
        # de-dup by id
        wd_uniq = {}
        for c in wd_candidates:
            wid = c.get("id")
            if wid and wid not in wd_uniq:
                wd_uniq[wid] = c
        wd_ranked = rank_wd_candidates(label, list(wd_uniq.values()))
        wd_status, wd_selected = auto_select(wd_ranked)

        status = "match" if gnd_status == "match" or wd_status == "match" else "ambiguous" if gnd_status == "ambiguous" or wd_status == "ambiguous" else "no_match"

        result = {
            "label": label,
            "variants": variants,
            "gnd": {
                "status": gnd_status,
                "selected": gnd_selected,
                "candidates": gnd_ranked[:10],
            },
            "wikidata": {
                "status": wd_status,
                "selected": wd_selected,
                "candidates": wd_ranked[:10],
            },
            "status": status,
        }
        results.append(result)

        if status == "no_match":
            missing.append({"label": label})
        if status == "ambiguous":
            ambiguous.append({"label": label})

        if len(results) % 25 == 0:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_LINKS, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_MISSING, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["label"])
        writer.writeheader()
        for row in missing:
            writer.writerow(row)

    with open(OUTPUT_AMBIGUOUS, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["label"])
        writer.writeheader()
        for row in ambiguous:
            writer.writerow(row)

    print(f"total persons: {len(persons)}")
    print(f"matches: {len([r for r in results if r['status']=='match'])}")
    print(f"ambiguous: {len(ambiguous)}")
    print(f"missing: {len(missing)}")


if __name__ == "__main__":
    main()
