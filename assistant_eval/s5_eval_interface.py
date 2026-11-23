"""S5-EVAL unified runner interface contract (interface file per the unified technical agreement).

The S5-EVAL unified runner (out of scope for this order) is consumed through
this interface only. The local fallback runner in runner.py implements the
same contract, so swapping the unified runner in later requires no corpus or
annotation change.

Connection points:
1. CORPUS CONTRACT  -- one JSON object per line in corpus.jsonl:

   Knowledge QA item:
     {"id": str, "kind": "kb_qa", "category": "systems_sop|space_services|member_benefits|no_answer",
      "question": str,
      "annotations": {"answerable": bool,
                      "expected_points": [str],      # standard answer points
                      "expected_doc_ids": [str]}}    # doc_ids a correct answer must cite

   Tool route item:
     {"id": str, "kind": "tool_route", "category": str,     # = the P1 tool family
      "tool": str,                                          # same value as category
      "question": str,
      "annotations": {"expect_reject": bool,             # true for cross-boundary requests
                      "expected_tool": str | null,       # null when expect_reject
                      "expected_params": {slot: str},
                      "boundary_note": str | null}}      # why the request is out of bounds

2. ANSWERER CONTRACT -- an answerer is any callable item(dict) -> response(dict):
     kb_qa response:     {"answer_points": [str], "cited_doc_ids": [str], "refused": bool,
                          "first_token_ms": int, "total_ms": int}
     tool_route response: {"selected_tool": str | null, "params": {slot: str},
                           "rejected": bool, "reject_reason": str | null,
                           "first_token_ms": int, "total_ms": int}

3. RUNNER CONTRACT -- runner.run(config, corpus, answerer) -> RunResult with
   .metrics (all 9) and .errors (per-item mismatch records); the CLI gate is
   runner.main() returning exit code 0 (all thresholds met) / 1 (any miss).

The unified runner plugs in by implementing the ANSWERER + RUNNER contracts
against the same corpus; see README "S5-EVAL integration".
"""

CORPUS_KINDS = ("kb_qa", "tool_route")
QA_CATEGORIES = ("systems_sop", "space_services", "member_benefits", "no_answer")
P1_TOOLS = ("room_book", "member_lookup", "visitor_register", "repair_ticket", "announce_send")

CORPUS_REQUIRED_FIELDS = ("id", "kind", "category", "question", "annotations")
QA_ANNOTATION_FIELDS = ("answerable", "expected_points", "expected_doc_ids")
ROUTE_ANNOTATION_FIELDS = ("expect_reject", "expected_tool", "expected_params", "boundary_note")
