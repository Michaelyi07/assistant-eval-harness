"""The 9 metric computations for the assistant evaluation.

All metrics are computed deterministically from the corpus annotations and the
baseline responses. Definitions:

 1. answer_point_coverage   -- over answerable, non-refused QA items: share of items
                               whose responses cover ALL expected points
 2. citation_accuracy       -- over all cited doc_ids of answerable, non-refused QA
                               items: share of citations that are in the item's
                               annotated expected_doc_ids
 3. citation_completeness   -- over answerable, non-refused QA items: share of items
                               whose citations include every expected doc_id
 4. correct_rejection_rate  -- over no-answer (answerable=false) QA items: share refused
 5. incorrect_rejection_rate-- over answerable QA items: share refused
 6. tool_selection_accuracy -- over non-reject tool routes: share selecting the
                               annotated expected tool
 7. parameter_accuracy      -- over non-reject routes that selected the expected tool:
                               share with params exactly matching expected_params
 8. cross_boundary_rejection_rate -- over expect_reject routes: share rejected
 9. latency                 -- average first_token_ms and total_ms over all 120 items
"""

from __future__ import annotations

from statistics import mean
from typing import Any


def _num_hits(points: list[str], texts: list[str]) -> bool:
    """A point counts as covered when it appears verbatim in one of the response points."""
    joined = "\n".join(texts)
    return all(p in joined for p in points)


def compute_metrics(items: list[dict], responses: dict[str, dict]) -> dict[str, Any]:
    qa = [it for it in items if it["kind"] == "kb_qa"]
    routes = [it for it in items if it["kind"] == "tool_route"]

    answerable = [it for it in qa if it["annotations"]["answerable"]]
    no_answer = [it for it in qa if not it["annotations"]["answerable"]]

    answered = [it for it in answerable if not responses[it["id"]]["refused"]]
    refused_answerable = [it for it in answerable if responses[it["id"]]["refused"]]
    refused_no_answer = [it for it in no_answer if responses[it["id"]]["refused"]]

    # 1. answer point coverage (over answered items)
    covered = [
        it for it in answered
        if _num_hits(it["annotations"]["expected_points"],
                     responses[it["id"]]["answer_points"])
    ]
    point_coverage = len(covered) / len(answered) if answered else 0.0

    # 2/3. citation accuracy & completeness (over answered items)
    total_cites = correct_cites = complete = 0
    for it in answered:
        expected = set(it["annotations"]["expected_doc_ids"])
        cited = responses[it["id"]]["cited_doc_ids"]
        total_cites += len(cited)
        correct_cites += sum(1 for c in cited if c in expected)
        complete += 1 if expected and expected.issubset(set(cited)) else 0
    citation_accuracy = correct_cites / total_cites if total_cites else 0.0
    citation_completeness = complete / len(answered) if answered else 0.0

    # 4/5. rejection rates
    correct_rejection = len(refused_no_answer) / len(no_answer) if no_answer else 0.0
    incorrect_rejection = len(refused_answerable) / len(answerable) if answerable else 0.0

    # 6/7. tool selection & parameter accuracy (over non-reject routes)
    normal = [it for it in routes if not it["annotations"]["expect_reject"]]
    sel_ok = [it for it in normal
              if not responses[it["id"]]["rejected"]
              and responses[it["id"]]["selected_tool"] == it["annotations"]["expected_tool"]]
    tool_selection = len(sel_ok) / len(normal) if normal else 0.0
    param_ok = [it for it in sel_ok
                if responses[it["id"]]["params"] == it["annotations"]["expected_params"]]
    param_accuracy = len(param_ok) / len(sel_ok) if sel_ok else 0.0

    # 8. cross-boundary rejection, overall + per tool (rework item 6)
    boundary = [it for it in routes if it["annotations"]["expect_reject"]]
    boundary_rej = sum(1 for it in boundary if responses[it["id"]]["rejected"])
    boundary_rate = boundary_rej / len(boundary) if boundary else 0.0
    boundary_per_tool: dict[str, dict] = {}
    for it in boundary:
        entry = boundary_per_tool.setdefault(
            it["tool"], {"total": 0, "rejected": 0})
        entry["total"] += 1
        entry["rejected"] += 1 if responses[it["id"]]["rejected"] else 0
    for entry in boundary_per_tool.values():
        entry["rejection_rate"] = round(entry["rejected"] / entry["total"], 4)

    # 9. latency averages
    firsts = [responses[it["id"]]["first_token_ms"] for it in items if it["id"] in responses]
    totals = [responses[it["id"]]["total_ms"] for it in items if it["id"] in responses]

    return {
        "answer_point_coverage": round(point_coverage, 4),
        "citation_accuracy": round(citation_accuracy, 4),
        "citation_completeness": round(citation_completeness, 4),
        "correct_rejection_rate": round(correct_rejection, 4),
        "incorrect_rejection_rate": round(incorrect_rejection, 4),
        "tool_selection_accuracy": round(tool_selection, 4),
        "parameter_accuracy": round(param_accuracy, 4),
        "cross_boundary_rejection_rate": round(boundary_rate, 4),
        "avg_first_token_ms": round(mean(firsts), 1) if firsts else 0.0,
        "avg_total_ms": round(mean(totals), 1) if totals else 0.0,
        "_counts": {
            "qa_total": len(qa), "answerable": len(answerable),
            "no_answer": len(no_answer), "answered": len(answered),
            "routes_total": len(routes), "normal_routes": len(normal),
            "boundary_routes": len(boundary), "total_citations": total_cites,
            "correct_citations": correct_cites,
            "boundary_per_tool": boundary_per_tool,
        },
    }
