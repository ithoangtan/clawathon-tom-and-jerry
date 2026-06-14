from __future__ import annotations

"""Lightweight BM25 lexical scoring for hybrid retrieval (no extra deps)."""

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[\w\u00C0-\u1EF9]+", re.UNICODE)
_CAMEL_RE = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens for VI/EN mixed text, with camelCase expansion."""
    base = [t.lower() for t in _TOKEN_RE.findall(text or "") if t.strip()]
    expanded: list[str] = []
    seen: dict[str, None] = {}
    for tok in base:
        if tok not in seen:
            seen[tok] = None
            expanded.append(tok)
        if len(tok) > 5:
            for sub in _CAMEL_RE.split(tok):
                sub = sub.lower()
                if sub and sub not in seen:
                    seen[sub] = None
                    expanded.append(sub)
    return expanded


def bm25_scores(query: str, documents: list[str], *, k1: float = 1.5, b: float = 0.75) -> list[float]:
    """Return BM25 scores for *documents* against *query*.

    Pure-Python MVP implementation — scores the candidate pool returned by dense
    retrieval rather than requiring a separate inverted index.
    """
    if not documents:
        return []

    query_terms = tokenize(query)
    if not query_terms:
        return [0.0] * len(documents)

    doc_tokens = [tokenize(doc) for doc in documents]
    doc_lens = [len(toks) for toks in doc_tokens]
    avg_dl = sum(doc_lens) / len(doc_lens) if doc_lens else 0.0

    df: Counter[str] = Counter()
    for toks in doc_tokens:
        for term in set(toks):
            df[term] += 1

    n_docs = len(documents)
    idf = {term: math.log(1 + (n_docs - df[term] + 0.5) / (df[term] + 0.5)) for term in df}

    scores: list[float] = []
    for toks, dl in zip(doc_tokens, doc_lens):
        tf = Counter(toks)
        score = 0.0
        for term in query_terms:
            if term not in tf:
                continue
            freq = tf[term]
            denom = freq + k1 * (1 - b + b * dl / avg_dl if avg_dl else 1.0)
            score += idf.get(term, 0.0) * (freq * (k1 + 1)) / denom
        scores.append(score)
    return scores
