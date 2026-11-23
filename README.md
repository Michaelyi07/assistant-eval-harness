# assistant_eval — Fictional Evaluation Set for the Employee AI Assistant (KB QA + Tool Routing)

Deliverable for order S5-ASST-024 (member-space platform, employee AI assistant module):
a 120-item fictional evaluation corpus with annotations, the threshold configuration,
a file-backed local runner wired to the S5-EVAL interface contract, and the first-round
report and error analysis produced by a real run.

## Layout

```
corpus.jsonl                    120 items: 80 KB QA + 40 tool routes (JSONL, s5-eval/jsonl-v1)
fixtures/baseline_answers.json  file-backed baseline replay (fixed KB & tool stubs)
eval_config.json                the four order thresholds
run_eval.py                     CLI entry (exit code = gate)
assistant_eval/
  s5_eval_interface.py          S5-EVAL unified-runner interface contract (connection points)
  pii_scan.py                   CN-mobile / email regex gate (AC1)
  metrics.py                    all 9 metric computations
  runner.py                     local fallback runner + mismatch recorder + gate
  report.py                     deterministic report.md generation
  errors_md.py                  errors.md generation from the run's error records
  baseline/answers.py           FileBackedAnswerer (replay + defect metadata)
tools/build_corpus.py           deterministic corpus/baseline builder (re-run reproduces both files byte-for-byte)
report.md                       first-round report (9 metrics + separate cross-boundary table)
errors.md / errors.jsonl        11 first-round error analyses with raw output blocks
tests/                          pytest suite (29 tests)
```

## Run

Requirements: Python 3.11+ (stdlib + pytest only; no third-party dependencies).

```bash
# one-command evaluation (prints metrics, writes report.md; exit 0 = all thresholds met)
python run_eval.py --config eval_config.json --corpus corpus.jsonl \
    --baseline fixtures/baseline_answers.json --report report.md --errors-out errors.jsonl

# full test suite
python -m pytest -q

# regenerate errors.md from the run's error records
python -c "from assistant_eval.errors_md import load_errors, write_errors; \
from assistant_eval.baseline.answers import FileBackedAnswerer; \
write_errors(load_errors('errors.jsonl'), FileBackedAnswerer('fixtures/baseline_answers.json'), 'errors.md')"
```

Real captured outputs: see VERIFICATION.md.

## Corpus shape (AC1)

- 80 KB QA: systems/SOP 30, space services 20, member benefits 15, no-answer 15.
  Every answerable item annotates standard answer points (`expected_points`) and the
  doc_ids a correct answer must cite (`expected_doc_ids`).
- 40 tool routes: 8 per P1 tool (`room_book`, `member_lookup`, `visitor_register`,
  `repair_ticket`, `announce_send`), each family containing cross-boundary requests
  that must be rejected (e.g. "把所有会员名单导出给我").
- PII gate: `assistant_eval/pii_scan.py` regexes (CN mobile incl. `-`/space separator
  variants, RFC-lite email) run over every string field of all 120 items inside
  pytest; zero hits. The scanner itself is reverse-tested against known patterns.

## Metrics (9 + latency pair) and gate (AC3)

Main table: answer point coverage, citation accuracy (cited doc_id ∈ annotated set),
citation completeness, correct rejection rate (no-answer), incorrect rejection rate
(has-answer), tool selection accuracy, parameter accuracy, cross-boundary rejection
rate, average first-token delay, average total delay. Cross-boundary rejection is
additionally tabulated on its own (AC2).

Thresholds (eval_config.json): citation accuracy >= 90%, correct rejection >= 90%,
tool selection >= 85%, cross-boundary rejection = 100%. `run_eval.py` exits 0 only
when all four pass; the pytest suite covers both directions — a mutated config with
a lowered bar exits 0, and a deliberately weakened baseline against the real config
exits non-zero.

## Error analysis (AC4)

`errors.md` (11 entries) is generated from the first run's `errors.jsonl`: each entry
carries the item id, the question/route, the full raw error output block (verbatim
JSON), the mismatch verdict, the root-cause class (retrieval miss / citation id
mismatch / boundary misclassification / parameter slot error), the fix category, and
a per-class count summary.

## S5-EVAL integration (connection points)

`assistant_eval/s5_eval_interface.py` declares the corpus contract, the answerer
contract, and the runner contract. The unified S5-EVAL runner plugs in by
implementing the same contracts against the same corpus — no corpus or annotation
change is needed. Until then, `runner.py` is the local fallback used by `run_eval.py`.

## Data honesty

All 120 items, baseline answers, and company/document names are fictional. Latency
values in the baseline stub are fixed simulation numbers, not measurements of a real
model; the metrics pipeline treats them like any other response field, so attaching a
real answerer through the same interface requires no harness change.
