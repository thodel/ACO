#!/usr/bin/env python3
import json
import os
import re

ROOT = "/Users/TH_1/Documents/Repo/ACO"
META_PATH = os.path.join(ROOT, "src/lib/data/aco-metadata.json")
TIMELINE_PATH = os.path.join(ROOT, "data_processing/output/timeline.json")
OUT_PATH = os.path.join(ROOT, "src/lib/data/document-structure.json")


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "")


def normalize(value: str) -> str:
    return strip_tags(value).lower()


COLLECTION_LABELS = {
    "CPal": "Collectio Palatina",
    "CV": "Collectio Vaticana",
    "CVer": "Collectio Veronensis",
    "CU": "Collectio U",
}

GENRE_RULES = [
    ("letter", ["brief", "ep.", "ep ", "epist", "schreiben", "sacra"]),
    ("sermon", ["predigt", "homilie", "sermo", "oratio"]),
    ("petition", ["bittschrift", "petition", "supplik", "supplic", "libellus"]),
    ("acts", ["acta", "akten", "sitzung", "protokoll"]),
]

GENRE_LABELS = {
    "letter": "Letters",
    "sermon": "Sermons/Homilies",
    "petition": "Petitions",
    "acts": "Acts/Proceedings",
    "other": "Other",
}


def infer_genre(title: str) -> str:
    t = normalize(title)
    for key, needles in GENRE_RULES:
        for needle in needles:
            if needle in t:
                return key
    return "other"


def load_timeline_years():
    with open(TIMELINE_PATH, encoding="utf-8") as f:
        timeline = json.load(f)
    years = {}
    for item in timeline.get("items", []):
        doc_id = item.get("doc_id")
        start = item.get("start")
        end = item.get("end")
        if not (doc_id and start and end):
            continue
        # midpoint year
        y = int(start[:4])
        y2 = int(end[:4])
        year = y if y == y2 else int((y + y2) / 2)
        years[doc_id] = year
    return years


def slice_key(year: int | None) -> str:
    if year is None:
        return "undated"
    if year < 431:
        return "pre-431"
    if year == 431:
        return "431"
    return "post-431"


def build():
    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)["metaData"]

    doc_year = load_timeline_years()

    collections = sorted({d.get("type") for d in meta if d.get("type")})
    genres = list(GENRE_LABELS.keys())
    slices = ["pre-431", "431", "post-431", "undated"]

    data = {s: {c: {g: 0 for g in genres} for c in collections} for s in slices}

    total_docs = 0
    for d in meta:
        collection = d.get("type")
        if collection not in collections:
            continue
        doc_id = d.get("slug") or d.get("schwartzSlug")
        year = doc_year.get(doc_id)
        s_key = slice_key(year)
        genre = infer_genre(d.get("title", ""))
        if genre not in genres:
            genre = "other"
        data[s_key][collection][genre] += 1
        total_docs += 1

    payload = {
        "meta": {
            "title": "Document Type & Collection Overview (Draft)",
            "notes": "Genres are inferred from title keywords. Date slices use document-level midpoint years from timeline.json.",
            "genre_rules": GENRE_RULES,
        },
        "collections": [{"key": c, "label": COLLECTION_LABELS.get(c, c)} for c in collections],
        "genres": [{"key": g, "label": GENRE_LABELS[g]} for g in genres],
        "slices": [
            {"key": "pre-431", "label": "Pre-431"},
            {"key": "431", "label": "431"},
            {"key": "post-431", "label": "Post-431"},
            {"key": "undated", "label": "Undated"},
        ],
        "data": data,
        "total_docs": total_docs,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    build()
