"""AC2: report lists all 9 metrics; cross-boundary rejection tabulated separately;
deterministic regeneration."""

from __future__ import annotations

from assistant_eval.report import METRIC_LABELS, render_report
from assistant_eval.runner import load_corpus, main, run
from assistant_eval.baseline.answers import FileBackedAnswerer
import json


def _result():
    config = json.loads(open("eval_config.json", encoding="utf-8").read())
    items = load_corpus("corpus.jsonl")
    return run(config, items, FileBackedAnswerer("fixtures/baseline_answers.json"))


def test_report_contains_all_nine_metrics() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    labels = [lab for _, lab in METRIC_LABELS]
    assert len(labels) == 10  # 9 evaluation metrics + latency pair rendered as two rows
    for lab in labels:
        assert lab in md


def test_report_cross_boundary_own_table() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    assert "## 越界请求拒绝率（单独成表，按工具拆分）" in md
    assert "越界请求拒绝率（整体）" in md
    # the main table must also carry the metric row
    assert "| 8 | 越界请求拒绝率 | 100.0% |" in md


def test_report_gate_section() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    assert "全部达标（exit code 0）" in md
    for name, ok in res["gate"]["checks"].items():
        assert (f"[{'PASS' if ok else 'FAIL'}]" in md) or (name in md)


def test_report_regeneration_is_deterministic() -> None:
    # One command regenerates report.md; two consecutive renders are byte-identical.
    a = render_report(_result()["metrics"], _result()["gate"])
    b = render_report(_result()["metrics"], _result()["gate"])
    assert a == b


def test_cli_writes_report(tmp_path) -> None:
    out = tmp_path / "report.md"
    rc = main(["--config", "eval_config.json", "--corpus", "corpus.jsonl",
               "--baseline", "fixtures/baseline_answers.json", "--report", str(out)])
    assert rc == 0
    assert out.exists() and "指标主表" in out.read_text(encoding="utf-8")
