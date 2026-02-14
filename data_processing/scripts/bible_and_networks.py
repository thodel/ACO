#!/usr/bin/env python3
"""Detect Bible references (OSIS) and build person networks (GEXF)."""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET

OUTPUT_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/output"
CORPUS_PATH = os.path.join(OUTPUT_DIR, "corpus.jsonl")
REGISTER_PATH = os.path.join(OUTPUT_DIR, "register.json")
DOC_MAP_PATH = os.path.join(OUTPUT_DIR, "doc_id_map.json")

NETWORK_DIR = os.path.join(OUTPUT_DIR, "networks")

NT_BOOKS = {
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph",
    "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb",
    "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
}

OSIS_TO_GERMAN = {
    "Gen": "Genesis",
    "Exod": "Exodus",
    "Lev": "Levitikus",
    "Num": "Numeri",
    "Deut": "Deuteronomium",
    "Josh": "Josua",
    "Judg": "Richter",
    "Ruth": "Rut",
    "1Sam": "1 Samuel",
    "2Sam": "2 Samuel",
    "1Kgs": "1 Könige",
    "2Kgs": "2 Könige",
    "1Chr": "1 Chronik",
    "2Chr": "2 Chronik",
    "Ezra": "Esra",
    "Neh": "Nehemia",
    "Esth": "Ester",
    "Job": "Hiob",
    "Ps": "Psalmen",
    "Prov": "Sprüche",
    "Eccl": "Prediger",
    "Song": "Hoheslied",
    "Isa": "Jesaja",
    "Jer": "Jeremia",
    "Lam": "Klagelieder",
    "Ezek": "Ezechiel",
    "Dan": "Daniel",
    "Hos": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obad": "Obadja",
    "Jonah": "Jona",
    "Mic": "Micha",
    "Nah": "Nahum",
    "Hab": "Habakuk",
    "Zeph": "Zefanja",
    "Hag": "Haggai",
    "Zech": "Sacharja",
    "Mal": "Maleachi",
    "Tob": "Tobit",
    "Jdt": "Judit",
    "Wis": "Weisheit",
    "Sir": "Sirach",
    "Bar": "Baruch",
    "1Macc": "1 Makkabäer",
    "2Macc": "2 Makkabäer",
    "3Macc": "3 Makkabäer",
    "4Macc": "4 Makkabäer",
    "Matt": "Matthäus",
    "Mark": "Markus",
    "Luke": "Lukas",
    "John": "Johannes",
    "Acts": "Apostelgeschichte",
    "Rom": "Römer",
    "1Cor": "1 Korinther",
    "2Cor": "2 Korinther",
    "Gal": "Galater",
    "Eph": "Epheser",
    "Phil": "Philipper",
    "Col": "Kolosser",
    "1Thess": "1 Thessalonicher",
    "2Thess": "2 Thessalonicher",
    "1Tim": "1 Timotheus",
    "2Tim": "2 Timotheus",
    "Titus": "Titus",
    "Phlm": "Philemon",
    "Heb": "Hebräer",
    "Jas": "Jakobus",
    "1Pet": "1 Petrus",
    "2Pet": "2 Petrus",
    "1John": "1 Johannes",
    "2John": "2 Johannes",
    "3John": "3 Johannes",
    "Jude": "Judas",
    "Rev": "Offenbarung",
}


def get_testament(book: str) -> Optional[str]:
    if not book:
        return None
    return "NT" if book in NT_BOOKS else "OT"


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def safe_xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse_int(num: str | None) -> Optional[int]:
    if not num:
        return None
    num = re.sub(r"\(.*?\)", "", num)
    try:
        return int(num)
    except ValueError:
        return None


def roman_to_int(s: str) -> Optional[int]:
    s = s.upper()
    if s == "I":
        return 1
    if s == "II":
        return 2
    if s == "III":
        return 3
    return None


