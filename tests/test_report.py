"""AC2: report lists all 9 metrics; cross-boundary rejection tabulated per tool;
deterministic regeneration over the real evaluated answerer."""

from __future__ import annotations

import json

from assistant_eval.report import METRIC_LABELS, render_report
from assistant_eval.runner import load_corpus, main, run
from mock_assistant import MockAssistant


def _result():
    config = json.loads(open("eval_config.json", encoding="utf-8").read())
    items = load_corpus("corpus.jsonl")
    return run(config, items, MockAssistant())


def test_report_contains_all_nine_metrics() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    labels = [lab for _, lab in METRIC_LABELS]
    assert len(labels) == 10  # 9 evaluation metrics + latency pair as two rows
    for lab in labels:
        assert lab in md


def test_report_cross_boundary_table_per_tool() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    assert "## 越界请求拒绝率（单独成表，按工具拆分）" in md
    # every P1 tool with boundary cases is listed with counts and rate
    per_tool = res["metrics"]["_counts"]["boundary_per_tool"]
    assert len(per_tool) >= 5
    for tool, e in per_tool.items():
        assert f"| {tool} | {e['total']} | {e['rejected']} |" in md
    assert "**整体**" in md


def test_report_gate_section() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    for name, ok in res["gate"]["checks"].items():
        assert name in md
        assert ("PASS" if ok else "FAIL") in md


def test_report_latency_marked_stub_environment() -> None:
    res = _result()
    md = render_report(res["metrics"], res["gate"])
    assert "桩环境实测" in md


def test_report_regeneration_is_deterministic() -> None:
    # the evaluated answerer is deterministic; two renders are byte-identical
    a = render_report(_result()["metrics"], _result()["gate"])
    b = render_report(_result()["metrics"], _result()["gate"])
    assert a == b


def test_cli_writes_report(tmp_path) -> None:
    out = tmp_path / "report.md"
    rc = main(["--config", "eval_config.json", "--corpus", "corpus.jsonl",
               "--report", str(out)])
    assert rc == 0
    assert out.exists() and "指标主表" in out.read_text(encoding="utf-8")
