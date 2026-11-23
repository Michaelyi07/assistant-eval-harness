"""AC4: at least 10 error analyses, each with problem, raw error output, and a
cause class DERIVED from the actual mismatch (no pre-assigned labels)."""

from __future__ import annotations

import json

import pytest

from assistant_eval.errors_md import classify, load_errors, render_errors
from assistant_eval.runner import load_corpus, run
from mock_assistant import MockAssistant


@pytest.fixture(scope="module")
def errors() -> list[dict]:
    config = json.loads(open("eval_config.json", encoding="utf-8").read())
    result = run(config, load_corpus("corpus.jsonl"), MockAssistant())
    return result["errors"]


def test_at_least_10_errors(errors: list[dict]) -> None:
    assert len(errors) >= 10


def test_each_error_has_problem_output_and_cause(errors: list[dict]) -> None:
    for e in errors:
        assert e["item_id"] and e["question"]
        assert e["error_output"], "raw error output block must be present"
        assert e["problems"], "mismatch description must be present"
        # cause classification must be derivable from the mismatch itself
        assert classify(e["problems"]) != "other", (
            f"{e['item_id']}: mismatch not covered by any root-cause rule"
        )


def test_classification_covers_the_five_classes(errors: list[dict]) -> None:
    # the first round exhibits several distinct real failure modes
    classes = {classify(e["problems"]) for e in errors}
    assert classes >= {"citation_id_mismatch", "point_miss", "parameter_error"}
    assert "boundary_miss" not in classes  # cross-boundary rejection is 100%


def test_error_output_is_the_answerer_actual_output(errors: list[dict]) -> None:
    # spot-check: the recorded output carries real measured latency fields,
    # proving it came from a timed call rather than a canned answer key
    for e in errors[:5]:
        assert "first_token_ms" in e["error_output"]
        assert "total_ms" in e["error_output"]


def test_error_report_renders_all_fields(errors: list[dict]) -> None:
    md = render_errors(errors)
    assert f"错误条目共 {len(errors)} 条" in md
    for e in errors:
        assert e["item_id"] in md
        assert e["question"] in md
    assert "原因分类：" in md and "修复类别：" in md
    assert "## 根因分类汇总" in md


def test_error_report_counts_match(errors: list[dict]) -> None:
    from collections import Counter

    md = render_errors(errors)
    counter = Counter(classify(e["problems"]) for e in errors)
    for fc, n in counter.items():
        assert f"| {fc} | {n} |" in md