def osis_to_german(osis: str) -> str:
    if not osis:
        return osis
    if "." in osis:
        book, rest = osis.split(".", 1)
        return f"{OSIS_TO_GERMAN.get(book, book)}.{rest}"
    return OSIS_TO_GERMAN.get(osis, osis)


NON_NUMBERED = {
    "gen": "Gen",
    "genesis": "Gen",
    "ex": "Exod",
    "exod": "Exod",
    "exodus": "Exod",
    "lev": "Lev",
    "num": "Num",
    "dtn": "Deut",
    "deut": "Deut",
    "deuteronomium": "Deut",
    "jos": "Josh",
    "josua": "Josh",
    "ri": "Judg",
    "richter": "Judg",
    "rut": "Ruth",
    "ruth": "Ruth",
    "tob": "Tob",
    "tobit": "Tob",
    "jdt": "Jdt",
    "judit": "Jdt",
    "est": "Esth",
    "ester": "Esth",
    "ijob": "Job",
    "hiob": "Job",
    "job": "Job",
    "ps": "Ps",
    "psalm": "Ps",
    "psalmen": "Ps",
    "spr": "Prov",
    "sprich": "Prov",
    "sprueche": "Prov",
    "sprüche": "Prov",
    "koh": "Eccl",
    "kohelet": "Eccl",
    "pred": "Eccl",
    "prediger": "Eccl",
    "hld": "Song",
    "hoheslied": "Song",
    "hohes lied": "Song",
    "cant": "Song",
    "weish": "Wis",
    "weisheit": "Wis",
    "sap": "Wis",
    "sir": "Sir",
    "sirach": "Sir",
    "jes": "Isa",
    "jesaja": "Isa",
    "jer": "Jer",
    "jeremia": "Jer",
    "klgl": "Lam",
    "klg": "Lam",
    "klagelieder": "Lam",
    "bar": "Bar",
    "baruch": "Bar",
    "ez": "Ezek",
    "ezechiel": "Ezek",
    "hes": "Ezek",
    "dan": "Dan",
    "daniel": "Dan",
    "hos": "Hos",
    "hosea": "Hos",
    "joel": "Joel",
    "am": "Amos",
    "amos": "Amos",
    "ob": "Obad",
    "obad": "Obad",
    "obadja": "Obad",
    "jona": "Jonah",
    "jonah": "Jonah",
    "mi": "Mic",
    "micha": "Mic",
    "nah": "Nah",
    "nahum": "Nah",
    "hab": "Hab",
    "habakuk": "Hab",
    "zef": "Zeph",
    "zeph": "Zeph",
    "hag": "Hag",
    "haggai": "Hag",
    "sach": "Zech",
    "sacharja": "Zech",
    "sacharias": "Zech",
    "mal": "Mal",
    "maleachi": "Mal",
    "mt": "Matt",
    "matth": "Matt",
    "matthäus": "Matt",
    "matthaeus": "Matt",
    "mk": "Mark",
    "mar": "Mark",
    "markus": "Mark",
    "lk": "Luke",
    "luk": "Luke",
    "lukas": "Luke",
    "joh": "John",
    "johannes": "John",
    "ioh": "John",
    "apg": "Acts",
    "apostelgeschichte": "Acts",
    "röm": "Rom",
    "roem": "Rom",
    "rom": "Rom",
    "gal": "Gal",
    "eph": "Eph",
    "epheser": "Eph",
    "phil": "Phil",
    "kol": "Col",
    "kolosser": "Col",
    "tit": "Titus",
    "titus": "Titus",
    "hebr": "Heb",
    "heb": "Heb",
    "hebräer": "Heb",
    "hebraeer": "Heb",
    "jak": "Jas",
    "jakobus": "Jas",
    "jud": "Jude",
    "judas": "Jude",
    "offb": "Rev",
    "apk": "Rev",
    "apok": "Rev",
    "apokalypse": "Rev",
}

