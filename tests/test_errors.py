"""AC4: at least 10 error analyses, each with problem, raw error output, cause class."""

from __future__ import annotations

import pytest

from assistant_eval.errors_md import load_errors, render_errors
from assistant_eval.baseline.answers import FileBackedAnswerer
from assistant_eval.runner import load_corpus, run
import json


@pytest.fixture(scope="module")
def errors() -> list[dict]:
    config = json.loads(open("eval_config.json", encoding="utf-8").read())
    items = load_corpus("corpus.jsonl")
    result = run(config, items, FileBackedAnswerer("fixtures/baseline_answers.json"))
    return result["errors"]


def test_at_least_10_errors(errors: list[dict]) -> None:
    assert len(errors) >= 10


def test_each_error_has_problem_output_and_cause(errors: list[dict]) -> None:
    answerer = FileBackedAnswerer("fixtures/baseline_answers.json")
    meta = answerer.defect_meta()
    for e in errors:
        assert e["item_id"] and e["question"]
        assert e["error_output"], "raw error output block must be present"
        assert e["problems"], "mismatch description must be present"
        # cause classification available for every recorded error
        assert e["item_id"] in meta, f"{e['item_id']} missing failure_class metadata"
        assert meta[e["item_id"]]["failure_class"]
        assert meta[e["item_id"]]["fix_category"]


def test_error_report_renders_all_fields(errors: list[dict]) -> None:
    answerer = FileBackedAnswerer("fixtures/baseline_answers.json")
    md = render_errors(errors, answerer)
    assert f"错误条目共 {len(errors)} 条" in md
    for e in errors:
        assert e["item_id"] in md
        assert e["question"] in md
    assert "原因分类：" in md and "修复类别：" in md
    assert "## 根因分类汇总" in md


def test_error_report_counts_match(errors: list[dict]) -> None:
    from collections import Counter
    answerer = FileBackedAnswerer("fixtures/baseline_answers.json")
    meta = answerer.defect_meta()
    md = render_errors(errors, answerer)
    counter = Counter(meta[e["item_id"]]["failure_class"] for e in errors)
    for fc, n in counter.items():
        assert f"| {fc} | {n} |" in md
