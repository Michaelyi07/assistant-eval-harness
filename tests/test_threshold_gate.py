"""AC3: exit-code gate tested in both directions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assistant_eval.runner import load_corpus, main, run
from assistant_eval.baseline.answers import FileBackedAnswerer

CONFIG = "eval_config.json"
CORPUS = "corpus.jsonl"
BASELINE = "fixtures/baseline_answers.json"


def _weakened_baseline(tmp_path: Path) -> str:
    # Mutate 10 no-answer items into answered responses -> correct rejection
    # rate collapses to 5/15, breaking the 90% gate.
    data = json.loads(Path(BASELINE).read_text(encoding="utf-8"))
    changed = 0
    corpus = load_corpus(CORPUS)
    no_answer_ids = [it["id"] for it in corpus
                     if it["kind"] == "kb_qa" and not it["annotations"]["answerable"]]
    for rec in data["answers"]:
        if rec["item_id"] in no_answer_ids and changed < 10:
            rec["response"] = {**rec["response"], "refused": False,
                               "answer_points": ["据估计约 100 家"],
                               "cited_doc_ids": ["SOP-ONBOARD"]}
            changed += 1
    assert changed == 10
    out = tmp_path / "weakened_baseline.json"
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(out)


def _loosened_config(tmp_path: Path) -> str:
    cfg = json.loads(Path(CONFIG).read_text(encoding="utf-8"))
    for k in cfg["thresholds"]:
        cfg["thresholds"][k] = 0.0
    out = tmp_path / "loosened_config.json"
    out.write_text(json.dumps(cfg), encoding="utf-8")
    return str(out)


def test_real_baseline_meets_gate_exit_zero(tmp_path: Path) -> None:
    # Full real run: all four thresholds met -> exit 0.
    assert main(["--config", CONFIG, "--corpus", CORPUS, "--baseline", BASELINE,
                 "--report", str(tmp_path / "report.md")]) == 0


def test_loosened_thresholds_exit_zero(tmp_path: Path) -> None:
    # Mutated config with lowered bar -> even a weakened answerer exits 0.
    weak = _weakened_baseline(tmp_path)
    loose = _loosened_config(tmp_path)
    assert main(["--config", loose, "--corpus", CORPUS, "--baseline", weak]) == 0


def test_weakened_baseline_real_thresholds_exit_nonzero(tmp_path: Path) -> None:
    # The deliberate-mutation direction: real thresholds + weakened baseline -> non-zero.
    weak = _weakened_baseline(tmp_path)
    rc = main(["--config", CONFIG, "--corpus", CORPUS, "--baseline", weak])
    assert rc != 0


def test_run_result_records_gate_failures(tmp_path: Path) -> None:
    weak = _weakened_baseline(tmp_path)
    config = json.loads(Path(CONFIG).read_text(encoding="utf-8"))
    result = run(config, load_corpus(CORPUS), FileBackedAnswerer(weak))
    assert result["gate"]["passed"] is False
    failed = [k for k, ok in result["gate"]["checks"].items() if not ok]
    assert failed, "at least one gate check must fail on the weakened baseline"
