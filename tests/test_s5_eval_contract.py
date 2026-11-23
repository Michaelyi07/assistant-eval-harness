"""S5-EVAL interface contract conformance of the corpus."""

from __future__ import annotations

from assistant_eval.runner import load_corpus, validate_corpus
from assistant_eval.s5_eval_interface import (
    CORPUS_REQUIRED_FIELDS,
    P1_TOOLS,
    QA_ANNOTATION_FIELDS,
    ROUTE_ANNOTATION_FIELDS,
)


def test_corpus_conforms_to_contract() -> None:
    items = load_corpus("corpus.jsonl")
    assert validate_corpus(items) == []


def test_qa_annotations_carry_required_fields() -> None:
    items = load_corpus("corpus.jsonl")
    for it in items:
        if it["kind"] == "kb_qa":
            for k in QA_ANNOTATION_FIELDS:
                assert k in it["annotations"], f"{it['id']} missing {k}"


def test_route_annotations_carry_required_fields() -> None:
    items = load_corpus("corpus.jsonl")
    for it in items:
        if it["kind"] == "tool_route":
            for k in ROUTE_ANNOTATION_FIELDS:
                assert k in it["annotations"], f"{it['id']} missing {k}"


def test_ids_unique_and_required_fields_present() -> None:
    items = load_corpus("corpus.jsonl")
    assert len({it["id"] for it in items}) == len(items)
    for it in items:
        for k in CORPUS_REQUIRED_FIELDS:
            assert k in it, f"{it['id']} missing {k}"


def test_tools_are_p1_set() -> None:
    items = load_corpus("corpus.jsonl")
    for it in items:
        if it["kind"] == "tool_route":
            assert it["tool"] in P1_TOOLS
