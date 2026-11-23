# VERIFICATION — S5-ASST-024 assistant_eval deliverable

All outputs below are real captured runs on the delivery machine (Windows 11,
win32), executed from a clean checkout copy with a dedicated virtualenv.
No third-party runtime dependencies (stdlib only); pytest is a test-only dependency.

## 1. Environment

```
$ python --version
Python 3.13.14
$ python -m pip show pytest | grep -E "^(Name|Version)"
Name: pytest
Version: 9.2.0
```

Runtime: Python 3.13.14 (dedicated venv) on Windows (win32); stdlib only for the
harness itself; pytest 9.2.0 (plus pluggy 1.7.0) for the test suite.

## 2. Full test suite (29 tests, one command)

```
$ python -m pytest -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
cachedir: .pytest_cache
rootdir: D:\tmp\kb1894_verify
configfile: pytest.ini
testpaths: tests
collecting ... collected 29 items

tests/test_corpus_shape.py::test_total_120 PASSED                        [  3%]
tests/test_corpus_shape.py::test_qa_distribution PASSED                  [  6%]
tests/test_corpus_shape.py::test_no_answer_items_have_empty_annotations PASSED [ 10%]
tests/test_corpus_shape.py::test_route_count_and_per_tool_range PASSED   [ 13%]
tests/test_corpus_shape.py::test_boundary_routes_present_per_tool PASSED [ 17%]
tests/test_corpus_shape.py::test_pii_scan_zero_hits PASSED               [ 20%]
tests/test_corpus_shape.py::test_pii_scanner_detects_known_patterns PASSED [ 24%]
tests/test_corpus_shape.py::test_pii_scanner_ignores_safe_numbers PASSED [ 27%]
tests/test_errors.py::test_at_least_10_errors PASSED                     [ 31%]
tests/test_errors.py::test_each_error_has_problem_output_and_cause PASSED [ 34%]
tests/test_errors.py::test_error_report_renders_all_fields PASSED        [ 37%]
tests/test_errors.py::test_error_report_counts_match PASSED              [ 41%]
tests/test_metrics.py::test_metrics_hand_computed PASSED                 [ 44%]
tests/test_metrics.py::test_metrics_detect_wrong_citation_and_tool PASSED [ 48%]
tests/test_metrics.py::test_gate_thresholds_boundaries PASSED            [ 51%]
tests/test_report.py::test_report_contains_all_nine_metrics PASSED       [ 55%]
tests/test_report.py::test_report_cross_boundary_own_table PASSED        [ 58%]
tests/test_report.py::test_report_gate_section PASSED                    [ 62%]
tests/test_report.py::test_report_regeneration_is_deterministic PASSED   [ 65%]
tests/test_report.py::test_cli_writes_report PASSED                      [ 68%]
tests/test_s5_eval_contract.py::test_corpus_conforms_to_contract PASSED  [ 72%]
tests/test_s5_eval_contract.py::test_qa_annotations_carry_required_fields PASSED [ 75%]
tests/test_s5_eval_contract.py::test_route_annotations_carry_required_fields PASSED [ 79%]
tests/test_s5_eval_contract.py::test_ids_unique_and_required_fields_present PASSED [ 82%]
tests/test_s5_eval_contract.py::test_tools_are_p1_set PASSED             [ 86%]
tests/test_threshold_gate.py::test_real_baseline_meets_gate_exit_zero PASSED [ 89%]
tests/test_threshold_gate.py::test_loosened_thresholds_exit_zero PASSED  [ 93%]
tests/test_threshold_gate.py::test_weakened_baseline_real_thresholds_exit_nonzero PASSED [ 96%]
tests/test_threshold_gate.py::test_run_result_records_gate_failures PASSED [100%]

============================= 29 passed in 2.10s ==============================
```

## 3. One-command evaluation run (exit code 0 = all thresholds met)

```
$ python run_eval.py --config eval_config.json --corpus corpus.jsonl --baseline fixtures/baseline_answers.json --report report.md --errors-out errors.jsonl
== metrics ==
  answer_point_coverage: 0.9688
  citation_accuracy: 0.9697
  citation_completeness: 0.9844
  correct_rejection_rate: 0.9333
  incorrect_rejection_rate: 0.0154
  tool_selection_accuracy: 0.9091
  parameter_accuracy: 0.9333
  cross_boundary_rejection_rate: 1.0
  avg_first_token_ms: 179.5
  avg_total_ms: 820
== gate ==
  [PASS] citation_accuracy >= 90%
  [PASS] correct_rejection_rate >= 90%
  [PASS] tool_selection_accuracy >= 85%
  [PASS] cross_boundary_rejection_rate == 100%
errors recorded: 11
report written: report.md
errors written: errors.jsonl
exit=0
```

## 4. Deterministic report regeneration

```
$ python run_eval.py ... --report report_a.md
$ python run_eval.py ... --report report_b.md
$ cmp report_a.md report_b.md && echo identical
identical
```

Two consecutive runs of the same command produce byte-identical report files
(fixed file-backed data; no randomness in the harness).

## 5. Reverse check: removing a gate check turns the tests red

The cross-boundary check was temporarily deleted from `evaluate_gate()` in
`assistant_eval/runner.py`, then the metric tests were re-run, then the file
was restored:

```
$ python -m pytest tests/test_metrics.py -q        (with the check deleted)
1 failed, 2 passed in 0.33s

$ (restore runner.py)
$ python -m pytest tests/test_metrics.py -q
3 passed in 0.09s
```

This proves the gate enforces all four order thresholds and that the test
suite detects its removal (the `len(checks) == 4` assertion fails).

## 6. Acceptance-criteria mapping

| AC (order text) | Proof |
|---|---|
| 1. Item count/distribution per requirements; regex scan shows no mobile/email strings | `test_qa_distribution` (30/20/15/15), `test_route_count_and_per_tool_range` (40, 8 per tool), `test_pii_scan_zero_hits` over all 120 items; scanner reverse-tested in `test_pii_scanner_detects_known_patterns` |
| 2. Report lists all 9 metrics; cross-boundary rejection tabulated separately | `test_report_contains_all_nine_metrics`, `test_report_cross_boundary_own_table` (own section with overall + per-tool distribution), real run in section 3 |
| 3. Command returns non-zero exit code when thresholds not met | `test_loosened_thresholds_exit_zero`, `test_weakened_baseline_real_thresholds_exit_nonzero`, `test_run_result_records_gate_failures` (both directions); real passing run exit 0 in section 3 |
| 4. At least 10 error analyses with problem, error output, cause | `test_at_least_10_errors` (11), `test_each_error_has_problem_output_and_cause` (raw output block + failure_class + fix_category per entry), rendered `errors.md` |
