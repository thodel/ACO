#!/usr/bin/env python3
"""Export GEXF networks to JSON (nodes + links)."""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, List

NETWORK_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/output/networks"


def strip_ns(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def parse_gexf(path: str) -> Dict:
    tree = ET.parse(path)
    root = tree.getroot()

    # map attribute id -> title
    attr_map: Dict[str, str] = {}
    for attr in root.findall(".//{http://www.gexf.net/1.2draft}attributes/{http://www.gexf.net/1.2draft}attribute"):
        attr_id = attr.get("id")
        title = attr.get("title")
        if attr_id and title:
            attr_map[attr_id] = title

    nodes: List[Dict] = []
    for node in root.findall(".//{http://www.gexf.net/1.2draft}node"):
        node_id = node.get("id")
        label = node.get("label")
        node_obj = {"id": node_id, "label": label}
        attvalues = node.find("{http://www.gexf.net/1.2draft}attvalues")
        if attvalues is not None:
            for att in attvalues.findall("{http://www.gexf.net/1.2draft}attvalue"):
                key = attr_map.get(att.get("for") or "", att.get("for") or "attr")
                val = att.get("value")
                if key and val is not None:
                    node_obj[key] = val
        nodes.append(node_obj)

    links: List[Dict] = []
    for edge in root.findall(".//{http://www.gexf.net/1.2draft}edge"):
        links.append(
            {
                "id": edge.get("id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "weight": float(edge.get("weight") or 1.0),
            }
        )

    return {"nodes": nodes, "links": links}


def main() -> None:
    for name in os.listdir(NETWORK_DIR):
        if not name.endswith(".gexf"):
            continue
        path = os.path.join(NETWORK_DIR, name)
        data = parse_gexf(path)
        out_path = os.path.join(NETWORK_DIR, os.path.splitext(name)[0] + ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
