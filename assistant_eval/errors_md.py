"""errors.md generation from the runner's error records + baseline defect metadata."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from assistant_eval.baseline.answers import FileBackedAnswerer


def _fmt_expected(expected: dict) -> str:
    return json.dumps(expected, ensure_ascii=False, sort_keys=True)


def render_errors(errors: list[dict], answerer: FileBackedAnswerer) -> str:
    meta = answerer.defect_meta()
    lines: list[str] = []
    lines.append("# 首轮典型错误分析")
    lines.append("")
    lines.append(f"错误条目共 {len(errors)} 条（首轮运行由 run_eval.py 实际产出，"
                 "原始错误输出块逐字保留）。")
    lines.append("")
    class_counter: Counter = Counter()
    for i, e in enumerate(errors, 1):
        m = meta.get(e["item_id"], {})
        fc = m.get("failure_class") or "other"
        class_counter[fc] += 1
        lines.append(f"## {i}. {e['item_id']}")
        lines.append("")
        lines.append(f"- 问题/路由：{e['question']}")
        lines.append(f"- 期望：{_fmt_expected(e['expected'])}")
        lines.append("- 错误输出（原始，逐字）：")
        lines.append("  ```json")
        for ln in json.dumps(e["error_output"], ensure_ascii=False, indent=2).splitlines():
            lines.append("  " + ln)
        lines.append("  ```")
        lines.append(f"- 判定：{'；'.join(e['problems'])}")
        lines.append(f"- 原因分类：{fc}")
        lines.append(f"- 修复类别：{m.get('fix_category', 'to-be-assigned')}")
        if m.get("note"):
            lines.append(f"- 备注：{m['note']}")
        lines.append("")
    lines.append("## 根因分类汇总")
    lines.append("")
    lines.append("| 原因分类 | 条数 |")
    lines.append("|---|---|")
    for fc, n in class_counter.most_common():
        lines.append(f"| {fc} | {n} |")
    lines.append("")
    return "\n".join(lines)


def write_errors(errors: list[dict], answerer: FileBackedAnswerer, path: str | Path) -> Path:
    p = Path(path)
    p.write_text(render_errors(errors, answerer), encoding="utf-8")
    return p


def load_errors(path: str | Path) -> list[dict]:
    out = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
