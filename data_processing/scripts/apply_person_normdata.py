#!/usr/bin/env python3
"""Apply approved normdata mappings to the person register.

Reads:
  - output/register.json
  - output/person_normdata_links.json
Writes:
  - output/register_normdata.json
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

BASE = "/Users/TH_1/Documents/Repo/ACO/data_processing"
REGISTER_PATH = os.path.join(BASE, "output", "register.json")
LINKS_PATH = os.path.join(BASE, "output", "person_normdata_links.json")
OUTPUT_PATH = os.path.join(BASE, "output", "register.json")


def main() -> None:
    with open(REGISTER_PATH, "r", encoding="utf-8") as f:
        register = json.load(f)
    with open(LINKS_PATH, "r", encoding="utf-8") as f:
        links = json.load(f)

    link_map: Dict[str, Dict] = {entry["label"]: entry for entry in links}

    applied = 0
    total = 0
    for entry in register.get("registerData", {}).get("Personen", []):
        label = entry.get("label")
        total += 1
        match = link_map.get(label)
        if not match or match.get("status") != "match":
            continue

        gnd_sel = match.get("gnd", {}).get("selected")
        wd_sel = match.get("wikidata", {}).get("selected")

        normdata = {
            "match_status": "match",
            "gnd": None,
            "wikidata": None,
        }

        if gnd_sel:
            normdata["gnd"] = {
                "id": gnd_sel.get("gnd_id"),
                "uri": gnd_sel.get("uri"),
                "preferredName": gnd_sel.get("preferredName"),
                "match_score": gnd_sel.get("match_score"),
                "wikidata": gnd_sel.get("wikidata"),
            }
        if wd_sel:
            normdata["wikidata"] = {
                "id": wd_sel.get("id"),
                "label": wd_sel.get("label"),
                "description": wd_sel.get("description"),
                "url": wd_sel.get("url"),
                "match_score": wd_sel.get("match_score"),
            }

        entry["normdata"] = normdata
        applied += 1

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(register, f, ensure_ascii=False, indent=2)

    print(f"total persons: {total}")
    print(f"applied mappings: {applied}")


if __name__ == "__main__":
    main()
