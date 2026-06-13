# Golden eval set (YAML)

Canonical file: **`golden_set.yaml`** (45 cases, MVP departments).

Each case includes:
- `expected_behavior`: `answer` | `refuse`
- `expected_citation_url`: substring expected in citation URLs (or `none` for refusals)

Run offline stub eval:
```bash
python3 tests/eval/run_golden.py --stub
```

Legacy JSON mirror: `evals/golden_cases.json`

Pytest: `tests/eval/test_golden_eval.py`, `tests/eval/test_golden_set.py`
