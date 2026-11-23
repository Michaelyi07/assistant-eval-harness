"""AC3: exit-code gate tested in both directions, using the real evaluated
answerer (mock over fixed stubs) and a fault-injecting wrapper."""

from __future__ import annotations

import json

from assistant_eval.runner import load_corpus, main, run
from mock_assistant import MockAssistant

CONFIG = "eval_config.json"
CORPUS = "corpus.jsonl"


class WeakenedAnswerer(MockAssistant):
    """Fault-injection wrapper around the real mock: answers 10 no-answer
    items instead of refusing -> correct rejection rate collapses to 5/15."""

    def __init__(self, refuse_override_ids: set[str]):
        super().__init__()
        self.ids = refuse_override_ids

    def stream(self, item: dict):
        if item["id"] in self.ids:
            yield item["question"][:6]
            yield {"answer_points": ["据估计约 100 家"], "cited_doc_ids": ["SOP-ONBOARD"],
                   "refused": False}
            return
        yield from super().stream(item)


def _no_answer_ids() -> set[str]:
    items = load_corpus(CORPUS)
    return {it["id"] for it in items
            if it["kind"] == "kb_qa" and not it["annotations"]["answerable"]}


def test_real_mock_meets_gate_exit_zero(tmp_path) -> None:
    # Full real run of the evaluated answerer over the fixed stubs -> exit 0.
    assert main(["--config", CONFIG, "--corpus", CORPUS,
                 "--report", str(tmp_path / "report.md")]) == 0


def _weakened(ids: set[str]) -> WeakenedAnswerer:
    return WeakenedAnswerer(ids)


def test_loosened_thresholds_exit_zero(tmp_path) -> None:
    # Mutated config with a lowered bar -> even the weakened answerer exits 0.
    cfg = json.loads(open(CONFIG, encoding="utf-8").read())
    for k in cfg["thresholds"]:
        cfg["thresholds"][k] = 0.0
    loose = tmp_path / "loosened_config.json"
    loose.write_text(json.dumps(cfg), encoding="utf-8")
    ids = set(list(_no_answer_ids())[:10])
    result = run(json.loads(loose.read_text(encoding="utf-8")),
                 load_corpus(CORPUS), _weakened(ids))
    assert result["gate"]["passed"] is True


def test_weakened_answerer_real_thresholds_exit_nonzero(tmp_path) -> None:
    # The deliberate-mutation direction: real thresholds + weakened answerer
    # (10 no-answer items answered) -> correct rejection 5/15 -> non-zero exit.
    ids = set(list(_no_answer_ids())[:10])
    config = json.loads(open(CONFIG, encoding="utf-8").read())
    result = run(config, load_corpus(CORPUS), _weakened(ids))
    assert result["gate"]["passed"] is False
    failed = [k for k, ok in result["gate"]["checks"].items() if not ok]
    assert any("correct_rejection" in k for k in failed)
