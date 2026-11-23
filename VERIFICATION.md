# VERIFICATION — S5-ASST-024 assistant_eval deliverable (rework round 1)

All outputs below are real captured runs on the delivery machine (Windows 11,
win32), executed from a clean checkout copy with a dedicated virtualenv built
from the repo's own requirements.txt (pytest 9.2.0; the harness itself is
stdlib-only).

## 1. Environment

```
$ python --version
Python 3.13.14
$ python -m pip install -r requirements.txt
$ python -m pip show pytest | grep -E "^(Name|Version)"
Name: pytest
Version: 9.2.0
```

## 2. Clean-environment collection and full suite (38 tests, one command)

```
$ python -m pytest --collect-only -q
38 tests collected in 0.19s

$ python -m pytest -q
......................................                                   [100%]
38 passed in 2.36s
```

## 3. Full verbose run

```
$ python -m pytest -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
cachedir: .pytest_cache
rootdir: D:\tmp\kb1894r_verify
configfile: pytest.ini
testpaths: tests
collecting ... collected 38 items

tests/test_corpus_shape.py::test_total_120 PASSED                        [  3%]
tests/test_corpus_shape.py::test_qa_distribution PASSED                  [  5%]
tests/test_corpus_shape.py::test_no_answer_items_have_empty_annotations PASSED [  7%]
tests/test_corpus_shape.py::test_route_count_and_per_tool_range PASSED   [ 10%]
tests/test_corpus_shape.py::test_boundary_routes_present_per_tool PASSED [ 13%]
tests/test_corpus_shape.py::test_pii_scan_zero_hits PASSED               [ 15%]
tests/test_corpus_shape.py::test_pii_scanner_detects_known_patterns PASSED [ 18%]
tests/test_corpus_shape.py::test_pii_scanner_ignores_safe_numbers PASSED [ 21%]
tests/test_errors.py::test_at_least_10_errors PASSED                     [ 23%]
tests/test_errors.py::test_each_error_has_problem_output_and_cause PASSED [ 26%]
tests/test_errors.py::test_classification_covers_the_five_classes PASSED [ 28%]
tests/test_errors.py::test_error_output_is_the_answerer_actual_output PASSED [ 31%]
tests/test_errors.py::test_error_report_renders_all_fields PASSED        [ 34%]
tests/test_errors.py::test_error_report_counts_match PASSED              [ 36%]
tests/test_metrics.py::test_metrics_hand_computed PASSED                 [ 39%]
tests/test_metrics.py::test_metrics_detect_wrong_citation_and_tool PASSED [ 42%]
tests/test_metrics.py::test_gate_thresholds_boundaries PASSED            [ 44%]
tests/test_report.py::test_report_contains_all_nine_metrics PASSED       [ 47%]
tests/test_report.py::test_report_cross_boundary_table_per_tool PASSED   [ 50%]
tests/test_report.py::test_report_gate_section PASSED                    [ 52%]
tests/test_report.py::test_report_latency_marked_stub_environment PASSED [ 55%]
tests/test_report.py::test_report_regeneration_is_deterministic PASSED  [ 57%]
tests/test_report.py::test_cli_writes_report PASSED                      [ 60%]
tests/test_s5_eval_contract.py::test_corpus_conforms_to_contract PASSED  [ 63%]
tests/test_s5_eval_contract.py::test_qa_annotations_carry_required_fields PASSED [ 65%]
tests/test_s5_eval_contract.py::test_route_annotations_carry_required_fields PASSED [ 68%]
tests/test_s5_eval_contract.py::test_ids_unique_and_required_fields_present PASSED [ 71%]
tests/test_s5_eval_contract.py::test_tools_are_p1_set PASSED             [ 73%]
tests/test_stubs.py::test_every_annotated_doc_id_has_a_document PASSED   [ 76%]
tests/test_stubs.py::test_documents_are_fictional_but_substantive PASSED [ 78%]
tests/test_stubs.py::test_kb_search_deterministic PASSED                 [ 81%]
tests/test_stubs.py::test_all_five_p1_tools_have_fixed_stubs PASSED      [ 84%]
tests/test_stubs.py::test_tool_stub_returns_fixed_data PASSED            [ 86%]
tests/test_stubs.py::test_answerer_entry_via_module_path PASSED          [ 89%]
tests/test_stubs.py::test_answerer_endpoint_from_env PASSED              [ 92%]
tests/test_threshold_gate.py::test_real_mock_meets_gate_exit_zero PASSED [ 94%]
tests/test_threshold_gate.py::test_loosened_thresholds_exit_zero PASSED  [ 97%]
tests/test_threshold_gate.py::test_weakened_answerer_real_thresholds_exit_nonzero PASSED [100%]

============================= 38 passed in 2.36s ==============================
```

