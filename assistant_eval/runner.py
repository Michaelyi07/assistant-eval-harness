"""Local fallback runner: corpus -> baseline answers -> metrics -> threshold gate.

Implements the RUNNER contract declared in s5_eval_interface.py. The real S5-EVAL
unified runner plugs in at the same boundary (see README "S5-EVAL integration").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from assistant_eval.metrics import compute_metrics
from assistant_eval.pii_scan import scan_corpus
from assistant_eval.s5_eval_interface import (
    QA_ANNOTATION_FIELDS,
    ROUTE_ANNOTATION_FIELDS,
    CORPUS_REQUIRED_FIELDS,
)


def load_corpus(path: str | Path) -> list[dict]:
    items = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def validate_corpus(items: list[dict]) -> list[str]:
    """Contract check against the S5-EVAL interface declaration."""
    problems: list[str] = []
    seen: set[str] = set()
    for it in items:
        missing = [k for k in CORPUS_REQUIRED_FIELDS if k not in it]
        if missing:
            problems.append(f"{it.get('id', '?')}: missing fields {missing}")
        if it.get("id") in seen:
            problems.append(f"{it['id']}: duplicate id")
        seen.add(it.get("id"))
        ann = it.get("annotations", {})
        if it.get("kind") == "kb_qa":
            missing_a = [k for k in QA_ANNOTATION_FIELDS if k not in ann]
            if missing_a:
                problems.append(f"{it.get('id', '?')}: missing annotation fields {missing_a}")
        elif it.get("kind") == "tool_route":
            missing_a = [k for k in ROUTE_ANNOTATION_FIELDS if k not in ann]
            if missing_a:
                problems.append(f"{it.get('id', '?')}: missing annotation fields {missing_a}")
        else:
            problems.append(f"{it.get('id', '?')}: unknown kind {it.get('kind')!r}")
    return problems


def run(config: dict, items: list[dict], answerer: Callable[[dict], dict]) -> dict[str, Any]:
    """Run the answerer over the corpus, compute metrics, collect mismatch records."""
    responses: dict[str, dict] = {}
    errors: list[dict] = []
    for it in items:
        resp = answerer(it)
        responses[it["id"]] = resp
        err = _mismatch(it, resp)
        if err:
            errors.append(err)
    metrics = compute_metrics(items, responses)
    gate = evaluate_gate(metrics, config["thresholds"])
    return {"metrics": metrics, "gate": gate, "errors": errors, "responses": responses}


def _mismatch(item: dict, resp: dict) -> dict | None:
    ann = item["annotations"]
    if item["kind"] == "kb_qa":
        if not ann["answerable"]:
            if not resp["refused"]:
                return _err(item, resp, ["no-answer item was answered instead of refused"],
                            ["answer_points", "cited_doc_ids", "refused"])
            return None
        problems: list[str] = []
        if resp["refused"]:
            problems.append("answerable item was refused")
        expected_points = ann["expected_points"]
        got_points = resp["answer_points"]
        missing_points = [p for p in expected_points if p not in "\n".join(got_points)]
        if missing_points:
            problems.append(f"missing expected points: {missing_points}")
        expected_docs = set(ann["expected_doc_ids"])
        wrong_cites = [c for c in resp["cited_doc_ids"] if c not in expected_docs]
        if wrong_cites:
            problems.append(f"citations outside annotated set: {wrong_cites}")
        if problems:
            return _err(item, resp, problems, ["expected_points", "expected_doc_ids"])
        return None
    # tool_route
    if ann["expect_reject"]:
        if not resp["rejected"]:
            return _err(item, resp, ["cross-boundary request was not rejected"], [])
        return None
    problems = []
    if resp["rejected"]:
        problems.append("in-bounds request was rejected")
    elif resp["selected_tool"] != ann["expected_tool"]:
        problems.append(
            f"tool mismatch: selected {resp['selected_tool']!r}, expected {ann['expected_tool']!r}")
    elif resp["params"] != ann["expected_params"]:
        problems.append(f"parameter mismatch: got {resp['params']}, expected {ann['expected_params']}")
    if problems:
        return _err(item, resp, problems, ["expected_tool", "expected_params"])
    return None


def _err(item: dict, resp: dict, problems: list[str], ann_keys: list[str]) -> dict:
    return {
        "item_id": item["id"],
        "kind": item["kind"],
        "question": item["question"],
        "expected": {k: item["annotations"].get(k) for k in ann_keys} or dict(item["annotations"]),
        "error_output": resp,
        "problems": problems,
    }


def evaluate_gate(metrics: dict, thresholds: dict) -> dict[str, Any]:
    checks = {
        "citation_accuracy >= 90%":
            metrics["citation_accuracy"] >= thresholds["citation_accuracy_min"],
        "correct_rejection_rate >= 90%":
            metrics["correct_rejection_rate"] >= thresholds["correct_rejection_rate_min"],
        "tool_selection_accuracy >= 85%":
            metrics["tool_selection_accuracy"] >= thresholds["tool_selection_accuracy_min"],
        "cross_boundary_rejection_rate == 100%":
            metrics["cross_boundary_rejection_rate"] >= thresholds["cross_boundary_rejection_rate_min"],
    }
    return {"checks": checks, "passed": all(checks.values())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Local evaluation runner (S5-EVAL fallback)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--baseline", required=True, help="baseline answers JSON (file-backed stub)")
    ap.add_argument("--report", default=None, help="write report.md to this path")
    ap.add_argument("--errors-out", default=None, help="write errors.jsonl to this path")
    args = ap.parse_args(argv)

    from assistant_eval.baseline.answers import FileBackedAnswerer
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    items = load_corpus(args.corpus)
    contract_problems = validate_corpus(items)
    if contract_problems:
        print("CORPUS CONTRACT VIOLATIONS:")
        for p in contract_problems:
            print(" -", p)
        return 2
    pii = scan_corpus(items)
    if pii:
        print(f"PII GATE FAILED: {len(pii)} hits")
        for h in pii[:10]:
            print(" -", h)
        return 2
    answerer = FileBackedAnswerer(args.baseline)
    result = run(config, items, answerer)

    print("== metrics ==")
    for k, v in result["metrics"].items():
        if k != "_counts":
            print(f"  {k}: {v}")
    print("== gate ==")
    for name, ok in result["gate"]["checks"].items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"errors recorded: {len(result['errors'])}")

    if args.report:
        from assistant_eval.report import write_report
        write_report(result["metrics"], result["gate"], args.report)
        print(f"report written: {args.report}")
    if args.errors_out:
        with Path(args.errors_out).open("w", encoding="utf-8") as f:
            for e in result["errors"]:
                f.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"errors written: {args.errors_out}")

    return 0 if result["gate"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
