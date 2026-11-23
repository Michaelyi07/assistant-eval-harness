"""Local fallback runner: corpus -> evaluated answerer -> metrics -> threshold gate.

Implements the RUNNER contract declared in s5_eval_interface.py. The runner
calls the evaluated answerer (default: mock_assistant.MockAssistant, built on
the fixed stubs; a real assistant can be plugged in via --answerer module path
or --answerer-endpoint URL) and measures per-call latency itself with
time.perf_counter -- first-token time is measured at the answerer's first
streamed token, total time at completion. Values are real measurements taken
in the stub environment (in-memory stubs, no network, no model inference) and
are reported as such.

Exit code: 0 = all thresholds met; 1 = any threshold missed; 2 = corpus/PII
gate violation.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from assistant_eval.metrics import compute_metrics
from assistant_eval.pii_scan import scan_corpus
from assistant_eval.s5_eval_interface import (
    CORPUS_REQUIRED_FIELDS,
    QA_ANNOTATION_FIELDS,
    ROUTE_ANNOTATION_FIELDS,
)


# ------------------------------------------------------------ answerer access

class StreamingAnswerer:
    """Adapter conforming to the AnswererContract: stream(item) yields the
    first-token string first and the full response dict last."""

    def stream(self, item: dict) -> Any:
        raise NotImplementedError


def load_answerer(spec: str | None) -> StreamingAnswerer:
    """--answerer takes a module path (default 'mock_assistant'); the module
    must expose a MockAssistant-compatible object named ANSWERER or a class."""
    module_name = spec or "mock_assistant"
    module = importlib.import_module(module_name)
    if hasattr(module, "ANSWERER"):
        return module.ANSWERER
    if hasattr(module, "MockAssistant"):
        return module.MockAssistant()
    raise ValueError(f"module {module_name!r} exposes neither ANSWERER nor MockAssistant")


class EndpointAnswerer(StreamingAnswerer):
    """HTTP answerer for the future S5-EVAL unified runner / a real assistant:
    POSTs the item to the endpoint (ANSWERER_ENDPOINT env or --answerer-endpoint)
    and expects {'response': {...}} back. Non-streaming endpoint: first-token
    time equals the full round-trip and is reported as such."""

    def __init__(self, endpoint: str):
        import urllib.request

        self.endpoint = endpoint
        self._urlopen = urllib.request.urlopen

    def stream(self, item: dict) -> Any:
        import urllib.request

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(item, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self._urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8"))
        yield ""  # non-streaming endpoint: no separate first token
        yield payload["response"]


# ------------------------------------------------------------------- corpus

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


# -------------------------------------------------------------------- run

def run(config: dict, items: list[dict], answerer: StreamingAnswerer) -> dict[str, Any]:
    """Call the answerer over the corpus with real per-call timing, compute
    metrics, and collect mismatch records for the error analysis."""
    responses: dict[str, dict] = {}
    errors: list[dict] = []
    for it in items:
        t0 = time.perf_counter()
        first_ms = None
        response = None
        for part in answerer.stream(it):
            if first_ms is None:
                first_ms = (time.perf_counter() - t0) * 1000.0
            response = part
        total_ms = (time.perf_counter() - t0) * 1000.0
        response = dict(response)
        response["first_token_ms"] = round(first_ms, 3)
        response["total_ms"] = round(total_ms, 3)
        responses[it["id"]] = response
        err = _mismatch(it, response)
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
                            ["answerable"])
            return None
        problems: list[str] = []
        if resp["refused"]:
            problems.append("answerable item was refused")
        got_points = resp["answer_points"]
        missing_points = [p for p in ann["expected_points"] if p not in "\n".join(got_points)]
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


# -------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Local evaluation runner (S5-EVAL fallback)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--answerer", default=None,
                    help="answerer module path (default: mock_assistant; module exposes ANSWERER or MockAssistant)")
    ap.add_argument("--answerer-endpoint", default=None,
                    help="HTTP endpoint of a real assistant / the S5-EVAL unified runner "
                         "(POST item JSON, expect {'response': {...}}); overrides --answerer. "
                         "Also readable from env ANSWERER_ENDPOINT")
    ap.add_argument("--report", default=None, help="write report.md to this path")
    ap.add_argument("--errors-out", default=None, help="write errors.jsonl to this path")
    args = ap.parse_args(argv)

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

    endpoint = args.answerer_endpoint or os.environ.get("ANSWERER_ENDPOINT")
    if endpoint:
        answerer: StreamingAnswerer = EndpointAnswerer(endpoint)
        print(f"answerer: HTTP endpoint {endpoint} (non-streaming; first-token == round-trip)")
    else:
        answerer = load_answerer(args.answerer)
        print(f"answerer: module {args.answerer or 'mock_assistant'} (default mock over fixed stubs)")

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
