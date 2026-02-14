#!/usr/bin/env python3
"""Enrich register places with Pleiades geodata and export GeoJSON."""

from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

BASE = "/Users/TH_1/Documents/Repo/ACO/data_processing"
REGISTER_PATH = os.path.join(BASE, "output", "register.json")
PLEIADES_DIR = os.path.join(BASE, "external_data", "gis")
OUTPUT_REGISTER = os.path.join(BASE, "output", "register_geo.json")
OUTPUT_MISSING = os.path.join(BASE, "output", "places_without_geo.csv")
OUTPUT_AMBIGUOUS = os.path.join(BASE, "output", "places_ambiguous.csv")
OUTPUT_GEOJSON = os.path.join(BASE, "output", "geo", "places.geojson")


def norm(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    t = t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

GERMAN_SYNONYMS = {
    # Regions / countries (late antique usage)
    "afrika": ["africa"],
    "aegypten": ["aegyptus", "egypt"],
    "ägypten": ["aegyptus", "egypt"],
    "asien": ["asia"],
    "assyrien": ["assyria"],
    "babylon": ["babylon"],
    "galilaea": ["galilaea", "galilee", "galilea"],
    "galiläa": ["galilaea", "galilee", "galilea"],
    "judaea": ["judaea", "iudaea", "judea"],
    "judäa": ["judaea", "iudaea", "judea"],
    "palästina": ["palaestina", "palestina"],
    "palastina": ["palaestina", "palestina"],
    "syrien": ["syria"],
    "syrien": ["syria"],
    "italien": ["italia", "italy"],
    "rom": ["roma", "rome"],
    "konstantinopel": ["constantinopolis", "constantinople", "byzantion"],
    "jerusalem": ["hierosolyma", "ierusalem", "jerusalem"],
    "samosata": ["samosata"],
    "antiochia": ["antiochia", "antioch", "antiochia ad orontem"],
    "alexandria": ["alexandria", "alexandreia"],
    "nizäa": ["nicaea", "nikaia", "nicaea ad iznicum"],
    "thessaloniki": ["thessalonica", "thessalonike"],
    "korinth": ["corinth", "korinthos", "corinthus"],
    "ephesus": ["ephesus", "ephesos"],
    "karthago": ["carthago", "carthage"],
    "mailand": ["mediolanum", "milan"],
    "nazareth": ["nazareth", "nazara"],
    "bethlehem": ["bethlehem"],
    "samaria": ["samaria", "samareia"],
    "jordan": ["iordanes", "jordan"],
    "sinaï": ["sinai", "sina"],
    "sinai": ["sinai", "sina"],
    "zion": ["sion", "zion"],
    "ilIyrien": ["illyricum", "illyria"],
    "illyrien": ["illyricum", "illyria"],
    "pontus": ["pontus"],
    "galatien": ["galatia"],
    "bithynien": ["bithynia"],
    "phrygien": ["phrygia"],
    "pamphylien": ["pamphylia"],
    "pisidien": ["pisidia"],
    "kappadokien": ["cappadocia"],
}


def parse_point_wkt(wkt: str) -> Optional[Tuple[float, float]]:
    if not wkt:
        return None
    m = re.match(r"POINT \(([-\d\.]+) ([-\d\.]+)\)", wkt)
    if not m:
        return None
    lon = float(m.group(1))
    lat = float(m.group(2))
    return lat, lon


def load_places() -> Dict[str, Dict]:
    places_path = os.path.join(PLEIADES_DIR, "places.csv")
    places = {}
    with open(places_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("id")
            if not pid:
                continue
            places[pid] = {
                "title": row.get("title"),
                "uri": row.get("uri"),
                "rep_lat": row.get("representative_latitude"),
                "rep_lon": row.get("representative_longitude"),
                "location_precision": row.get("location_precision"),
            }
    return places


def load_location_points() -> Dict[str, Dict]:
    loc_path = os.path.join(PLEIADES_DIR, "location_points.csv")
    best = {}
    precision_rank = {"precise": 3, "rough": 2, "unknown": 1, "": 0, None: 0}

    with open(loc_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("place_id")
            if not pid:
                continue
            latlon = parse_point_wkt(row.get("geometry_wkt", ""))
            if not latlon:
                continue
            rank = precision_rank.get(row.get("location_precision"), 0)
            radius = row.get("accuracy_radius")
            radius_val = float(radius) if radius and radius.replace('.', '', 1).isdigit() else None
            existing = best.get(pid)
            if not existing:
                best[pid] = {
                    "lat": latlon[0],
                    "lon": latlon[1],
                    "location_precision": row.get("location_precision"),
                    "accuracy_radius": radius_val,
                }
                continue
            # choose better precision, or smaller radius
            existing_rank = precision_rank.get(existing.get("location_precision"), 0)
            if rank > existing_rank:
                best[pid] = {
                    "lat": latlon[0],
                    "lon": latlon[1],
                    "location_precision": row.get("location_precision"),
                    "accuracy_radius": radius_val,
                }
            elif rank == existing_rank and radius_val is not None:
                old_radius = existing.get("accuracy_radius")
                if old_radius is None or radius_val < old_radius:
                    best[pid] = {
                        "lat": latlon[0],
                        "lon": latlon[1],
                        "location_precision": row.get("location_precision"),
                        "accuracy_radius": radius_val,
                    }
    return best


def load_name_index() -> Dict[str, List[str]]:
    name_path = os.path.join(PLEIADES_DIR, "names.csv")
    idx: Dict[str, List[str]] = defaultdict(list)
    with open(name_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("place_id")
            if not pid:
                continue
            for key in ["title", "attested_form", "romanized_form_1", "romanized_form_2", "romanized_form_3"]:
                val = row.get(key) or ""
                if not val:
                    continue
                n = norm(val)
                if n:
                    if pid not in idx[n]:
                        idx[n].append(pid)
    return idx


def load_place_title_index(places: Dict[str, Dict]) -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = defaultdict(list)
    for pid, info in places.items():
        title = info.get("title")
        if not title:
            continue
        n = norm(title)
        if n:
            if pid not in idx[n]:
                idx[n].append(pid)
    return idx


def count_occurrences(loc: Dict[str, List[str]]) -> int:
    total = 0
    for v in (loc or {}).values():
        total += len(v)
    return total


def main() -> None:
    os.makedirs(os.path.dirname(OUTPUT_GEOJSON), exist_ok=True)

    with open(REGISTER_PATH, "r", encoding="utf-8") as f:
        register = json.load(f)

    places = load_places()
    location_points = load_location_points()
    name_index = load_name_index()
    title_index = load_place_title_index(places)

    def candidates_for(norm_label: str) -> List[str]:
        candidates = []
        if norm_label in name_index:
            candidates.extend(name_index[norm_label])
        if norm_label in title_index:
            for pid in title_index[norm_label]:
                if pid not in candidates:
                    candidates.append(pid)
        return candidates

    def match_place(label: str) -> Tuple[str, List[str], str | None]:
        n = norm(label)
        if not n:
            return ("no_match", [], None)
        candidates = candidates_for(n)
        match_variant = None
        if not candidates:
            # try synonym expansion
            for syn in GERMAN_SYNONYMS.get(n, []):
                candidates = candidates_for(norm(syn))
                if candidates:
                    match_variant = syn
                    break
        if not candidates:
            return ("no_match", [], None)
        if len(candidates) == 1:
            return ("match", candidates, match_variant)
        return ("ambiguous", candidates, match_variant)

    missing_rows = []
    features = []

    ambiguous_rows = []

    for entry in register.get("registerData", {}).get("Orte", []):
        label = entry.get("label")
        loc = entry.get("loc", {})
        count = count_occurrences(loc)

        status, candidates, match_variant = match_place(label)
        geo = {
            "match_status": status,
            "candidates": candidates,
            "match_variant": match_variant,
        }

        if status == "match":
            pid = candidates[0]
            info = places.get(pid, {})
            geo.update(
                {
                    "pleiades_place_id": pid,
                    "pleiades_uri": info.get("uri"),
                    "pleiades_title": info.get("title"),
                }
            )
            point = location_points.get(pid)
            lat = None
            lon = None
            if point:
                lat = point.get("lat")
                lon = point.get("lon")
                geo.update(
                    {
                        "lat": lat,
                        "lon": lon,
                        "location_precision": point.get("location_precision"),
                        "accuracy_radius": point.get("accuracy_radius"),
                        "source": "location_points",
                    }
                )
            else:
                rep_lat = info.get("rep_lat")
                rep_lon = info.get("rep_lon")
                if rep_lat and rep_lon:
                    lat = float(rep_lat)
                    lon = float(rep_lon)
                    geo.update(
                        {
                            "lat": lat,
                            "lon": lon,
                            "location_precision": info.get("location_precision"),
                            "source": "representative",
                        }
                    )
            if lat is not None and lon is not None:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "label": label,
                            "count": count,
                            "pleiades_place_id": pid,
                            "pleiades_uri": info.get("uri"),
                            "pleiades_title": info.get("title"),
                            "match_status": status,
                        },
                    }
                )
            else:
                missing_rows.append(
                    {
                        "label": label,
                        "reason": "no_coordinates",
                        "candidates": ";".join(candidates),
                        "match_variant": match_variant or "",
                    }
                )
        else:
            if status == "ambiguous":
                ambiguous_rows.append(
                    {
                        "label": label,
                        "candidates": ";".join(candidates),
                        "match_variant": match_variant or "",
                    }
                )
            missing_rows.append(
                {
                    "label": label,
                    "reason": status,
                    "candidates": ";".join(candidates),
                    "match_variant": match_variant or "",
                }
            )

        entry["geo"] = geo

    with open(OUTPUT_REGISTER, "w", encoding="utf-8") as f:
        json.dump(register, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_MISSING, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "reason", "candidates", "match_variant"])
        writer.writeheader()
        for row in missing_rows:
            writer.writerow(row)

    with open(OUTPUT_AMBIGUOUS, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "candidates", "match_variant"])
        writer.writeheader()
        for row in ambiguous_rows:
            writer.writerow(row)

    geojson = {"type": "FeatureCollection", "features": features}
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"matched: {len(features)}")
    print(f"missing: {len(missing_rows)}")


if __name__ == "__main__":
    main()
