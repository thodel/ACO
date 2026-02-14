#!/usr/bin/env python3
"""Simple semantic search + query expansion over the hashed char n-gram index.

Usage:
  python3 search_query.py "your query" --top 10
"""

from __future__ import annotations

import json
import os
import re
import sys
import hashlib
from typing import Dict, Iterable, List, Tuple

OUTPUT_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/output"
SEARCH_DIR = os.path.join(OUTPUT_DIR, "search_index")
SEARCH_DIR_BGE = os.path.join(OUTPUT_DIR, "search_index_bge_m3")


def resolve_model_path(model_path: str) -> str:
    # If given a HF cache root, resolve to the latest snapshot path
    if os.path.isdir(model_path) and not os.path.isfile(os.path.join(model_path, "config.json")):
        candidate = os.path.join(model_path, "models--BAAI--bge-m3", "snapshots")
        if os.path.isdir(candidate):
            snapshots = [os.path.join(candidate, d) for d in os.listdir(candidate)]
            snapshots = [d for d in snapshots if os.path.isdir(d)]
            if snapshots:
                valid = []
                for snap in snapshots:
                    has_tok = os.path.isfile(os.path.join(snap, "tokenizer.json")) or os.path.isfile(
                        os.path.join(snap, "sentencepiece.bpe.model")
                    )
                    has_cfg = os.path.isfile(os.path.join(snap, "config.json"))
                    if has_tok and has_cfg:
                        valid.append(snap)
                if valid:
                    valid.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                    return valid[0]
                snapshots.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                return snapshots[0]
    return model_path

DIM = 256
NGRAM_MIN = 3
NGRAM_MAX = 5
TOP_K = 5
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
    for n in range(NGRAM_MIN, NGRAM_MAX + 1):
        if len(t) < n:
            continue
        for i in range(len(t) - n + 1):
            ngram = t[i : i + n]
            idx, sign = hash_to_index(ngram, DIM)
            feats[idx] = feats.get(idx, 0.0) + float(sign)
    idx, sign = hash_to_index(token, DIM)
    feats[idx] = feats.get(idx, 0.0) + float(sign)
    return list(feats.items())

def embed_token(token: str) -> List[float]:
    vec = [0.0] * DIM
    for idx, val in token_vector_sparse(token):
        vec[idx] += val
    return l2_normalize(vec)


def l2_normalize(vec: List[float]) -> List[float]:
    norm = sum(v * v for v in vec) ** 0.5
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def embed_text(text: str) -> List[float]:
    vec = [0.0] * DIM
    tokens = [t for t in tokenize(text) if len(t) >= 2 and t not in STOPWORDS]
    for tok in tokens:
        for idx, val in token_vector_sparse(tok):
            vec[idx] += val
    return l2_normalize(vec)


def dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_corpus_paragraphs() -> Dict[str, List[str]]:
    corpus_path = os.path.join(OUTPUT_DIR, "corpus.jsonl")
    mapping: Dict[str, List[str]] = {}
    if not os.path.exists(corpus_path):
        return mapping
    for row in read_jsonl(corpus_path):
        doc_id = row.get("doc_id")
        paras = row.get("paragraphs") or []
        if doc_id and paras:
            mapping[doc_id] = paras
    return mapping


def load_vocab() -> Tuple[List[str], List[List[float]]]:
    tokens = []
    vectors = []
    for row in read_jsonl(os.path.join(SEARCH_DIR, "vocab.jsonl")):
        tokens.append(row["token"])
        vectors.append(row["vector"])
    return tokens, vectors


