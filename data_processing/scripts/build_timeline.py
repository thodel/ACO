#!/usr/bin/env python3
"""Build timeline data from corpus metadata (Datierung)."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

BASE = "/Users/TH_1/Documents/Repo/ACO/data_processing"
CORPUS_PATH = os.path.join(BASE, "output", "corpus.jsonl")
OUTPUT_PATH = os.path.join(BASE, "output", "timeline.json")

MONTHS = {
    "januar": 1,
    "februar": 2,
    "maerz": 3,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

SEASON_RANGES = {
    "anfang": ((1, 1), (3, 31)),
    "mitte": ((5, 1), (8, 31)),
    "ende": ((10, 1), (12, 31)),
    "fruehjahr": ((3, 1), (5, 31)),
    "frühjahr": ((3, 1), (5, 31)),
    "fruehsommer": ((5, 1), (6, 30)),
    "frühsommer": ((5, 1), (6, 30)),
    "sommer": ((6, 1), (8, 31)),
    "herbst": ((9, 1), (11, 30)),
}


def last_day_of_month(year: int, month: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    # February
    return 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28


def parse_day_month_year(text: str) -> Optional[date]:
    m = re.search(r"(\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)\s*(\d{3,4})", text)
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2).lower()
    year = int(m.group(3))
    month = MONTHS.get(month_name)
    if not month:
        return None
    return date(year, month, day)


def parse_month_year(text: str, default_year: Optional[int]) -> Optional[Tuple[date, date]]:
    m = re.search(r"([A-Za-zäöüÄÖÜ]+)\s*(\d{3,4})", text)
    month_name = None
    year = None
    if m:
        month_name = m.group(1).lower()
        year = int(m.group(2))
    else:
        m = re.search(r"([A-Za-zäöüÄÖÜ]+)", text)
        if m:
            month_name = m.group(1).lower()
        year = default_year
    if not month_name or year is None:
        return None
    month = MONTHS.get(month_name)
    if not month:
        return None
    start = date(year, month, 1)
    end = date(year, month, last_day_of_month(year, month))
    return (start, end)


def parse_season(text: str, default_year: Optional[int]) -> Optional[Tuple[date, date]]:
    lowered = text.lower()
    for key, ((m1, d1), (m2, d2)) in SEASON_RANGES.items():
        if key in lowered:
            year = extract_year(lowered) or default_year
            if year is None:
                return None
            return (date(year, m1, d1), date(year, m2, d2))
    return None


def extract_year(text: str) -> Optional[int]:
    m = re.search(r"(\d{3,4})", text)
    if not m:
        return None
    return int(m.group(1))


def parse_single(text: str, default_year: Optional[int]) -> Optional[Tuple[date, date]]:
    lowered = text.lower()
    exact = parse_day_month_year(text)
    if exact:
        return (exact, exact)

    season = parse_season(lowered, default_year)
    if season:
        return season

    month_year = parse_month_year(lowered, default_year)
    if month_year:
        return month_year

    year = extract_year(lowered) or default_year
    if year is None:
        return None
    return (date(year, 1, 1), date(year, 12, 31))


def normalize_raw(raw: str) -> str:
    text = raw.strip()
    text = text.replace("–", "-")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("(", " ").replace(")", " ")
    return text.strip()


def parse_range(text: str) -> Optional[Tuple[date, date]]:
    normalized = normalize_raw(text)
    normalized = re.sub(r"^datierung unsicher:\s*", "", normalized, flags=re.IGNORECASE)
    if ";" in normalized:
        normalized = normalized.split(";", 1)[0].strip()
    if ":" in normalized:
        _, rest = normalized.split(":", 1)
        normalized = rest.strip()

    normalized = normalized.replace("zw.", "zwischen").replace("u.", "und")

    between = re.search(r"zwischen\s+(.+?)\s+und\s+(.+)", normalized, flags=re.IGNORECASE)
    if between:
        a = between.group(1).strip()
        b = between.group(2).strip()
        year_b = extract_year(b)
        start = parse_single(a, year_b)
        end = parse_single(b, year_b)
        if start and end:
            return (start[0], end[1])

    if " bis " in normalized:
        left, right = normalized.split(" bis ", 1)
        year_right = extract_year(right)
        start = parse_single(left.strip(), year_right)
        end = parse_single(right.strip(), year_right)
        if start and end:
            return (start[0], end[1])

    if " / " in normalized:
        left, right = normalized.split(" / ", 1)
        year_right = extract_year(right)
        start = parse_single(left.strip(), year_right)
        end = parse_single(right.strip(), year_right)
        if start and end:
            return (start[0], end[1])

    if " und " in normalized and not re.search(r"\d{1,2}\.\s*[A-Za-zäöüÄÖÜ]+\s*\d{3,4}", normalized):
        left, right = normalized.split(" und ", 1)
        year_right = extract_year(right)
        start = parse_single(left.strip(), year_right)
        end = parse_single(right.strip(), year_right)
        if start and end:
            return (start[0], end[1])

    return None


def parse_datierung(raw: str) -> Optional[Tuple[date, date]]:
    if not raw:
        return None
    normalized = normalize_raw(raw)
    rng = parse_range(normalized)
    if rng:
        return rng
    return parse_single(normalized, None)


def read_jsonl(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    items = []
    for row in read_jsonl(CORPUS_PATH):
        md = row.get("metadata") or {}
        raw = md.get("Datierung")
        if not raw:
            continue
        rng = parse_datierung(raw)
        if not rng:
            continue
        start, end = rng
        items.append(
            {
                "doc_id": row.get("doc_id"),
                "title": row.get("title"),
                "date_raw": raw,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )

    items.sort(key=lambda x: (x["start"], x["doc_id"] or ""))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "items": items,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"items: {len(items)}")


if __name__ == "__main__":
    main()