NUMBERED_BASE_MAP = {
    "sam": "Sam",
    "samuel": "Sam",
    "kön": "Kgs",
    "koen": "Kgs",
    "könige": "Kgs",
    "koenige": "Kgs",
    "chr": "Chr",
    "chron": "Chr",
    "chronik": "Chr",
    "makk": "Macc",
    "makkabäer": "Macc",
    "makkabaer": "Macc",
    "kor": "Cor",
    "korinther": "Cor",
    "thes": "Thess",
    "thess": "Thess",
    "thessalonicher": "Thess",
    "tim": "Tim",
    "timotheus": "Tim",
    "petr": "Pet",
    "petrus": "Pet",
    "joh": "John",
    "johannes": "John",
}

# Build book regex
BOOK_VARIANTS = sorted(set(list(NON_NUMBERED.keys()) + list(NUMBERED_BASE_MAP.keys())), key=len, reverse=True)
BOOK_PATTERN = r"|".join(re.escape(b) for b in BOOK_VARIANTS)
BOOK_RE = re.compile(
    rf"(?<!\w)(?P<prefix>(?:[1-3]|I{{1,3}}))?\s*(?P<book>{BOOK_PATTERN})\b",
    flags=re.IGNORECASE,
)


def resolve_book(prefix: str | None, book_raw: str) -> Optional[str]:
    book_key = book_raw.lower()
    num = None
    if prefix:
        prefix = prefix.strip()
        if prefix.isdigit():
            num = int(prefix)
        else:
            num = roman_to_int(prefix)
    if num is not None:
        base = NUMBERED_BASE_MAP.get(book_key)
        if base:
            return f"{num}{base}"
        return None
    # no prefix
    return NON_NUMBERED.get(book_key)


def parse_reference_sequence(text: str, start: int) -> Tuple[List[Dict], int]:
    refs: List[Dict] = []
    i = start
    n = len(text)

    def skip_ws(j: int) -> int:
        while j < n and text[j].isspace():
            j += 1
        return j

    while i < n:
        i = skip_ws(i)
        if i >= n or not text[i].isdigit():
            break

        m = re.match(r"(?P<chap>\d{1,3}(?:\(\d{1,3}\))?)", text[i:])
        if not m:
            break
        chap_raw = m.group("chap")
        chap = parse_int(chap_raw)
        i += m.end()

        verse_raw = None
        verse_end_raw = None
        i = skip_ws(i)
        if i < n and text[i] in ",:":
            j = skip_ws(i + 1)
            if j < n and text[j].isdigit():
                mv = re.match(r"(?P<verse>\d{1,3}(?:\(\d{1,3}\))?)(?:\s*[-–]\s*(?P<verse_end>\d{{1,3}}))?", text[j:])
                if mv:
                    verse_raw = mv.group("verse")
                    verse_end_raw = mv.group("verse_end")
                    i = j + mv.end()
                else:
                    i = j
            else:
                # ignore dangling punctuation
                i = j

        qualifier = None
        q = re.match(r"\s*(f{1,2})\.", text[i:])
        if q:
            qualifier = q.group(1)
            i += q.end()

        refs.append(
            {
                "chapter": chap,
                "chapter_raw": chap_raw,
                "verse": parse_int(verse_raw),
                "verse_raw": verse_raw,
                "verse_end": parse_int(verse_end_raw),
                "verse_end_raw": verse_end_raw,
                "qualifier": qualifier,
            }
        )

        k = skip_ws(i)
        if k < n and text[k] == ";":
            i = k + 1
            break
        if k < n and text[k] in ".,":
            k2 = skip_ws(k + 1)
            if k2 < n and text[k2].isdigit():
                i = k2
                continue
        i = k
        break

    return refs, i