def expand_query(query: str, top_k: int = TOP_K, min_sim: float = MIN_SIM) -> Dict[str, List[Tuple[str, float]]]:
    tokens, vectors = load_vocab()
    expansions: Dict[str, List[Tuple[str, float]]] = {}

    for qtok in [t for t in tokenize(query) if len(t) >= 2 and t not in STOPWORDS]:
        qvec = embed_token(qtok)
        scored = []
        for tok, vec in zip(tokens, vectors):
            if tok == qtok:
                continue
            sim = dot(qvec, vec)
            if sim >= min_sim:
                scored.append((tok, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        expansions[qtok] = scored[:top_k]

    return expansions


def search(query: str, top: int = 10, expand: bool = True) -> List[Tuple[str, float]]:
    qvec = embed_text(query)

    if expand:
        exp = expand_query(query)
        # simple expansion: average in expansion token embeddings
        exp_tokens = [t for lst in exp.values() for t, _ in lst]
        if exp_tokens:
            exp_vec = [0.0] * DIM
            for tok in exp_tokens:
                for idx, val in token_vector_sparse(tok):
                    exp_vec[idx] += val
            exp_vec = l2_normalize(exp_vec)
            qvec = l2_normalize([q + 0.5 * e for q, e in zip(qvec, exp_vec)])

    results = []
    for row in read_jsonl(os.path.join(SEARCH_DIR, "doc_embeddings.jsonl")):
        doc_id = row["doc_id"]
        sim = dot(qvec, row["vector"])
        results.append((doc_id, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top]


def attach_best_paragraph_hash(query: str, results: List[Tuple[str, float]]) -> List[Tuple[str, float, str | None]]:
    paragraphs = load_corpus_paragraphs()
    qvec = embed_text(query)
    final = []
    for doc_id, sim in results:
        paras = paragraphs.get(doc_id, [])
        if not paras:
            final.append((doc_id, sim, None))
            continue
        best_text = None
        best_score = -1.0
        for text in paras:
            pvec = embed_text(text)
            score = dot(qvec, pvec)
            if score > best_score:
                best_score = score
                best_text = text
        final.append((doc_id, sim, best_text))
    return final


def search_bge_m3(
    query: str,
    top: int = 10,
    model_path: str = "BAAI/bge-m3",
    with_paragraphs: bool = False,
) -> List[Tuple[str, float, str | None]]:
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
    except Exception as exc:
        raise SystemExit(
            "Missing dependencies. Install 'torch' and 'transformers' to use BGE-M3."
        ) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    resolved_model_path = resolve_model_path(model_path)
    tokenizer = AutoTokenizer.from_pretrained(resolved_model_path, use_fast=False)
    model = AutoModel.from_pretrained(resolved_model_path).to(device)
    model.eval()

    enc = tokenizer([query], padding=True, truncation=True, return_tensors="pt")
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        out = model(**enc)
        mask = enc["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
        pooled = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
    qvec = pooled[0].cpu().tolist()

    results = []
    for row in read_jsonl(os.path.join(SEARCH_DIR_BGE, "doc_embeddings.jsonl")):
        doc_id = row["doc_id"]
        vec = row.get("vector") or []
        if not vec:
            continue
        sim = dot(qvec, vec)
        results.append((doc_id, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    if not with_paragraphs:
        return [(doc_id, sim, None) for doc_id, sim in results[:top]]

    paragraphs = load_corpus_paragraphs()
    final = []
    for doc_id, sim in results[:top]:
        paras = paragraphs.get(doc_id, [])
        if not paras:
            final.append((doc_id, sim, None))
            continue
        best_text = None
        best_score = -1.0
        batch_size = 16
        for i in range(0, len(paras), batch_size):
            batch = paras[i : i + batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=tokenizer.model_max_length,
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.no_grad():
                out = model(**enc)
                mask = enc["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
                pooled = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            for text, vec in zip(batch, pooled.cpu().tolist()):
                score = dot(qvec, vec)
                if score > best_score:
                    best_score = score
                    best_text = text
        final.append((doc_id, sim, best_text))
    return final


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 search_query.py \"your query\" [--top N]")
        return
    args = sys.argv[1:]
    top = 10
    backend = "hash"
    model_path = "BAAI/bge-m3"
    if "--backend" in args:
        idx = args.index("--backend")
        backend = args[idx + 1] if idx + 1 < len(args) else "hash"
        args = args[:idx] + args[idx + 2 :]
    if "--model-path" in args:
        idx = args.index("--model-path")
        model_path = args[idx + 1] if idx + 1 < len(args) else model_path
        args = args[:idx] + args[idx + 2 :]
    if "--top" in args:
        idx = args.index("--top")
        try:
            top = int(args[idx + 1])
        except Exception:
            pass
        args = args[:idx]
    query = " ".join(args).strip()

    if backend == "bge-m3":
        print("\nTop results (bge-m3):")
        for doc_id, sim, para in search_bge_m3(query, top=top, model_path=model_path, with_paragraphs=True):
            print(f"  {doc_id}\t{sim:.4f}")
            if para:
                print(f"    {para}")
        return

    exp = expand_query(query)
    print("Query expansion:")
    for k, v in exp.items():
        print(f"  {k}: {[t for t,_ in v]}")

    print("\nTop results (hash):")
    for doc_id, sim, para in attach_best_paragraph_hash(query, search(query, top=top)):
        print(f"  {doc_id}\t{sim:.4f}")
        if para:
            print(f"    {para}")


if __name__ == "__main__":
    main()
