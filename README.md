# assistant_eval — Fictional Evaluation Set for the Employee AI Assistant (KB QA + Tool Routing)

Deliverable for order S5-ASST-024 (member-space platform, employee AI assistant
module): a 120-item fictional evaluation corpus with annotations, fixed stub
data for the KB and the five P1 tools, an evaluated answerer built only on
those stubs, a threshold-gated local runner wired to the S5-EVAL interface
contract, and a first-round report + error analysis produced by a real run of
that answerer.

## Layout

```
corpus.jsonl                    120 items: 80 KB QA + 40 tool routes (JSONL, s5-eval/jsonl-v1)
fixtures/kb_documents.json      fixed KB document stub: one fictional doc per annotated doc_id
eval_config.json                the four order thresholds
run_eval.py                     CLI entry (exit code = gate)
mock_assistant.py               the evaluated answerer: retrieval KB QA + rule-based tool routing,
                                built ONLY on the stubs (never reads annotations)
assistant_eval/
  s5_eval_interface.py          S5-EVAL unified-runner interface contract (connection points)
  stubs.py                      KBStore (deterministic retrieval stub) + five P1 tool call stubs
  pii_scan.py                   CN-mobile / email regex gate (AC1)
  metrics.py                    all 9 metric computations (incl. per-tool boundary stats)
  runner.py                     local runner: calls the answerer, times every call,
                                records mismatches, enforces the gate via exit code
  report.py                     deterministic report.md generation
  errors_md.py                  errors.md generation (cause classes derived from mismatches)
tools/build_corpus.py           deterministic corpus builder (re-runs reproduce corpus.jsonl byte-for-byte)
report.md                       first-round report (9 metrics + per-tool boundary table)
errors.md / errors.jsonl        first-round error analyses from the real run
tests/                          pytest suite (38 tests)
pytest.ini                      pythonpath=. / testpaths=tests
requirements.txt                jsonschema==4.26.0, pytest==9.2.0
```

## Run

Requirements: Python 3.11+ (stdlib + pytest only; no third-party runtime deps).

```bash
python -m pip install -r requirements.txt

# one-command evaluation (default answerer: mock_assistant over the fixed stubs)
python run_eval.py --config eval_config.json --corpus corpus.jsonl \
    --report report.md --errors-out errors.jsonl

# plug in a real assistant via module path (module exposes ANSWERER or MockAssistant)
python run_eval.py --config eval_config.json --corpus corpus.jsonl --answerer my_assistant

# plug in via HTTP endpoint (S5-EVAL unified runner / real assistant service);
# also configurable through the ANSWERER_ENDPOINT environment variable
python run_eval.py --config eval_config.json --corpus corpus.jsonl \
    --answerer-endpoint http://127.0.0.1:8000/v1/answer

# thresholds: eval_config.json is the default; per the unified technical
# agreement (configuration from environment variables) they can be overridden
# with an env JSON object, e.g.
#   EVAL_THRESHOLDS_JSON='{"citation_accuracy_min": 0.95}'
# The harness holds no secrets and sends no data overseas.

# regenerate errors.md from the run's error records
python -c "from assistant_eval.errors_md import load_errors, write_errors; \
write_errors(load_errors('errors.jsonl'), 'errors.md')"

# full test suite
python -m pytest -q
```

Real captured outputs: see `VERIFICATION.md`.

## Fixed stubs (order scope)

- **KB document stub** (`fixtures/kb_documents.json` + `assistant_eval/stubs.py::KBStore`):
  one fictional document per annotated doc_id (13 docs, title/version/content);
  `KBStore.search(query)` is a deterministic keyword-retrieval stub standing in
  for the real S3-KB retrieval service. **S3-KB integration point**: replace
  `KBStore.search` with the real retrieval client; the document store and the
  answerer interface stay unchanged.
- **Tool interface stubs** (`stubs.py::TOOL_STUBS` / `call_tool`): the five P1
  tools (`room_book`, `member_lookup`, `visitor_register`, `repair_ticket`,
  `announce_send`) return fixed canned data per call. **Tool work-order
  integration point**: replace `call_tool` with the real tool-gateway client;
  the mock assistant and the runner need no change.

## The evaluated answerer (`mock_assistant.py`)

`MockAssistant` is the default evaluated answerer. It is built ONLY on the
stubs above and never reads `corpus.jsonl` or any annotation: KB questions are
answered by deterministic retrieval over the KB document stub (refusing when
retrieval finds nothing relevant), tool routes are classified by an intent
keyword table (rejecting cross-boundary requests) with slot extraction, and
selected tools are actually invoked through the tool stubs. It streams a
first token before the full response, so the runner can time both. Its real
weaknesses (citation misses, point misses, slot errors) are what the first
round's error analysis is made of.

## Metrics (9 + latency pair) and gate (AC3)

Main table: answer point coverage, citation accuracy (cited doc_id ∈ annotated
set), citation completeness, correct rejection rate (no-answer), incorrect
rejection rate (has-answer), tool selection accuracy, parameter accuracy,
cross-boundary rejection rate, average first-token delay, average total delay.
Latency is measured by the runner with `time.perf_counter` on every call —
first-token at the answerer's first streamed token, total at completion — and
the report marks the values as **stub-environment measurements** (in-memory
stubs, no network, no model inference). Cross-boundary rejection is
additionally tabulated per tool with counts and rates (AC2).

Thresholds (eval_config.json): citation accuracy >= 90%, correct rejection
>= 90%, tool selection >= 85%, cross-boundary rejection = 100%. `run_eval.py`
exits 0 only when all four pass; the pytest suite covers both directions — a
mutated config with a lowered bar exits 0 even for a weakened answerer, and
the real answerer against the real config exits non-zero when a
fault-injecting wrapper answers no-answer items.

## Error analysis (AC4)

`errors.md` is generated from the real run's mismatch records: each entry
carries the item id, the question/route, the evaluated answerer's actual
output (verbatim JSON, with the measured latency fields), the mismatch
verdict, and a root-cause class **derived from the mismatch content**
(citation_id_mismatch / point_miss / incorrect_refusal / missed_refusal /
tool_selection_error / parameter_error / boundary_miss) plus a fix category
and a per-class count table. No pre-assigned labels exist anywhere.

## S5-EVAL integration (connection points)

`assistant_eval/s5_eval_interface.py` declares the corpus contract, the
streaming answerer contract, and the runner contract. The unified S5-EVAL
runner or a real assistant plugs in through `--answerer <module>` or
`--answerer-endpoint <URL>` (env `ANSWERER_ENDPOINT`); the corpus, annotations,
metrics and gate need no change.

## Data honesty

All 120 items, documents, stub data and the answerer's outputs are synthetic.
Latency values are real `perf_counter` measurements taken in the stub
environment and are labelled as such in the report. The metrics pipeline
treats a real assistant exactly like the mock: same interface, same timing,
same thresholds.
