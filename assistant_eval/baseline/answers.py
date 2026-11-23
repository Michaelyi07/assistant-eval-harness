"""File-backed baseline answerer (fixed KB & tool stubs).

Replays pre-recorded responses from a JSON file so every metric is
reproducible. The stub simulates the (out-of-scope) production answerer:
- kb_qa responses carry fixed simulated latencies (first_token_ms / total_ms);
  these are stub values, not measurements of a real model (README, honest boundary).
- Deliberate defect entries reproduce the first-round failure modes for the
  error analysis; each defect carries failure_class / fix_category used by
  errors_md.py.
"""

from __future__ import annotations

import json
from pathlib import Path


class FileBackedAnswerer:
    def __init__(self, answers_path: str | Path):
        data = json.loads(Path(answers_path).read_text(encoding="utf-8"))
        self.answers = {a["item_id"]: a for a in data["answers"]}

    def __call__(self, item: dict) -> dict:
        rec = self.answers.get(item["id"])
        if rec is None:
            raise KeyError(f"no baseline answer recorded for item {item['id']}")
        return rec["response"]

    def defect_meta(self) -> dict[str, dict]:
        """item_id -> {failure_class, fix_category} for deliberate defect entries."""
        return {
            item_id: {
                "failure_class": rec.get("failure_class", ""),
                "fix_category": rec.get("fix_category", ""),
                "note": rec.get("note", ""),
            }
            for item_id, rec in self.answers.items()
            if rec.get("failure_class")
        }
