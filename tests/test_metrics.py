"""Metric formula unit checks on a small hand-computed sample."""

from __future__ import annotations

from assistant_eval.metrics import compute_metrics

ITEMS = [
    {"id": "q1", "kind": "kb_qa", "category": "systems_sop", "question": "q1",
     "annotations": {"answerable": True, "expected_points": ["点A"], "expected_doc_ids": ["D1"]}},
    {"id": "q2", "kind": "kb_qa", "category": "no_answer", "question": "q2",
     "annotations": {"answerable": False, "expected_points": [], "expected_doc_ids": []}},
    {"id": "r1", "kind": "tool_route", "category": "room_book", "tool": "room_book", "question": "r1",
     "annotations": {"expect_reject": False, "expected_tool": "room_book",
                     "expected_params": {"room": "翠竹厅"}, "boundary_note": None}},
    {"id": "r2", "kind": "tool_route", "category": "member_lookup", "tool": "member_lookup",
     "question": "r2",
     "annotations": {"expect_reject": True, "expected_tool": None, "expected_params": {},
                     "boundary_note": "cross-boundary"}},
]


def test_metrics_hand_computed() -> None:
    responses = {
        "q1": {"answer_points": ["点A"], "cited_doc_ids": ["D1"], "refused": False,
               "first_token_ms": 100, "total_ms": 500},
        "q2": {"answer_points": [], "cited_doc_ids": [], "refused": True,
               "first_token_ms": 100, "total_ms": 500},
        "r1": {"selected_tool": "room_book", "params": {"room": "翠竹厅"},
               "rejected": False, "reject_reason": None,
               "first_token_ms": 200, "total_ms": 700},
        "r2": {"selected_tool": None, "params": {}, "rejected": True,
               "reject_reason": "cross-boundary", "first_token_ms": 200, "total_ms": 700},
    }
    m = compute_metrics(ITEMS, responses)
    assert m["answer_point_coverage"] == 1.0
    assert m["citation_accuracy"] == 1.0
    assert m["citation_completeness"] == 1.0
    assert m["correct_rejection_rate"] == 1.0
    assert m["incorrect_rejection_rate"] == 0.0
    assert m["tool_selection_accuracy"] == 1.0
    assert m["parameter_accuracy"] == 1.0
    assert m["cross_boundary_rejection_rate"] == 1.0
    assert m["avg_first_token_ms"] == 150.0
    assert m["avg_total_ms"] == 600.0


def test_metrics_detect_wrong_citation_and_tool() -> None:
    responses = {
        "q1": {"answer_points": ["点A"], "cited_doc_ids": ["D9"], "refused": False,
               "first_token_ms": 100, "total_ms": 500},
        "q2": {"answer_points": ["瞎答"], "cited_doc_ids": ["D1"], "refused": False,
               "first_token_ms": 100, "total_ms": 500},
        "r1": {"selected_tool": "repair_ticket", "params": {},
               "rejected": False, "reject_reason": None,
               "first_token_ms": 100, "total_ms": 500},
        "r2": {"selected_tool": None, "params": {}, "rejected": True,
               "reject_reason": "cross-boundary", "first_token_ms": 100, "total_ms": 500},
    }
    m = compute_metrics(ITEMS, responses)
    assert m["citation_accuracy"] == 0.0  # the only citation is outside the set
    assert m["correct_rejection_rate"] == 0.0  # no-answer item answered
    assert m["incorrect_rejection_rate"] == 0.0
    assert m["tool_selection_accuracy"] == 0.0  # wrong tool selected
    assert m["cross_boundary_rejection_rate"] == 1.0


def test_gate_thresholds_boundaries() -> None:
    from assistant_eval.runner import evaluate_gate
    thresholds = {"citation_accuracy_min": 0.90, "correct_rejection_rate_min": 0.90,
                  "tool_selection_accuracy_min": 0.85, "cross_boundary_rejection_rate_min": 1.0}
    at_edge = {"citation_accuracy": 0.90, "correct_rejection_rate": 0.90,
               "tool_selection_accuracy": 0.85, "cross_boundary_rejection_rate": 1.0}
    gate = evaluate_gate(at_edge, thresholds)
    assert gate["passed"] is True
    assert len(gate["checks"]) == 4  # all four order thresholds must be enforced
    below = dict(at_edge, cross_boundary_rejection_rate=0.99)
    assert evaluate_gate(below, thresholds)["passed"] is False
