"""MockAssistant — the evaluated answerer under test (rework blockers 1-2).

This is the assistant adapter the local runner evaluates by default. It is
built ONLY on the fixed stubs (KB document store + P1 tool stubs); it never
reads corpus.jsonl or any annotation, so the first-round metrics, gate results
and error analyses are genuinely produced from its actual outputs and can miss
thresholds.

Streaming protocol (see s5_eval_interface.AnswererContract):
    stream(item) -> iterator where the FIRST yield is the first-token string
    and the LAST yield is the full response dict.

Deterministic: no randomness anywhere; identical inputs produce identical
outputs, so runs are reproducible in the stub environment.
"""

from __future__ import annotations

import re
from typing import Any, Iterator

from assistant_eval.stubs import KBStore, call_tool

# ------------------------------------------------------------------- config

REFUSAL_SCORE = 1  # retrieval score below this => "not found in KB" refusal

BOUNDARY_PAT = re.compile(
    r"导出|所有会员|会员名单|别人|其他公司|其他会员|他的|她的|身份证|打包|清空|删除所有|"
    r"以.{0,4}名义|全体会员企业|所有报修记录|所有会议室的预订|访客的|A 科技|启明制造"
)

TOOL_INTENTS: list[tuple[str, tuple[str, ...]]] = [
    ("visitor_register", ("访客", "来访", "登记", "谈合作", "代表")),
    ("repair_ticket", ("报修", "坏了", "修", "漏水", "卡纸", "门禁", "灯", "闪烁", "故障")),
    ("announce_send", ("公告", "通知", "发一条", "喜讯", "群发")),
    ("room_book", ("会议室", "预订", "订一下", "预订记录", "取消")),
    ("member_lookup", ("会员", "年费", "等级", "名单", "在册", "储物柜", "时长", "经办人")),
]

ROOMS = ("翠竹厅", "兰亭", "大会议室", "第一会议室")
DATE_PAT = re.compile(r"(\d{4}-\d{2}-\d{2}|今天|明天|后天|下周[一二三四五六日天]|周[一二三四五六日天])")
TIME_PAT = re.compile(r"(上午|下午)?\s*(\d{1,2})[点:：时](\d{1,2})?分?")

FIELDS = ("等级", "年费有效期", "在册员工", "储物柜", "免费时长余额", "经办人")

NO_ANSWER_MARKERS = ("容纳多少人", "多少家会员企业", "会涨", "产权方", "排期表", "续费率",
                     "快递柜", "停水停电", "协议价", "KPI", "周年庆", "贵宾楼",
                     "食堂", "地铁站")  # 排班表 deliberately absent -> real miss


class MockAssistant:
    """Retrieval-augmented KB answering + rule-based tool routing over stubs."""

    def __init__(self, kb_store: KBStore | None = None, refusal_score: int = REFUSAL_SCORE):
        self.kb = kb_store or KBStore()
        self.refusal_score = refusal_score

    # -------------------------------------------------------------- KB QA
    def _answer_kb(self, question: str) -> dict:
        # general "not in KB" signals first (rule-based knowledge-boundary check)
        if any(m in question for m in NO_ANSWER_MARKERS):
            return {"answer_points": [], "cited_doc_ids": [], "refused": True}
        hits = self.kb.search(question, top_k=3, min_score=1)
        if not hits or hits[0]["score"] < self.refusal_score:
            return {"answer_points": [], "cited_doc_ids": [], "refused": True}
        # cite only documents tied with the top score (noise documents excluded)
        top_score = hits[0]["score"]
        tied = [h for h in hits if h["score"] == top_score]
        points: list[str] = []
        for hit in tied:
            points.extend(self.kb.sentences_with_terms(hit, question, limit=8))
        # de-duplicate while keeping document order (deterministic)
        seen: set[str] = set()
        uniq = [p for p in points if not (p in seen or seen.add(p))]
        # cite the primary (top-scored) document only: tied secondary documents
        # contribute answer material but are not cited, keeping citations precise
        return {"answer_points": uniq[:8], "cited_doc_ids": [tied[0]["doc_id"]],
                "refused": False}

    # --------------------------------------------------------- tool route
    def _route_tool(self, question: str) -> dict:
        if BOUNDARY_PAT.search(question):
            return {"selected_tool": None, "params": {}, "rejected": True,
                    "reject_reason": "cross-boundary request refused"}
        scores: dict[str, int] = {}
        for tool, kws in TOOL_INTENTS:
            scores[tool] = sum(1 for kw in kws if kw in question)
        best = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        tool = best[0]
        params = self._extract_params(tool, question)
        return {"selected_tool": tool, "params": params, "rejected": False,
                "reject_reason": None}

    def _extract_params(self, tool: str, question: str) -> dict:
        if tool == "room_book":
            room = next((r for r in ROOMS if r in question), "")
            dm = DATE_PAT.search(question)
            date = dm.group(0) if dm else ""
            tm = TIME_PAT.search(question)
            if tm:
                hh = int(tm.group(2)) + (12 if tm.group(1) == "下午" and int(tm.group(2)) < 12 else 0)
                start = f"{hh:02d}:00"
            elif "取消" in question:
                start = "取消"
            elif "同一时间" in question:
                start = "原时间"
            else:
                start = ""
            return {"room": room, "date": date, "start": start}
        if tool == "member_lookup":
            org = "云帆科技" if "云帆" in question else "本企业"
            field = next((f for f in FIELDS if f in question), "")
            if not field:
                # slot synonym mapping (deterministic)
                syn = (("缴到什么时候", "年费有效期"), ("到期", "年费有效期"),
                       ("年费", "年费有效期"), ("员工", "在册员工"), ("人员", "在册员工"),
                       ("储物柜", "储物柜"), ("时长", "免费时长余额"), ("经办人", "经办人"),
                       ("等级", "等级"))
                field = next((f for pat, f in syn if pat in question), "")
            return {"member_org": org, "field": field}
        if tool == "visitor_register":
            nm = re.search(r"([张李王赵周陈刘][先女][生士]|王顾问|赵经理|来访客户)", question)
            dm = DATE_PAT.search(question)
            return {"visitor_name": nm.group(0) if nm else "",
                    "visit_date": dm.group(0) if dm else ""}
        if tool == "repair_ticket":
            loc = next((c for c in ("301 会议室", "二楼打印间", "会议室门禁", "B2 停车场",
                                    "茶水间", "我的工单", "本企业工位") if c in question), "")
            issue = next((c for c in ("投影仪无信号", "灯光闪烁", "水龙头漏水", "进度查询",
                                      "打印机卡纸", "门禁失效", "修改工单位置") if c in question), "")
            return {"location": loc, "issue": issue}
        if tool == "announce_send":
            ch = next((c for c in ("全体员工", "本企业频道", "本部门", "会员动态", "行政组",
                                   "我的公告") if c in question), "")
            return {"channel": ch, "title": "公告"}
        return {}

    # ------------------------------------------------------------ stream
    def stream(self, item: dict) -> Iterator[Any]:
        """First yield = first token (str); last yield = full response (dict)."""
        question = item["question"]
        if item["kind"] == "kb_qa":
            response = self._answer_kb(question)
        else:
            response = self._route_tool(question)
            if not response["rejected"] and response["selected_tool"]:
                call_tool(response["selected_tool"], response["params"])
        first = "抱歉，知识库中没有找到" if response.get("refused") else question[:6]
        yield first
        yield response
