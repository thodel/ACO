#!/usr/bin/env python3
"""Serve the ACO visualization with a BGE-M3 semantic search API.

Run:
  /Users/TH_1/Documents/Repo/ACO/.venv/bin/python /Users/TH_1/Documents/Repo/ACO/data_processing/visualization/search_server.py

Then open:
  http://localhost:8000/visualization/search.html
"""

from __future__ import annotations

import json
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Tuple

BASE_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing"
MODEL_DIR = os.path.join(BASE_DIR, "models", "bge-m3")
EMB_DIR = os.path.join(BASE_DIR, "output", "search_index_bge_m3")
CORPUS_PATH = os.path.join(BASE_DIR, "output", "corpus.jsonl")


def resolve_model_path(model_path: str) -> str:
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


def read_jsonl(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


# Load metadata and embeddings at startup
DOCS = {d["doc_id"]: d for d in read_jsonl(os.path.join(EMB_DIR, "docs.jsonl"))}
DOC_EMB = read_jsonl(os.path.join(EMB_DIR, "doc_embeddings.jsonl"))

# Paragraphs for snippets
CORPUS = {d.get("doc_id"): d for d in read_jsonl(CORPUS_PATH)}

# Lazy model load
TOKENIZER = None
MODEL = None


def load_model():
    global TOKENIZER, MODEL
    if TOKENIZER is not None and MODEL is not None:
        return
    from transformers import AutoTokenizer, AutoModel
    import torch

    resolved = resolve_model_path(MODEL_DIR)
    TOKENIZER = AutoTokenizer.from_pretrained(resolved, use_fast=False)
    MODEL = AutoModel.from_pretrained(resolved)
    MODEL.eval()


def mean_pool(last_hidden_state, attention_mask):
    import torch

    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    masked = last_hidden_state * mask
    summed = masked.sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def embed_texts(texts: List[str]) -> List[List[float]]:
    import torch

    load_model()
    enc = TOKENIZER(
        texts,
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=TOKENIZER.model_max_length,
    )
    with torch.no_grad():
        out = MODEL(**enc)
        pooled = mean_pool(out.last_hidden_state, enc["attention_mask"])
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
    return pooled.cpu().tolist()


def dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def best_paragraph(doc_id: str, qvec: List[float]) -> str | None:
    entry = CORPUS.get(doc_id)
    if not entry:
        return None
    paras = entry.get("paragraphs") or []
    if not paras:
        return None

    best = None
    best_score = -1.0
    batch_size = 16
    for i in range(0, len(paras), batch_size):
        batch = paras[i : i + batch_size]
        vecs = embed_texts(batch)
        for text, vec in zip(batch, vecs):
            score = dot(qvec, vec)
            if score > best_score:
                best_score = score
                best = text
    return best


def search(query: str, top: int) -> List[Dict]:
    qvec = embed_texts([query])[0]
    scored = []
    for row in DOC_EMB:
        doc_id = row.get("doc_id")
        vec = row.get("vector") or []
        if not vec:
            continue
        scored.append((doc_id, dot(qvec, vec)))
    scored.sort(key=lambda x: x[1], reverse=True)
    top_results = scored[:top]

    results = []
    for doc_id, score in top_results:
        meta = DOCS.get(doc_id, {})
        snippet = best_paragraph(doc_id, qvec) or meta.get("snippet") or ""
        results.append(
            {
                "doc_id": doc_id,
                "score": score,
                "title": meta.get("title") or doc_id,
                "snippet": snippet,
            }
        )
    return results


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/search":
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0].strip()
            top = int((qs.get("top") or ["10"])[0])
            if not q:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "missing query"}).encode("utf-8"))
                return
            results = search(q, top)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"results": results}).encode("utf-8"))
            return
        return super().do_GET()


if __name__ == "__main__":
    server = HTTPServer(("", 8000), Handler)
    print("Server running on http://localhost:8000")
    server.serve_forever()