## 4. One-command real evaluation run (exit code 0 = all thresholds met)

The default answerer (`mock_assistant`, built only on the fixed KB document
stub and the five tool stubs) actually answers all 120 items; the runner
measures every call with `time.perf_counter` and computes the metrics from
those real outputs:

```
$ python run_eval.py --config eval_config.json --corpus corpus.jsonl --report report.md --errors-out errors.jsonl
answerer: module mock_assistant (default mock over fixed stubs)
== metrics ==
  answer_point_coverage: 0.873
  citation_accuracy: 0.9365
  citation_completeness: 0.9206
  correct_rejection_rate: 0.9333
  incorrect_rejection_rate: 0.0308
  tool_selection_accuracy: 1.0
  parameter_accuracy: 0.4242
  cross_boundary_rejection_rate: 1.0
  avg_first_token_ms: 0.1
  avg_total_ms: 0.1
== gate ==
  [PASS] citation_accuracy >= 90%
  [PASS] correct_rejection_rate >= 90%
  [PASS] tool_selection_accuracy >= 85%
  [PASS] cross_boundary_rejection_rate == 100%
errors recorded: 30
report written: report.md
errors written: errors.jsonl
exit=0
```

The 30 recorded errors are genuine mismatches of the evaluated answerer
(citation_id_mismatch / point_miss / parameter_error / missed_refusal) — they
are produced by the run, not pre-written.

## 5. Deterministic report regeneration

```
$ python run_eval.py ... --report report_a.md ; python run_eval.py ... --report report_b.md
$ cmp report_a.md report_b.md && echo identical
identical
```

The evaluated answerer is fully deterministic (no randomness), so two runs
produce byte-identical report files.

## 6. Gate tested in both directions (excerpt from the suite)

- `test_real_mock_meets_gate_exit_zero`: real answerer + real config -> exit 0.
- `test_loosened_thresholds_exit_zero`: lowered-bar config + fault-injecting
  wrapper (10 no-answer items answered) -> gate passes -> exit 0.
- `test_weakened_answerer_real_thresholds_exit_nonzero`: same wrapper against
  the real config -> correct rejection 5/15 -> gate fails -> non-zero.

## 7. Acceptance-criteria mapping (the 4 ACs + the rework items)

| Item | Proof |
|---|---|
| AC1 count/distribution per requirements; regex scan zero hits | `test_qa_distribution` (30/20/15/15), `test_route_count_and_per_tool_range` (40, 8 per tool), `test_pii_scan_zero_hits` over all 120 items |
| AC2 report lists all 9 metrics; boundary rejection tabulated separately **per tool** | `test_report_contains_all_nine_metrics`, `test_report_cross_boundary_table_per_tool` (per-tool counts + rates + overall row) |
| AC3 non-zero exit when thresholds not met (test) | both directions: `test_real_mock_meets_gate_exit_zero`, `test_loosened_thresholds_exit_zero`, `test_weakened_answerer_real_thresholds_exit_nonzero` |
| AC4 10+ error analyses with problem, output, cause | `test_at_least_10_errors` (30 real mismatches), cause classes derived via `errors_md.classify` from the mismatch content, output = the answerer's actual timed output (`test_error_output_is_the_answerer_actual_output`) |
| rework 1 (fixed stubs: KB docs + retrieval, 5 tool stubs) | `fixtures/kb_documents.json` (13 docs), `stubs.KBStore.search` deterministic retrieval stub, `stubs.call_tool` fixed data for all five P1 tools; `test_every_annotated_doc_id_has_a_document`, `test_all_five_p1_tools_have_fixed_stubs`, `test_tool_stub_returns_fixed_data` |
| rework 2 (real evaluated answerer, not answer keys) | `mock_assistant.MockAssistant` built only on the stubs (no annotation access); report/errors regenerated from its actual outputs (section 4); metrics CAN miss thresholds — demonstrated by the weakened wrapper tests |
| rework 3 (cause classes derived, real outputs) | `errors_md.CLASS_RULES` + `classify()`; `test_classification_covers_the_five_classes`, `test_each_error_has_problem_output_and_cause` |
| rework 4 (runner-measured latency, stub-env labelled) | `runner.run` times first token + total with `time.perf_counter`; report marks values as 桩环境实测 (`test_report_latency_marked_stub_environment`) |
| rework 5 (configurable answerer entry) | `--answerer <module>` / `--answerer-endpoint <URL>` / env `ANSWERER_ENDPOINT`; `test_answerer_entry_via_module_path`, `test_answerer_endpoint_from_env` |
| rework 6 (per-tool boundary table; honest wording) | per-tool table test (above); README/errors.md wording states outputs come from the evaluated answerer's real run |
