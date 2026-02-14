#!/usr/bin/env python3
import json
import os
import re
import unicodedata
from datetime import datetime, timezone

ROOT = "/Users/TH_1/Documents/Repo/ACO"
CORPUS_PATH = os.path.join(ROOT, "data_processing/output/corpus.jsonl")
TIMELINE_PATH = os.path.join(ROOT, "data_processing/output/timeline.json")
OUT_PATH = os.path.join(ROOT, "src/lib/data/term-frequency.json")


def normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def midpoint_year(start: str, end: str) -> int:
    s = parse_date(start)
    e = parse_date(end)
    mid_ts = s.timestamp() + (e.timestamp() - s.timestamp()) / 2
    return datetime.fromtimestamp(mid_ts, tz=timezone.utc).year


TERMS = [
    {"key": "theotokos", "term": "θεοτόκος", "stem": "θεοτοκ"},
    {"key": "christotokos", "term": "χριστοτόκος", "stem": "χριστοτοκ"},
    {"key": "physis", "term": "φύσις", "stem": "φυσι"},
    {"key": "hypostasis", "term": "ὑπόστασις", "stem": "υποστασ"},
    {"key": "ousia", "term": "οὐσία", "stem": "ουσι"},
    {"key": "prosopon", "term": "πρόσωπον", "stem": "προσωπ"},
    {"key": "logos", "term": "λόγος", "stem": "λογο"},
    {"key": "henosis", "term": "ἕνωσις", "stem": "ενωσ"},
]


def build():
    with open(TIMELINE_PATH, encoding="utf-8") as f:
        timeline = json.load(f)

    doc_year = {}
    for item in timeline.get("items", []):
        doc_id = item.get("doc_id")
        start = item.get("start")
        end = item.get("end")
        if not (doc_id and start and end):
            continue
        doc_year[doc_id] = midpoint_year(start, end)

    year_set = set()
    counts = {t["key"]: {} for t in TERMS}

    term_regex = {
        t["key"]: re.compile(rf"\b{normalize(t['stem'])}\w*")
        for t in TERMS
    }

    with open(CORPUS_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            doc_id = obj.get("doc_id")
            if not doc_id or doc_id not in doc_year:
                continue

            year = doc_year[doc_id]
            year_set.add(year)
            text = obj.get("text_full", "")
            text_norm = normalize(text)

            for t in TERMS:
                key = t["key"]
                n = len(term_regex[key].findall(text_norm))
                if n:
                    counts[key][year] = counts[key].get(year, 0) + n

    years = sorted(year_set)
    series = []
    for t in TERMS:
        key = t["key"]
        series.append(
            {
                "key": key,
                "term": t["term"],
                "counts": [counts[key].get(y, 0) for y in years],
            }
        )

    payload = {
        "meta": {
            "title": "Doctrinal Term Frequency (Draft)",
            "terms": [{"key": t["key"], "term": t["term"], "stem": t["stem"]} for t in TERMS],
            "normalization": "NFD + strip diacritics + lowercase; regex stem match on normalized text_full",
            "date_source": "data_processing/output/timeline.json (midpoint of date ranges)",
            "notes": "Draft counts; not lemmatized and may miss inflected forms or count false positives.",
        },
        "years": years,
        "series": series,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    build()
