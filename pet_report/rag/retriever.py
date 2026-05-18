from __future__ import annotations

import math
import re
from pathlib import Path

import yaml

from pet_report.models.schemas import Evidence, LabItem

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [t.upper() for t in TOKEN_RE.findall(text)]


class LocalKnowledgeRetriever:
    def __init__(self, path: Path):
        self.path = path
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.docs = payload.get("documents", [])
        self.doc_tokens = [tokenize(" ".join([d.get("title", ""), d.get("content", ""), " ".join(d.get("tags", []))])) for d in self.docs]
        self.df: dict[str, int] = {}
        for toks in self.doc_tokens:
            for tok in set(toks):
                self.df[tok] = self.df.get(tok, 0) + 1
        self.avgdl = sum(len(t) for t in self.doc_tokens) / max(1, len(self.doc_tokens))

    def retrieve(self, query: str, lab_items: list[LabItem], top_k: int = 5) -> list[Evidence]:
        metric_query = " ".join([i.canonical_code for i in lab_items] + [i.display_name for i in lab_items])
        q = f"{query} {metric_query}".strip()
        q_tokens = tokenize(q)
        scored: list[tuple[float, dict]] = []
        for doc, toks in zip(self.docs, self.doc_tokens):
            bm25 = self._bm25(q_tokens, toks)
            tag_score = 0.0
            tags = {t.upper() for t in doc.get("tags", [])}
            for item in lab_items:
                if item.canonical_code.upper() in tags:
                    tag_score += 2.0
            score = bm25 + tag_score
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored[:top_k]:
            results.append(
                Evidence(
                    id=str(doc.get("id")),
                    title=str(doc.get("title")),
                    content=str(doc.get("content")),
                    source=str(doc.get("source", self.path.name)),
                    score=round(float(score), 4),
                    tags=list(doc.get("tags", [])),
                )
            )
        return results

    def _bm25(self, q_tokens: list[str], d_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> float:
        if not q_tokens or not d_tokens:
            return 0.0
        n_docs = max(1, len(self.docs))
        tf: dict[str, int] = {}
        for tok in d_tokens:
            tf[tok] = tf.get(tok, 0) + 1
        score = 0.0
        dl = len(d_tokens)
        for tok in q_tokens:
            if tok not in tf:
                continue
            df = self.df.get(tok, 0)
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            freq = tf[tok]
            denom = freq + k1 * (1 - b + b * dl / max(1.0, self.avgdl))
            score += idf * (freq * (k1 + 1)) / denom
        return score
