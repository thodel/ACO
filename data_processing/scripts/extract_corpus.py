#!/usr/bin/env python3
"""Extract doc id map, register index, and canonical corpus from TEI files."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Iterable, Tuple
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS}

INPUT_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/input-dir"
INDEX_FILE = "/Users/TH_1/Documents/Repo/ACO/data_processing/input-dir/meta/99_Indices.xml"
OUTPUT_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/output"


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def iter_text(
    elem: ET.Element,
    skip_tags: Iterable[str] | None = None,
    skip_hidden: bool = False,
) -> str:
    skip = set(skip_tags or [])
    parts: List[str] = []

    def rec(e: ET.Element) -> None:
        if local_name(e.tag) in skip:
            return
        if skip_hidden:
            rend = e.get("rend") or e.get("rendition") or ""
            if "display:none" in rend:
                return
        if e.text:
            parts.append(e.text)
        for child in list(e):
            rec(child)
            if child.tail:
                parts.append(child.tail)

    rec(elem)
    return "".join(parts)


def list_doc_files(input_dir: str) -> List[str]:
    files = []
    for name in os.listdir(input_dir):
        path = os.path.join(input_dir, name)
        if not os.path.isfile(path):
            continue
        if not name.lower().endswith(".xml"):
            continue
        files.append(path)
    return sorted(files)


def derive_doc_id(stem: str) -> str:
    if "_" in stem:
        return stem.split("_", 1)[1]
    return stem


def parse_doc_id_map(doc_files: List[str]) -> Dict:
    docs = []
    for path in doc_files:
        filename = os.path.basename(path)
        stem = os.path.splitext(filename)[0]
        doc_id = derive_doc_id(stem)
        # prefix may include letters (e.g., 08a)
        prefix = stem.split("_", 1)[0]
        order = None
        m = re.match(r"^(\d+)", prefix)
        if m:
            order = int(m.group(1))
        docs.append({
            "filename": filename,
            "stem": stem,
            "doc_id": doc_id,
            "order": order,
        })
    return {
        "generated_on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_dir": INPUT_DIR,
        "docs": docs,
    }


DELIM_RE = re.compile(r"[\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A]")


def split_label_and_refs(text: str) -> Tuple[str, str]:
    # try unicode space delimiter first
    m = DELIM_RE.search(text)
    if m:
        label = text[: m.start()]
        rest = text[m.end() :]
        return label.strip(), rest.strip()
    # fallback: split on 2+ spaces
    m2 = re.search(r"\s{2,}", text)
    if m2:
        label = text[: m2.start()]
        rest = text[m2.end() :]
        return label.strip(), rest.strip()
    return text.strip(), ""


def cleanup_index_text(text: str) -> str:
    # Preserve en-space delimiters while normalizing ASCII whitespace
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = re.sub(r" +", " ", text)
    return text.strip()

def decompress_index_token(token: str) -> List[str]:
    token = token.strip()
    if not token:
        return []
    token = token.replace(";", "")
    if "," not in token:
        return [token]
    doc, locs = token.split(",", 1)
    doc = doc.strip()
    locs = locs.strip()
    if not locs:
        return [doc]

    if re.match(r"^Z", locs):
        parts = locs.split(".")
        return [f"{doc},Z.{p}" for p in parts[1:] if p]

    if re.match(r"^[\.\d]+$", locs):
        parts = locs.split(".")
        return [f"{doc},{p}" for p in parts if p]

    locs_tmp = re.sub(r"\.?([IVX]+)(,)", r"¦\1\2", locs)
    locs_tmp = re.sub(r"\.;$", "ø", locs_tmp)
    groups = [g for g in locs_tmp.split("¦") if g.strip()]
    out: List[str] = []
    for g in groups:
        if "," not in g:
            continue
        lib, rest = g.split(",", 1)
        rest = rest.replace("ø", "")
        for part in rest.split("."):
            part = part.strip()
            if not part:
                continue
            out.append(f"{doc},{lib}-{part.lower()}")
    return out


def parse_indices(index_file: str) -> Dict:
    tree = ET.parse(index_file)
    root = tree.getroot()

    register_data: Dict[str, List[Dict]] = {}

    body = root.find(".//tei:text/tei:body", NS)
    if body is None:
        return {
            "registerData": {},
            "meta": {
                "task": "parse-register",
                "generated-by": "extract_corpus.py",
                "generated-on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "description": "No body found",
            },
        }

    # prefer nested sections under a top-level Register div if present
    divs = body.findall(".//tei:div", NS)
    register_div = None
    for div in divs:
        head = div.find("tei:head", NS)
        head_text = normalize_space(iter_text(head, skip_tags={"milestone"})) if head is not None else ""
        if head_text.lower() == "register":
            register_div = div
            break

    if register_div is not None:
        divs = register_div.findall("tei:div", NS)

    for div in divs:
        head = div.find("tei:head", NS)
        head_text = ""
        if head is not None:
            head_text = normalize_space(iter_text(head, skip_tags={"milestone"}))
        if not head_text:
            head_text = "(Unlabeled)"
        entries: List[Dict] = []
        for p in div.findall("tei:p", NS):
            if p.get("rendition") != "#rp-p_index":
                continue
            raw_text = cleanup_index_text(iter_text(p, skip_tags={"milestone"}))
            if not raw_text:
                continue
            label, remainder = split_label_and_refs(raw_text)
            label = normalize_space(label)
            remainder = normalize_space(remainder)
            tokens = remainder.split()
            decompressed: List[str] = []
            for tok in tokens:
                decompressed.extend(decompress_index_token(tok))

            loc: Dict[str, List[str]] = {}
            loc_s: Dict[str, List[str]] = {}
            for entry in decompressed:
                if "," in entry:
                    doc_key = entry.split(",", 1)[0]
                else:
                    doc_key = entry
                loc.setdefault(doc_key, []).append(entry)
                loc_s.setdefault(doc_key, []).append(entry[len(doc_key) :])

            entries.append(
                {
                    "label": label,
                    "loc": loc,
                    "loc-s": loc_s,
                    "print": remainder,
                }
            )

        register_data[head_text] = entries

    return {
        "registerData": register_data,
        "meta": {
            "task": "parse-register",
            "generated-by": "extract_corpus.py",
            "generated-on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "description": "Derived from 99_Indices.xml",
        },
    }


def extract_metadata(body: ET.Element) -> Dict[str, str | List[str]]:
    metadata: Dict[str, str | List[str]] = {}
    misc: List[str] = []

    for p in body.findall(".//tei:p", NS):
        if p.get("rendition") != "#rp-kopf":
            continue
        text = normalize_space(iter_text(p, skip_tags={"note", "milestone"}, skip_hidden=True))
        if not text:
            continue
        if ":" in text:
            key, value = text.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in metadata:
                if isinstance(metadata[key], list):
                    metadata[key].append(value)
                else:
                    metadata[key] = [metadata[key], value]
            else:
                metadata[key] = value
        else:
            misc.append(text)

    if misc:
        metadata["_misc"] = misc

    return metadata


def extract_paragraphs(body: ET.Element) -> Tuple[List[str], List[str]]:
    main_paras: List[str] = []
    note_paras: List[str] = []

    for p in body.findall(".//tei:p", NS):
        if p.get("rendition") == "#rp-kopf":
            continue
        p_text = normalize_space(iter_text(p, skip_tags={"note", "milestone"}, skip_hidden=True))
        if p_text:
            main_paras.append(p_text)

    for note in body.findall(".//tei:note", NS):
        note_text = normalize_space(iter_text(note, skip_tags={"milestone"}, skip_hidden=True))
        if note_text:
            note_paras.append(note_text)

    return main_paras, note_paras


def extract_texts(body: ET.Element) -> Tuple[str, str, str]:
    # main text: all non-kopf paragraphs + heads, without notes
    main_parts: List[str] = []

    for head in body.findall(".//tei:head", NS):
        head_text = normalize_space(iter_text(head, skip_tags={"note", "milestone"}, skip_hidden=True))
        if head_text:
            main_parts.append(head_text)

    for p in body.findall(".//tei:p", NS):
        if p.get("rendition") == "#rp-kopf":
            continue
        p_text = normalize_space(iter_text(p, skip_tags={"note", "milestone"}, skip_hidden=True))
        if p_text:
            main_parts.append(p_text)

    text_main = normalize_space(" ".join(main_parts))

    # notes text
    note_parts: List[str] = []
    for note in body.findall(".//tei:note", NS):
        note_text = normalize_space(iter_text(note, skip_tags={"milestone"}, skip_hidden=True))
        if note_text:
            note_parts.append(note_text)
    text_notes = normalize_space(" ".join(note_parts))

    # full text
    text_full = normalize_space(" ".join([t for t in [text_main, text_notes] if t]))

    return text_main, text_notes, text_full


def build_corpus(doc_files: List[str]) -> List[Dict]:
    corpus: List[Dict] = []

    for path in doc_files:
        filename = os.path.basename(path)
        stem = os.path.splitext(filename)[0]
        doc_id = derive_doc_id(stem)

        tree = ET.parse(path)
        root = tree.getroot()

        body = root.find(".//tei:text/tei:body", NS)
        if body is None:
            continue

        # title from first head
        head = body.find(".//tei:head", NS)
        title = ""
        if head is not None:
            title = normalize_space(iter_text(head, skip_tags={"note", "milestone"}, skip_hidden=True))
            if title.startswith(doc_id):
                title = title[len(doc_id) :].lstrip()

        lang = None
        text_elem = root.find(".//tei:text", NS)
        if text_elem is not None:
            lang = text_elem.get(f"{{{XML_NS}}}lang")

        metadata = extract_metadata(body)
        paragraphs_main, paragraphs_notes = extract_paragraphs(body)
        text_main, text_notes, text_full = extract_texts(body)

        corpus.append(
            {
                "doc_id": doc_id,
                "filename": filename,
                "title": title,
                "lang": lang,
                "metadata": metadata,
                "text_main": text_main,
                "text_notes": text_notes,
                "text_full": text_full,
                "paragraphs": paragraphs_main,
                "paragraphs_notes": paragraphs_notes,
            }
        )

    return corpus


def write_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_jsonl(path: str, rows: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    doc_files = list_doc_files(INPUT_DIR)
    doc_id_map = parse_doc_id_map(doc_files)
    write_json(os.path.join(OUTPUT_DIR, "doc_id_map.json"), doc_id_map)

    register = parse_indices(INDEX_FILE)
    write_json(os.path.join(OUTPUT_DIR, "register.json"), register)

    corpus = build_corpus(doc_files)
    write_jsonl(os.path.join(OUTPUT_DIR, "corpus.jsonl"), corpus)

    print(f"Docs: {len(doc_files)}")
    print(f"Register sections: {len(register.get('registerData', {}))}")
    print(f"Corpus entries: {len(corpus)}")


if __name__ == "__main__":
    main()
