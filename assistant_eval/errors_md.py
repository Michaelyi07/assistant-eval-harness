"""errors.md generation from the runner's mismatch records (rework item 3).

Root-cause classes are DERIVED from the actual mismatch problems of the run
(citation out of annotated set / missing points / incorrect or missed refusal /
tool selection error / parameter error) -- no pre-assigned labels exist. The
error output block is the evaluated answerer's actual output, verbatim.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

# problem-text fragment -> root-cause class (derived, not pre-assigned)
CLASS_RULES: list[tuple[str, str]] = [
    ("citations outside annotated set", "citation_id_mismatch"),
    ("missing expected points", "point_miss"),
    ("answerable item was refused", "incorrect_refusal"),
    ("no-answer item was answered", "missed_refusal"),
    ("tool mismatch", "tool_selection_error"),
    ("parameter mismatch", "parameter_error"),
    ("cross-boundary request was not rejected", "boundary_miss"),
    ("in-bounds request was rejected", "incorrect_refusal"),
]

FIX_CATEGORIES = {
    "citation_id_mismatch": "retrieval-filter-tightening",
    "point_miss": "answer-composition",
    "incorrect_refusal": "refusal-gate",
    "missed_refusal": "refusal-gate",
    "tool_selection_error": "router-intent-training",
    "parameter_error": "slot-filling",
    "boundary_miss": "boundary-rules",
    "other": "to-be-assigned",
}


def classify(problems: list[str]) -> str:
    joined = " | ".join(problems)
    for fragment, cls in CLASS_RULES:
        if fragment in joined:
            return cls
    return "other"


def _fmt_expected(expected: dict) -> str:
    return json.dumps(expected, ensure_ascii=False, sort_keys=True)


def render_errors(errors: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# 首轮典型错误分析")
    lines.append("")
    lines.append(f"错误条目共 {len(errors)} 条，全部来自被测作答方（mock 助手，基于固定桩）"
                 "实际输出与标注的不匹配记录；原因分类由不匹配内容推导，无预设标签。")
    lines.append("")
    class_counter: Counter = Counter()
    for i, e in enumerate(errors, 1):
        fc = classify(e["problems"])
        class_counter[fc] += 1
        lines.append(f"## {i}. {e['item_id']}")
        lines.append("")
        lines.append(f"- 问题/路由：{e['question']}")
        lines.append(f"- 期望：{_fmt_expected(e['expected'])}")
        lines.append("- 错误输出（被测作答方实际输出，逐字）：")
        lines.append("  ```json")
        for ln in json.dumps(e["error_output"], ensure_ascii=False, indent=2).splitlines():
            lines.append("  " + ln)
        lines.append("  ```")
        lines.append(f"- 判定：{'；'.join(e['problems'])}")
        lines.append(f"- 原因分类：{fc}")
        lines.append(f"- 修复类别：{FIX_CATEGORIES.get(fc, FIX_CATEGORIES['other'])}")
        lines.append("")
    lines.append("## 根因分类汇总")
    lines.append("")
    lines.append("| 原因分类 | 条数 |")
    lines.append("|---|---|")
    for fc, n in class_counter.most_common():
        lines.append(f"| {fc} | {n} |")
    lines.append("")
    return "\n".join(lines)


def write_errors(errors: list[dict], path: str | Path) -> Path:
    p = Path(path)
    p.write_text(render_errors(errors), encoding="utf-8")
    return p


def load_errors(path: str | Path) -> list[dict]:
    out = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
