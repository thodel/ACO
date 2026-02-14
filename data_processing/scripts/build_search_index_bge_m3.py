#!/usr/bin/env python3
"""Build BAAI/bge-m3 embeddings for retrieval.

Requires (local install):
  - torch
  - transformers

Example:
  python3 build_search_index_bge_m3.py --model-path /path/to/BAAI/bge-m3

If --model-path is not provided, the script uses 'BAAI/bge-m3' which
requires network access to download from Hugging Face.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Iterable, List

OUTPUT_DIR = "/Users/TH_1/Documents/Repo/ACO/data_processing/output"
CORPUS_PATH = os.path.join(OUTPUT_DIR, "corpus.jsonl")
SEARCH_DIR = os.path.join(OUTPUT_DIR, "search_index_bge_m3")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


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


def chunk_text(text: str, max_chars: int) -> List[str]:
    text = normalize_space(text)
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # try to cut on sentence boundary
        cut = text.rfind(".", start, end)
        if cut == -1 or cut < start + max_chars * 0.5:
            cut = end
        chunks.append(text[start:cut].strip())
        start = cut
    return [c for c in chunks if c]

def resolve_model_path(model_path: str) -> str:
    # If given a HF cache root, resolve to the latest snapshot path
    if os.path.isdir(model_path) and not os.path.isfile(os.path.join(model_path, "config.json")):
        candidate = os.path.join(model_path, "models--BAAI--bge-m3", "snapshots")
        if os.path.isdir(candidate):
            snapshots = [os.path.join(candidate, d) for d in os.listdir(candidate)]
            snapshots = [d for d in snapshots if os.path.isdir(d)]
            if snapshots:
                # prefer snapshots that include tokenizer files
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


def mean_pool(last_hidden_state, attention_mask):
    import torch

    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    masked = last_hidden_state * mask
    summed = masked.sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def build_index(model_path: str, max_chars: int, batch_size: int) -> None:
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
    except Exception as exc:
        raise SystemExit(
            "Missing dependencies. Install 'torch' and 'transformers' to use BGE-M3."
        ) from exc

    os.makedirs(SEARCH_DIR, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    resolved_model_path = resolve_model_path(model_path)
    tokenizer = AutoTokenizer.from_pretrained(resolved_model_path, use_fast=False)
    model = AutoModel.from_pretrained(resolved_model_path).to(device)
    model.eval()

    docs_meta: List[Dict] = []
    embeddings_rows: List[Dict] = []

    for row in read_jsonl(CORPUS_PATH):
        doc_id = row.get("doc_id")
        title = row.get("title")
        lang = row.get("lang")
        metadata = row.get("metadata", {})
        text = normalize_space(" ".join([row.get("text_main", ""), row.get("text_notes", "")]))

        docs_meta.append(
            {
                "doc_id": doc_id,
                "title": title,
                "lang": lang,
                "metadata": metadata,
                "text_len": len(text),
                "snippet": text[:400],
            }
        )

        chunks = chunk_text(text, max_chars=max_chars)
        if not chunks:
            embeddings_rows.append({"doc_id": doc_id, "vector": []})
            continue

        all_embs = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
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
                pooled = mean_pool(out.last_hidden_state, enc["attention_mask"])
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            all_embs.append(pooled.cpu())

        emb = torch.cat(all_embs, dim=0).mean(dim=0)
        emb = torch.nn.functional.normalize(emb, p=2, dim=0)
        embeddings_rows.append({"doc_id": doc_id, "vector": emb.tolist()})

    write_jsonl(os.path.join(SEARCH_DIR, "docs.jsonl"), docs_meta)
    write_jsonl(os.path.join(SEARCH_DIR, "doc_embeddings.jsonl"), embeddings_rows)

    write_json(
        os.path.join(SEARCH_DIR, "index_meta.json"),
        {
            "generated_on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "corpus": os.path.abspath(CORPUS_PATH),
            "embedding": {
                "model": resolved_model_path,
                "method": "BAAI/bge-m3",
                "max_chars": max_chars,
                "batch_size": batch_size,
            },
            "counts": {"docs": len(docs_meta)},
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default="BAAI/bge-m3")
    parser.add_argument("--max-chars", type=int, default=4000)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    build_index(args.model_path, args.max_chars, args.batch_size)
    print("BGE-M3 search index built")


if __name__ == "__main__":
    main()
