# Phase 1 — Retriever extensions: label filtering + full-page fetch

## Goal

Give the retriever two capabilities the workflow platform needs:
1. **Label/metadata filtering** on search (so Discovery can restrict to
   `zalopay-workflow` + `status:active` + a domain).
2. **Full-page fetch** — return *all* chunks of one Confluence page by `page_id`, in order,
   so the executor can reconstruct the full workflow text to parse.

Both are backward-compatible additions.

## Background (verified in repo)

- Port: `app/ports/retriever.py` — `RetrieverPort.search(*, department, query, k=8, language="en")`
  returns `list[RetrievedChunk]`; also `is_ready()`.
- `RetrievedChunk` dataclass: `app/ports/types.py`.
- OpenSearch adapter: `app/adapters/opensearch_retriever.py` — `search()` builds a **k-NN only**
  query body (`{"query": {"knn": {"embedding": {...}}}}`), no filter clause today. It filters
  out `lifecycle_state == "sunset"` in Python after the query.
- FAISS adapter: `app/adapters/faiss_retriever.py` — local fallback, must keep parity.
- Index fields available for filtering (keyword type): `labels`, `space`, `lifecycle_state`,
  `department`, `doc_type`, `source` (page_id). See `app/ingestion/opensearch_indexer.py` mapping.
- `labels` is stored as a keyword field holding the label strings (JSON-serialized array; each
  label is independently matchable with a `term`/`terms` filter).

## What to build

### 1. `search(..., filters=None)`

Extend the port and both adapters:

```python
def search(self, *, department, query, k=8, language="en",
           filters: dict[str, list[str]] | None = None) -> list[RetrievedChunk]: ...
```

- `filters` maps a field name (`labels`, `space`, `lifecycle_state`, ...) → list of accepted
  values (OR within a field, AND across fields).
- OpenSearch: wrap the existing k-NN in a `bool` query with a `filter` array of `terms`
  clauses, one per field. Example:
  ```python
  {"query": {"bool": {
      "must": [{"knn": {"embedding": {"vector": qvec, "k": fetch}}}],
      "filter": [{"terms": {field: values}} for field, values in filters.items()]
  }}}
  ```
- Default `filters=None` → behaviour identical to today.
- FAISS: apply the filters in Python over chunk metadata after the vector search (keep
  semantics matching OpenSearch as closely as practical).

### 2. `get_page_chunks(*, department, page_id)`

New port method + both adapters:

```python
def get_page_chunks(self, *, department: str, page_id: str) -> list[RetrievedChunk]: ...
```

- OpenSearch: a `term` query on `source == page_id`, `size` large enough for a whole page
  (e.g. 1000), `_source` excludes `embedding`. Return chunks **ordered** by their natural
  page order (use the chunk ordering signal available — `anchor`/`section` sequence or
  `chunk_id` ordinal; inspect how `chunk_text` orders chunks to pick the right sort key).
- FAISS: iterate the local store, select chunks whose `source == page_id`, return ordered.
- This is exact-match retrieval, **not** semantic — no embedding needed.

## Acceptance criteria

- `search()` with no `filters` returns identical results to before (no regression).
- `search(..., filters={"labels": ["zalopay-workflow", "status:active"]})` only returns chunks
  whose labels include those values.
- `get_page_chunks(department="workflow", page_id=X)` returns every chunk of page X in page
  order and nothing from other pages.
- Both adapters expose the same signatures; the FAISS path behaves equivalently for tests.

## Tests

- `tests/unit/` with a fake/mocked OpenSearch client: assert the request body contains the
  expected `bool.filter.terms` clauses for given filters; assert `get_page_chunks` issues a
  `term` query on `source` and returns ordered chunks.
- A FAISS unit test using a small in-memory index proving filter + full-page selection.

## Verify

