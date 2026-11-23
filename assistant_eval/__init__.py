"""assistant_eval — fictional evaluation harness for the member-space employee AI assistant.

Components:
- s5_eval_interface.py  S5-EVAL unified-runner interface contract + adapter points
- pii_scan.py           CN-mobile / email regex scanner (the PII gate)
- metrics.py            the 9 metric computations
- runner.py             local fallback runner: corpus -> baseline answers -> metrics -> gate
- report.py             deterministic regeneration of report.md
- errors_md.py          errors.md generation from the runner's errors.jsonl
- baseline/answers.py   file-backed baseline answerer (fixed KB & tool stubs)
"""

PROMPT_CONTRACT = "s5-eval/jsonl-v1"

__all__ = ["PROMPT_CONTRACT"]
