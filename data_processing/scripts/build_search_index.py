#!/usr/bin/env python3
"""Build a multilingual (char n-gram) embedding index and query expansion vocab."""

from __future__ import annotations

import json
import os
import re
import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

OUTPUT_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/output"
CORPUS_PATH = os.path.join(OUTPUT_DIR, "corpus.jsonl")
SEARCH_DIR = os.path.join(OUTPUT_DIR, "search_index")

DIM = 256
NGRAM_MIN = 3
NGRAM_MAX = 5
MIN_DF = 2
DECIMALS = 6
TOP_EXPANSION = 5
MIN_SIM = 0.35

TOKEN_RE = re.compile(r"[A-Za-z\u00C0-\u024F\u0370-\u03FF\u1F00-\u1FFF]+")

STOPWORDS = set(
    """
    der die das des dem den und oder ein eine eines einer einem einen
    mit von zu zum zur im in am an auf aus bei durch für gegen ohne um
    ist sind war waren wird werden wurde wurden sein seine seinen ihrer ihre
    the and of to in for on with a an is are was were be been being
    et non sed nec ut ad ex qui quae quod
    """.split()
)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def hash_to_index(token: str, dim: int) -> Tuple[int, int]:
    digest = hashlib.md5(token.encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "little") % dim
    sign = 1 if digest[4] % 2 == 0 else -1
    return idx, sign


def token_vector_sparse(token: str) -> List[Tuple[int, float]]:
    token = token.lower()
    t = f"<{token}>"
    feats: Dict[int, float] = {}

    # char n-grams
    for n in range(NGRAM_MIN, NGRAM_MAX + 1):
        if len(t) < n:
            continue
        for i in range(len(t) - n + 1):
            ngram = t[i : i + n]
            idx, sign = hash_to_index(ngram, DIM)
            feats[idx] = feats.get(idx, 0.0) + float(sign)

    # full token hash
    idx, sign = hash_to_index(token, DIM)
    feats[idx] = feats.get(idx, 0.0) + float(sign)

    return list(feats.items())


def l2_normalize(vec: List[float]) -> List[float]:
    norm = sum(v * v for v in vec) ** 0.5
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def quantize(vec: List[float]) -> List[float]:
    return [round(v, DECIMALS) for v in vec]


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


def build_index() -> None:
    os.makedirs(SEARCH_DIR, exist_ok=True)

    docs_meta: List[Dict] = []
    doc_tokens: Dict[str, List[str]] = {}
    df = Counter()

    for row in read_jsonl(CORPUS_PATH):
        doc_id = row.get("doc_id")
        title = row.get("title")
        lang = row.get("lang")
        metadata = row.get("metadata", {})
        text = normalize_space(" ".join([row.get("text_main", ""), row.get("text_notes", "")]))
        tokens = [t for t in tokenize(text) if len(t) >= 2 and t not in STOPWORDS]
        doc_tokens[doc_id] = tokens

        for t in set(tokens):
            df[t] += 1

        docs_meta.append(
            {
                "doc_id": doc_id,
                "title": title,
                "lang": lang,
                "metadata": metadata,
                "token_count": len(tokens),
                "text_len": len(text),
                "snippet": text[:400],
            }
        )

    vocab = {t for t, c in df.items() if c >= MIN_DF and len(t) >= 3 and t not in STOPWORDS}

    token_cache: Dict[str, List[Tuple[int, float]]] = {}

    def get_token_sparse(tok: str) -> List[Tuple[int, float]]:
        if tok not in token_cache:
            token_cache[tok] = token_vector_sparse(tok)
        return token_cache[tok]

    # document embeddings
    doc_embeddings = []
    for meta in docs_meta:
        doc_id = meta["doc_id"]
        vec = [0.0] * DIM
        for tok in doc_tokens.get(doc_id, []):
            for idx, val in get_token_sparse(tok):
                vec[idx] += val
        vec = l2_normalize(vec)
        doc_embeddings.append({"doc_id": doc_id, "vector": quantize(vec)})

    # vocab embeddings
    vocab_rows = []
    for tok in sorted(vocab):
        vec = [0.0] * DIM
        for idx, val in get_token_sparse(tok):
            vec[idx] += val
        vec = l2_normalize(vec)
        vocab_rows.append({"token": tok, "df": df[tok], "vector": quantize(vec)})

    write_jsonl(os.path.join(SEARCH_DIR, "docs.jsonl"), docs_meta)
    write_jsonl(os.path.join(SEARCH_DIR, "doc_embeddings.jsonl"), doc_embeddings)
    write_jsonl(os.path.join(SEARCH_DIR, "vocab.jsonl"), vocab_rows)

    write_json(
        os.path.join(SEARCH_DIR, "index_meta.json"),
        {
            "generated_on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "corpus": os.path.abspath(CORPUS_PATH),
            "embedding": {
                "method": "char_ngram_hash",
                "dim": DIM,
                "ngram_min": NGRAM_MIN,
                "ngram_max": NGRAM_MAX,
                "min_df": MIN_DF,
                "stopwords": len(STOPWORDS),
                "decimals": DECIMALS,
            },
            "query_expansion": {
                "top_k": TOP_EXPANSION,
                "min_sim": MIN_SIM,
                "source": "vocab.jsonl",
            },
            "counts": {
                "docs": len(docs_meta),
                "vocab": len(vocab_rows),
            },
        },
    )


if __name__ == "__main__":
    build_index()
    print("Search index built")