`python -m ruff check .` and `make test-unit`.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/`. Implement **Phase 1**: extend the retriever
> with label filtering and full-page fetch. Backward compatibility is mandatory.
>
> 1. Read `app/ports/retriever.py`, `app/ports/types.py`, `app/adapters/opensearch_retriever.py`,
>    `app/adapters/faiss_retriever.py`, and `app/ingestion/opensearch_indexer.py` (for the index
>    field mapping and how chunks are ordered).
> 2. Add an optional `filters: dict[str, list[str]] | None = None` parameter to
>    `RetrieverPort.search` and both adapters. In OpenSearch, wrap the existing k-NN query in a
>    `bool` query with a `filter` array of `terms` clauses (one per field; `None` → unchanged
>    behaviour). In FAISS, apply the filters in Python after the vector search.
> 3. Add a new method `get_page_chunks(*, department, page_id) -> list[RetrievedChunk]` to the
>    port and both adapters. OpenSearch: `term` query on `source == page_id`, large `size`,
>    exclude `embedding`, return chunks in page order. FAISS: select matching chunks, ordered.
> 4. Add unit tests under `tests/unit/` (mock the OpenSearch client; use a tiny in-memory FAISS
>    index) proving: no-filter search is unchanged; filtered search builds the right query and
>    filters correctly; `get_page_chunks` returns one page's chunks in order.
>
> Keep `search()` defaults identical to today so no existing caller changes behaviour. Run
> `python -m ruff check .` and `make test-unit`. Report changes + test output.

---

## Result (2026-06-15) — ✅ DONE (code)

**Implemented:**
- `app/ports/retriever.py` — `search(..., filters: dict[str,list[str]] | None = None)` and new
  `get_page_chunks(*, department, page_id)` on the Protocol, with documented filter semantics
  (labels = AND; other fields = OR; None = unchanged).
- `app/adapters/opensearch_retriever.py` — `_build_filter_clauses()` helper (labels →
  `wildcard` AND clauses against the JSON-string `labels` field; other fields → `terms`);
  `search` wraps k-NN in a `bool`+`filter` only when filters are present (bare k-NN otherwise →
  backward compatible); `get_page_chunks` = `term` on `source` + `sort` by `seq` asc, sunset
  excluded, score=1.0.
- `app/adapters/faiss_retriever.py` — `_row_matches_filters()` Python-side equivalent; `search`
  applies it post-vector-search (fetches all rows when filters present); `get_page_chunks` via
  `MetaStore.fetch_chunks_by_source`.
- `app/store/meta.py` — new `fetch_chunks_by_source(department, source)` ordered by `vec_pos`.
- `app/ingestion/opensearch_indexer.py` — stamps a per-department `seq` ordinal on each doc
  (+ `seq` in the index mapping) so `get_page_chunks` can reconstruct page order. **Requires a
  re-sync** to populate `seq` on existing indices (`get_page_chunks` sort uses
  `unmapped_type:integer`, so it degrades gracefully on un-resynced indices).

**Key design note — labels are a JSON string, not a multi-value keyword.** A plain `terms`
filter can't match individual labels, so label filtering uses `wildcard` (OpenSearch) /
`parse_labels` membership (FAISS). Label filters are **AND** (discovery needs
`zalopay-workflow` AND `status:active`); other fields are OR.

**Tests:** `tests/unit/adapters/test_faiss_retriever.py` (+7: label AND/OR, non-label field,
get_page_chunks page isolation / sunset exclusion / position ordering);
`tests/unit/adapters/test_opensearch_retriever.py` (new, 11: `_build_filter_clauses`, search
query shaping with/without filters, sunset exclusion, get_page_chunks query+sort+sunset+empty+
missing-index).

**Verification:** full unit suite `7 failed, 435 passed, 124 errors` vs Phase-0 baseline
`7 failed, 418 passed, 124 errors` → **+17 passing, zero regressions** (same pre-existing 7
failures + 124 collection errors). `ruff --select F` on Phase 1 code: clean (3 pre-existing
F401s in `opensearch_indexer.py` left untouched — `Path`/`Union`, not mine).
