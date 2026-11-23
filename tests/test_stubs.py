"""Fixed-stub contract (rework blocker 1): every annotated doc_id has a document;
the five P1 tools expose fixed-data call stubs; the answerer is configurable."""

from __future__ import annotations

import json

import pytest

from assistant_eval.runner import load_corpus
from assistant_eval.s5_eval_interface import P1_TOOLS
from assistant_eval.stubs import KBStore, TOOL_STUBS, call_tool


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    return load_corpus("corpus.jsonl")


def test_every_annotated_doc_id_has_a_document(corpus: list[dict]) -> None:
    kb = KBStore()
    annotated = {d for it in corpus if it["kind"] == "kb_qa"
                 for d in it["annotations"]["expected_doc_ids"]}
    assert annotated <= set(kb.all_doc_ids()), "annotation references a missing document"


def test_documents_are_fictional_but_substantive() -> None:
    kb = KBStore()
    for doc_id in kb.all_doc_ids():
        doc = kb.documents[doc_id]
        assert doc["title"] and doc["version"] and len(doc["content"]) >= 80


def test_kb_search_deterministic() -> None:
    kb = KBStore()
    a = kb.search("怎么预订会议室？")
    b = kb.search("怎么预订会议室？")
    assert [h["doc_id"] for h in a] == [h["doc_id"] for h in b]


def test_all_five_p1_tools_have_fixed_stubs() -> None:
    assert set(TOOL_STUBS) == set(P1_TOOLS)
    for tool in P1_TOOLS:
        out = call_tool(tool, {})
        assert out["ok"] is True and out["action"] == tool


def test_tool_stub_returns_fixed_data() -> None:
    a = call_tool("room_book", {"room": "翠竹厅", "date": "2026-12-01", "start": "14:00"})
    b = call_tool("room_book", {"room": "翠竹厅", "date": "2026-12-01", "start": "14:00"})
    assert a == b  # reproducible
    assert a["room_id"] == "RM-001"
    assert call_tool("member_lookup", {"member_org": "云帆科技", "field": "等级"})["result"] == "旗舰会员"


def test_answerer_entry_via_module_path(tmp_path) -> None:
    from assistant_eval.runner import main

    rc = main(["--config", "eval_config.json", "--corpus", "corpus.jsonl",
               "--answerer", "mock_assistant"])
    assert rc == 0


def test_answerer_endpoint_from_env(monkeypatch, tmp_path) -> None:
    # the env-configured endpoint takes precedence and is announced; a live call
    # is not attempted in this test (no server), so we only assert the wiring
    import assistant_eval.runner as runner_mod

    monkeypatch.setenv("ANSWERER_ENDPOINT", "http://127.0.0.1:9/v1/answer")
    endpoint = runner_mod.os.environ.get("ANSWERER_ENDPOINT")
    assert endpoint == "http://127.0.0.1:9/v1/answer"
    ans = runner_mod.EndpointAnswerer(endpoint)
    assert ans.endpoint == endpoint
