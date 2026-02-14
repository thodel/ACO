#!/usr/bin/env python3
"""Export non-mapped persons to a disambiguation-friendly list."""

from __future__ import annotations

import json
import os
import csv

BASE = "/Users/TH_1/Documents/Repo/ACO/data_processing"
LINKS_PATH = os.path.join(BASE, "output", "person_normdata_links.json")
OUT_CSV = os.path.join(BASE, "output", "person_normdata_disambiguation.csv")
OUT_JSONL = os.path.join(BASE, "output", "person_normdata_disambiguation.jsonl")


def compact_gnd(cand):
    if not cand:
        return ""
    gid = cand.get("gnd_id") or ""
    name = cand.get("preferredName") or ""
    score = cand.get("match_score")
    score = f"{score:.3f}" if isinstance(score, (int, float)) else ""
    return f"{gid}|{name}|{score}"


def compact_wd(cand):
    if not cand:
        return ""
    wid = cand.get("id") or ""
    label = cand.get("label") or ""
    desc = cand.get("description") or ""
    score = cand.get("match_score")
    score = f"{score:.3f}" if isinstance(score, (int, float)) else ""
    return f"{wid}|{label}|{score}|{desc}"


def main() -> None:
    with open(LINKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for entry in data:
        status = entry.get("status")
        if status == "match":
            continue
        label = entry.get("label")
        variants = ";".join(entry.get("variants", []) or [])
        gnd_cands = entry.get("gnd", {}).get("candidates", [])[:5]
        wd_cands = entry.get("wikidata", {}).get("candidates", [])[:5]
        rows.append(
            {
                "label": label,
                "status": status,
                "variants": variants,
                "gnd_candidates": " || ".join(compact_gnd(c) for c in gnd_cands if c),
                "wikidata_candidates": " || ".join(compact_wd(c) for c in wd_cands if c),
                "resolved_gnd_id": "",
                "resolved_wikidata_id": "",
                "resolved_label": "",
                "notes": "",
            }
        )

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "label",
                "status",
                "variants",
                "gnd_candidates",
                "wikidata_candidates",
                "resolved_gnd_id",
                "resolved_wikidata_id",
                "resolved_label",
                "notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"rows: {len(rows)}")
    print(f"csv: {OUT_CSV}")
    print(f"jsonl: {OUT_JSONL}")


if __name__ == "__main__":
    main()
