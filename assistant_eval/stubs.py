"""Fixed stubs for the KB documents and the five P1 tools (order scope).

These are the stub data interfaces the order requires: the evaluated assistant
(or its mock) retrieves knowledge and calls tools ONLY through these stubs, so
every metric is reproducible. Connection points to S3-KB and the tool work
orders are documented in README "S3-KB / tool integration".
"""

from __future__ import annotations

import json
import zlib
from pathlib import Path
from typing import Any

_STUBS_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class KBStore:
    """Fixed KB document store with a deterministic keyword-retrieval stub.

    This stub stands in for the real S3-KB retrieval service (out of scope for
    this order): same interface, fixed data, deterministic ranking."""

    def __init__(self, documents_path: str | Path | None = None):
        p = Path(documents_path) if documents_path else _STUBS_DIR / "kb_documents.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        self.documents: dict[str, dict] = {d["doc_id"]: d for d in data["documents"]}

    def all_doc_ids(self) -> list[str]:
        return sorted(self.documents)

    @staticmethod
    def _terms(text: str) -> list[str]:
        """Deterministic naive tokenisation: strip punctuation and functional
        single-character stopwords, then emit 2- and 3-gram content fragments.
        Content morphemes (年/天/层/元...) are deliberately KEPT so word forms
        like 年费 / 几层 / 明天 survive."""
        stop = set("的吗呢吧是在我要能可有和请帮想问说给把被对从为与跟这那去过来着得就很还也都")
        chars = []
        for ch in text:
            if ch.isalnum() or "\u4e00" <= ch <= "\u9fff":
                chars.append(ch)
            else:
                chars.append(" ")
        runs = ["".join(c for c in run if c not in stop) for run in "".join(chars).split()]
        terms: list[str] = []
        for run2 in runs:
            if len(run2) < 2:
                continue
            if len(run2) <= 3:
                terms.append(run2)
                continue
            for n in (2, 3):
                terms.extend(run2[i:i + n] for i in range(len(run2) - n + 1))
        return terms

    def search(self, query: str, top_k: int = 3, min_score: int = 1) -> list[dict]:
        """Deterministic retrieval: score = sum of distinct query-term weights
        present in the document (2 for 3+ char terms, 1 for bigrams); ties
        broken by doc_id for reproducibility. Distinct-term scoring keeps
        generic-word-heavy documents from outranking topic matches."""
        terms = set(self._terms(query))
        scored = []
        for doc_id in sorted(self.documents):
            doc = self.documents[doc_id]
            content = doc["content"]
            score = sum((2 if len(t) >= 3 else 1) for t in terms if t and t in content)
            # title-topic boost: a query term appearing in the doc title adds 3
            score += 3 * sum(1 for t in terms if t and len(t) >= 2 and t in doc["title"])
            if score >= min_score:
                scored.append((score, doc_id, doc))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [
            {"doc_id": d["doc_id"], "title": d["title"], "version": d["version"],
             "content": d["content"], "score": s}
            for s, _, d in scored[:top_k]
        ]

    def sentences_with_terms(self, doc: dict, query: str, limit: int = 2) -> list[str]:
        """Sentences of the document containing at least one query term, in
        document order (deterministic)."""
        terms = self._terms(query)
        sents = [s.strip() for s in doc["content"].replace("。", "\n").split("\n") if s.strip()]
        picked = [s for s in sents if any(t and t in s for t in terms)]
        return picked[:limit]


# ---------------------------------------------------------------- tool stubs

def _room_book(params: dict) -> dict:
    room = params.get("room", "")
    fixed = {
        "翠竹厅": {"room_id": "RM-001", "status": "available"},
        "兰亭": {"room_id": "RM-002", "status": "available"},
        "大会议室": {"room_id": "RM-003", "status": "available"},
        "第一会议室": {"room_id": "RM-004", "status": "available"},
    }
    info = fixed.get(room, {"room_id": "RM-UNKNOWN", "status": "unknown"})
    seed = f"{room}|{params.get('date')}|{params.get('start')}"
    return {"ok": True, "action": "room_book", "room": room, **info,
            "booking_ref": f"BK-{zlib.crc32(seed.encode()) % 100000:05d}"
            if room in fixed else None}


def _member_lookup(params: dict) -> dict:
    org = params.get("member_org", "")
    field = params.get("field", "")
    fixed = {
        ("云帆科技", "等级"): {"result": "旗舰会员"},
        ("本企业", "年费有效期"): {"result": "2026-12-31"},
        ("本企业", "在册员工"): {"result": "12 人"},
        ("本企业", "储物柜"): {"result": "公共柜 C-07"},
        ("本企业", "免费时长余额"): {"result": "2 小时"},
        ("本企业", "经办人"): {"result": "市场部 张经理"},
    }
    hit = fixed.get((org, field), {"result": "no-record"})
    return {"ok": True, "action": "member_lookup", "member_org": org, "field": field, **hit}


def _visitor_register(params: dict) -> dict:
    return {"ok": True, "action": "visitor_register",
            "visitor_name": params.get("visitor_name", ""),
            "visit_date": params.get("visit_date", ""),
            "pass_code": f"VP-{zlib.crc32(params.get('visitor_name', '').encode()) % 10000:04d}"}


def _repair_ticket(params: dict) -> dict:
    return {"ok": True, "action": "repair_ticket",
            "location": params.get("location", ""), "issue": params.get("issue", ""),
            "ticket_id": f"RT-{zlib.crc32((params.get('location', '') + '|' + params.get('issue', '')).encode()) % 100000:05d}",
            "eta_minutes": 30}


def _announce_send(params: dict) -> dict:
    return {"ok": True, "action": "announce_send",
            "channel": params.get("channel", ""), "title": params.get("title", ""),
            "message_id": f"AM-{zlib.crc32((params.get('channel', '') + '|' + params.get('title', '')).encode()) % 100000:05d}"}


TOOL_STUBS: dict[str, Any] = {
    "room_book": _room_book,
    "member_lookup": _member_lookup,
    "visitor_register": _visitor_register,
    "repair_ticket": _repair_ticket,
    "announce_send": _announce_send,
}


def call_tool(tool: str, params: dict) -> dict:
    """Fixed tool-call stub: returns canned data per P1 tool work order."""
    fn = TOOL_STUBS.get(tool)
    if fn is None:
        return {"ok": False, "error": f"unknown tool {tool!r}"}
    return fn(dict(params))