def detect_bible_refs(text: str) -> List[Dict]:
    refs_out: List[Dict] = []
    if not text:
        return refs_out

    for match in BOOK_RE.finditer(text):
        prefix = match.group("prefix")
        book_raw = match.group("book")
        book = resolve_book(prefix, book_raw)
        if not book:
            continue

        # ensure a digit follows soon after
        j = match.end()
        while j < len(text) and text[j].isspace():
            j += 1
        if j >= len(text) or not text[j].isdigit():
            continue

        ref_list, _ = parse_reference_sequence(text, j)
        for ref in ref_list:
            osis = None
            if ref["chapter"] is not None and ref["verse"] is not None:
                if ref["verse_end"]:
                    osis = f"{book}.{ref['chapter']}.{ref['verse']}-{ref['verse_end']}"
                else:
                    osis = f"{book}.{ref['chapter']}.{ref['verse']}"
            elif ref["chapter"] is not None:
                osis = f"{book}.{ref['chapter']}"

            refs_out.append(
                {
                    "book": book,
                    "osis": osis,
                    "raw_book": (prefix or "") + (" " if prefix else "") + book_raw,
                    **ref,
                }
            )

    return refs_out


def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_jsonl(path: str, rows: Iterable[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_bible_outputs() -> None:
    bible_rows: List[Dict] = []
    book_counts = defaultdict(int)
    osis_counts = defaultdict(int)

    for row in read_jsonl(CORPUS_PATH):
        doc_id = row.get("doc_id")
        text = " ".join([row.get("text_main", ""), row.get("text_notes", "")])
        text = normalize_space(text)
        refs = detect_bible_refs(text)
        for ref in refs:
            if ref.get("book"):
                book_counts[osis_to_german(ref["book"])] += 1
            if ref.get("osis"):
                osis_counts[osis_to_german(ref["osis"])] += 1
        bible_rows.append({"doc_id": doc_id, "refs": refs})

    write_jsonl(os.path.join(OUTPUT_DIR, "bible_refs.jsonl"), bible_rows)
    write_json(
        os.path.join(OUTPUT_DIR, "bible_index.json"),
        {
            "generated_on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "books": dict(sorted(book_counts.items())),
            "osis": dict(sorted(osis_counts.items())),
        },
    )
    return None


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "item"


def load_doc_titles() -> Dict[str, str]:
    titles: Dict[str, str] = {}
    for row in read_jsonl(CORPUS_PATH):
        doc_id = row.get("doc_id")
        title = row.get("title") or doc_id
        if doc_id:
            titles[doc_id] = title
    return titles


def build_person_networks() -> None:
    with open(REGISTER_PATH, "r", encoding="utf-8") as f:
        register = json.load(f)

    persons = register.get("registerData", {}).get("Personen", [])

    doc_titles = load_doc_titles()

    # Person-Document edges
    person_doc_edges = []
    for entry in persons:
        label = entry.get("label")
        loc = entry.get("loc", {})
        for doc_id, occs in loc.items():
            weight = len(occs)
            if weight == 0:
                continue
            person_doc_edges.append((label, doc_id, weight))

    # Person-Person co-occurrence by document
    doc_to_persons: Dict[str, List[str]] = defaultdict(list)
    for entry in persons:
        label = entry.get("label")
        for doc_id in entry.get("loc", {}).keys():
            doc_to_persons[doc_id].append(label)

    pair_weights = defaultdict(int)
    for doc_id, plist in doc_to_persons.items():
        unique = sorted(set(plist))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                pair_weights[(unique[i], unique[j])] += 1

    person_person_edges = [(a, b, w) for (a, b), w in pair_weights.items()]

    os.makedirs(NETWORK_DIR, exist_ok=True)
    write_gexf_person_document(
        os.path.join(NETWORK_DIR, "person_document.gexf"),
        person_doc_edges,
        doc_titles,
    )
    write_gexf_person_person(
        os.path.join(NETWORK_DIR, "person_person.gexf"),
        person_person_edges,
    )


def build_bible_networks() -> None:
    os.makedirs(NETWORK_DIR, exist_ok=True)

    doc_titles = load_doc_titles()
    bible_doc_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    doc_to_bible: Dict[str, List[str]] = defaultdict(list)

    for row in read_jsonl(os.path.join(OUTPUT_DIR, "bible_refs.jsonl")):
        doc_id = row.get("doc_id")
        refs = row.get("refs", [])
        for ref in refs:
            osis = ref.get("osis")
            if not osis:
                continue
            bible_doc_counts[(osis, doc_id)] += 1
            doc_to_bible[doc_id].append(osis)

    bible_doc_edges = [(osis, doc, w) for (osis, doc), w in bible_doc_counts.items()]

    # Bible-Bible co-occurrence per document
    pair_weights = defaultdict(int)
    for doc_id, blist in doc_to_bible.items():
        unique = sorted(set(blist))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                pair_weights[(unique[i], unique[j])] += 1

    bible_bible_edges = [(a, b, w) for (a, b), w in pair_weights.items()]

    write_gexf_bible_document(
        os.path.join(NETWORK_DIR, "bible_document.gexf"),
        bible_doc_edges,
        doc_titles,
    )
    write_gexf_bible_bible(
        os.path.join(NETWORK_DIR, "bible_bible.gexf"),
        bible_bible_edges,
    )


def build_bible_book_networks() -> None:
    os.makedirs(NETWORK_DIR, exist_ok=True)

    doc_titles = load_doc_titles()
    book_doc_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    doc_to_books: Dict[str, List[str]] = defaultdict(list)

    for row in read_jsonl(os.path.join(OUTPUT_DIR, "bible_refs.jsonl")):
        doc_id = row.get("doc_id")
        refs = row.get("refs", [])
        for ref in refs:
            book = ref.get("book")
            if not book:
                continue
            book_doc_counts[(book, doc_id)] += 1
            doc_to_books[doc_id].append(book)

    book_doc_edges = [(book, doc, w) for (book, doc), w in book_doc_counts.items()]

    pair_weights = defaultdict(int)
    for doc_id, blist in doc_to_books.items():
        unique = sorted(set(blist))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                pair_weights[(unique[i], unique[j])] += 1

    book_book_edges = [(a, b, w) for (a, b), w in pair_weights.items()]

    write_gexf_bible_document(
        os.path.join(NETWORK_DIR, "bible_book_document.gexf"),
        book_doc_edges,
        doc_titles,
    )
    write_gexf_bible_bible(
        os.path.join(NETWORK_DIR, "bible_book_book.gexf"),
        book_book_edges,
    )


def write_gexf_person_document(path: str, edges: List[Tuple[str, str, int]], doc_titles: Dict[str, str]) -> None:
    node_ids: Dict[str, str] = {}
    nodes: List[Tuple[str, str, str, Optional[str]]] = []

    def get_node_id(kind: str, label: str) -> str:
        key = f"{kind}:{label}"
        if key not in node_ids:
            base = slugify(label)
            node_id = f"{kind}:{base}"
            # avoid collisions
            i = 1
            while node_id in node_ids.values():
                i += 1
                node_id = f"{kind}:{base}_{i}"
            node_ids[key] = node_id
        return node_ids[key]

    # collect nodes
    for person, doc, _ in edges:
        pid = get_node_id("p", person)
        if pid not in [n[0] for n in nodes]:
            nodes.append((pid, person, "person", None))
        did = get_node_id("d", doc)
        if did not in [n[0] for n in nodes]:
            nodes.append((did, doc, "document", doc_titles.get(doc)))

    gexf = ET.Element("gexf", attrib={"xmlns": "http://www.gexf.net/1.2draft", "version": "1.2"})
    graph = ET.SubElement(gexf, "graph", attrib={"mode": "static", "defaultedgetype": "undirected"})

    attributes = ET.SubElement(graph, "attributes", attrib={"class": "node"})
    ET.SubElement(attributes, "attribute", attrib={"id": "0", "title": "type", "type": "string"})
    ET.SubElement(attributes, "attribute", attrib={"id": "1", "title": "title", "type": "string"})

    nodes_el = ET.SubElement(graph, "nodes")
    for node_id, label, ntype, title in nodes:
        node_el = ET.SubElement(nodes_el, "node", attrib={"id": node_id, "label": label})
        attvalues = ET.SubElement(node_el, "attvalues")
        ET.SubElement(attvalues, "attvalue", attrib={"for": "0", "value": ntype})
        if title:
            ET.SubElement(attvalues, "attvalue", attrib={"for": "1", "value": title})

    edges_el = ET.SubElement(graph, "edges")
    for idx, (person, doc, weight) in enumerate(edges):
        source = get_node_id("p", person)
        target = get_node_id("d", doc)
        ET.SubElement(
            edges_el,
            "edge",
            attrib={"id": str(idx), "source": source, "target": target, "weight": str(weight)},
        )

    tree = ET.ElementTree(gexf)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def write_gexf_person_person(path: str, edges: List[Tuple[str, str, int]]) -> None:
    node_ids: Dict[str, str] = {}
    nodes: List[Tuple[str, str]] = []

    def get_node_id(label: str) -> str:
        if label not in node_ids:
            base = slugify(label)
            node_id = f"p:{base}"
            i = 1
            while node_id in node_ids.values():
                i += 1
                node_id = f"p:{base}_{i}"
            node_ids[label] = node_id
        return node_ids[label]

    for a, b, _ in edges:
        for label in (a, b):
            nid = get_node_id(label)
            if nid not in [n[0] for n in nodes]:
                nodes.append((nid, label))

    gexf = ET.Element("gexf", attrib={"xmlns": "http://www.gexf.net/1.2draft", "version": "1.2"})
    graph = ET.SubElement(gexf, "graph", attrib={"mode": "static", "defaultedgetype": "undirected"})

    attributes = ET.SubElement(graph, "attributes", attrib={"class": "node"})
    ET.SubElement(attributes, "attribute", attrib={"id": "0", "title": "type", "type": "string"})

    nodes_el = ET.SubElement(graph, "nodes")
    for node_id, label in nodes:
        node_el = ET.SubElement(nodes_el, "node", attrib={"id": node_id, "label": label})
        attvalues = ET.SubElement(node_el, "attvalues")
        ET.SubElement(attvalues, "attvalue", attrib={"for": "0", "value": "person"})

    edges_el = ET.SubElement(graph, "edges")
    for idx, (a, b, weight) in enumerate(edges):
        ET.SubElement(
            edges_el,
            "edge",
            attrib={"id": str(idx), "source": get_node_id(a), "target": get_node_id(b), "weight": str(weight)},
        )

    tree = ET.ElementTree(gexf)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def write_gexf_bible_document(path: str, edges: List[Tuple[str, str, int]], doc_titles: Dict[str, str]) -> None:
    node_ids: Dict[str, str] = {}
    nodes: List[Tuple[str, str, str, Optional[str], Optional[str]]] = []

    def get_node_id(kind: str, label: str) -> str:
        key = f"{kind}:{label}"
        if key not in node_ids:
            base = slugify(label)
            node_id = f"{kind}:{base}"
            i = 1
            while node_id in node_ids.values():
                i += 1
                node_id = f"{kind}:{base}_{i}"
            node_ids[key] = node_id
        return node_ids[key]

    for osis, doc, _ in edges:
        bid = get_node_id("b", osis)
        if bid not in [n[0] for n in nodes]:
            book = osis.split(".", 1)[0] if "." in osis else osis
            testament = get_testament(book)
            nodes.append((bid, osis, "bible", book, None, testament))
        did = get_node_id("d", doc)
        if did not in [n[0] for n in nodes]:
            nodes.append((did, doc, "document", None, doc_titles.get(doc), None))

    gexf = ET.Element("gexf", attrib={"xmlns": "http://www.gexf.net/1.2draft", "version": "1.2"})
    graph = ET.SubElement(gexf, "graph", attrib={"mode": "static", "defaultedgetype": "undirected"})

    attributes = ET.SubElement(graph, "attributes", attrib={"class": "node"})
    ET.SubElement(attributes, "attribute", attrib={"id": "0", "title": "type", "type": "string"})
    ET.SubElement(attributes, "attribute", attrib={"id": "1", "title": "book", "type": "string"})
    ET.SubElement(attributes, "attribute", attrib={"id": "2", "title": "title", "type": "string"})
    ET.SubElement(attributes, "attribute", attrib={"id": "3", "title": "testament", "type": "string"})

    nodes_el = ET.SubElement(graph, "nodes")
    for node_id, label, ntype, book, title, testament in nodes:
        node_el = ET.SubElement(nodes_el, "node", attrib={"id": node_id, "label": label})
        attvalues = ET.SubElement(node_el, "attvalues")
        ET.SubElement(attvalues, "attvalue", attrib={"for": "0", "value": ntype})
        if book:
            ET.SubElement(attvalues, "attvalue", attrib={"for": "1", "value": book})
        if title:
            ET.SubElement(attvalues, "attvalue", attrib={"for": "2", "value": title})
        if testament:
            ET.SubElement(attvalues, "attvalue", attrib={"for": "3", "value": testament})

    edges_el = ET.SubElement(graph, "edges")
    for idx, (osis, doc, weight) in enumerate(edges):
        source = get_node_id("b", osis)
        target = get_node_id("d", doc)
        ET.SubElement(
            edges_el,
            "edge",
            attrib={"id": str(idx), "source": source, "target": target, "weight": str(weight)},
        )

    tree = ET.ElementTree(gexf)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def write_gexf_bible_bible(path: str, edges: List[Tuple[str, str, int]]) -> None:
    node_ids: Dict[str, str] = {}
    nodes: List[Tuple[str, str, str, str | None, str | None]] = []

    def get_node_id(label: str) -> str:
        if label not in node_ids:
            base = slugify(label)
            node_id = f"b:{base}"
            i = 1
            while node_id in node_ids.values():
                i += 1
                node_id = f"b:{base}_{i}"
            node_ids[label] = node_id
        return node_ids[label]

    for a, b, _ in edges:
        for label in (a, b):
            nid = get_node_id(label)
            if nid not in [n[0] for n in nodes]:
                book = label.split(".", 1)[0] if "." in label else label
                testament = get_testament(book)
                nodes.append((nid, label, "bible", book, testament))

    gexf = ET.Element("gexf", attrib={"xmlns": "http://www.gexf.net/1.2draft", "version": "1.2"})
    graph = ET.SubElement(gexf, "graph", attrib={"mode": "static", "defaultedgetype": "undirected"})

    attributes = ET.SubElement(graph, "attributes", attrib={"class": "node"})
    ET.SubElement(attributes, "attribute", attrib={"id": "0", "title": "type", "type": "string"})
    ET.SubElement(attributes, "attribute", attrib={"id": "1", "title": "book", "type": "string"})
    ET.SubElement(attributes, "attribute", attrib={"id": "2", "title": "testament", "type": "string"})

    nodes_el = ET.SubElement(graph, "nodes")
    for node_id, label, ntype, book, testament in nodes:
        node_el = ET.SubElement(nodes_el, "node", attrib={"id": node_id, "label": label})
        attvalues = ET.SubElement(node_el, "attvalues")
        ET.SubElement(attvalues, "attvalue", attrib={"for": "0", "value": ntype})
        if book:
            ET.SubElement(attvalues, "attvalue", attrib={"for": "1", "value": book})
        if testament:
            ET.SubElement(attvalues, "attvalue", attrib={"for": "2", "value": testament})

    edges_el = ET.SubElement(graph, "edges")
    for idx, (a, b, weight) in enumerate(edges):
        ET.SubElement(
            edges_el,
            "edge",
            attrib={"id": str(idx), "source": get_node_id(a), "target": get_node_id(b), "weight": str(weight)},
        )

    tree = ET.ElementTree(gexf)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    build_bible_outputs()
    build_person_networks()
    build_bible_networks()
    build_bible_book_networks()
    print("Bible refs + networks generated")


if __name__ == "__main__":
    main()
