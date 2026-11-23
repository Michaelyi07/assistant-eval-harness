"""AC1: corpus size/distribution + PII regex scan zero hits."""

from __future__ import annotations

import pytest

from assistant_eval.pii_scan import scan_corpus, scan_item
from assistant_eval.runner import load_corpus
from assistant_eval.s5_eval_interface import P1_TOOLS


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    return load_corpus("corpus.jsonl")


def test_total_120(corpus: list[dict]) -> None:
    assert len(corpus) == 120


def test_qa_distribution(corpus: list[dict]) -> None:
    qa = [it for it in corpus if it["kind"] == "kb_qa"]
    assert len(qa) == 80
    by_cat = {c: sum(1 for it in qa if it["category"] == c)
              for c in ("systems_sop", "space_services", "member_benefits", "no_answer")}
    assert by_cat == {
        "systems_sop": 30, "space_services": 20,
        "member_benefits": 15, "no_answer": 15,
    }


def test_no_answer_items_have_empty_annotations(corpus: list[dict]) -> None:
    for it in corpus:
        if it["kind"] == "kb_qa" and it["category"] == "no_answer":
            assert it["annotations"]["answerable"] is False
            assert it["annotations"]["expected_points"] == []
            assert it["annotations"]["expected_doc_ids"] == []


def test_route_count_and_per_tool_range(corpus: list[dict]) -> None:
    routes = [it for it in corpus if it["kind"] == "tool_route"]
    assert len(routes) == 40
    per_tool = {t: sum(1 for it in routes if it["tool"] == t) for t in P1_TOOLS}
    assert set(per_tool) == set(P1_TOOLS)
    for tool, n in per_tool.items():
        assert 5 <= n <= 8, f"{tool}: {n} outside 5-8"


def test_boundary_routes_present_per_tool(corpus: list[dict]) -> None:
    routes = [it for it in corpus if it["kind"] == "tool_route"]
    boundary = [it for it in routes if it["annotations"]["expect_reject"]]
    assert len(boundary) >= 1
    for t in P1_TOOLS:
        assert any(it["tool"] == t for it in boundary), f"{t} has no boundary case"


def test_pii_scan_zero_hits(corpus: list[dict]) -> None:
    # AC1: regex scan over all 120 items -> zero mobile/email hits.
    assert scan_corpus(corpus) == []


def test_pii_scanner_detects_known_patterns() -> None:
    # Reverse check: the scanner must catch the patterns it guards against.
    hits = scan_item({"question": "联系 13812345678", "x": {"note": "mail a.b-c@ex.co"}})
    kinds = {h["pattern"] for h in hits}
    assert kinds == {"cn_mobile", "email"}
    hits2 = scan_item({"q": "电话 138-1234-5678 或 138 1234 5678"})
    assert len(hits2) == 2 and all(h["pattern"] == "cn_mobile" for h in hits2)


def test_pii_scanner_ignores_safe_numbers() -> None:
    assert scan_item({"q": "年费 6800 元，每日首次 4 小时内免费，A4 0.2 元/页"}) == []
