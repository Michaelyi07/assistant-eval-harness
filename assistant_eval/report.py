"""Deterministic report.md generation: 9-metric main table + separate cross-boundary table."""

from __future__ import annotations

from pathlib import Path

METRIC_LABELS = [
    ("answer_point_coverage", "答案要点覆盖率"),
    ("citation_accuracy", "引用准确率"),
    ("citation_completeness", "引用完整率"),
    ("correct_rejection_rate", "无答案题正确拒答率"),
    ("incorrect_rejection_rate", "有答案题误拒率"),
    ("tool_selection_accuracy", "工具选择准确率"),
    ("parameter_accuracy", "参数正确率"),
    ("cross_boundary_rejection_rate", "越界请求拒绝率"),
    ("avg_first_token_ms", "平均首字延迟 (ms)"),
    ("avg_total_ms", "平均总延迟 (ms)"),
]


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def render_report(metrics: dict, gate: dict, counts: dict | None = None) -> str:
    c = counts or metrics.get("_counts", {})
    lines: list[str] = []
    lines.append("# 首轮评测报告 — 员工 AI 助手问答与工具路由（虚构评测集）")
    lines.append("")
    lines.append("数据：120 条虚构评测集（80 知识问答 + 40 工具路由）。被测作答方为独立于标注的 "
                 "mock 助手（基于固定 KB 文档桩与五工具接口桩），指标由其真实输出计算；"
                 "延迟由 runner 用计时器对每次调用实测，数值为桩环境实测值"
                 "（内存桩，无网络、无模型推理延迟）。")
    lines.append("")
    lines.append(f"样本：知识问答 {c.get('qa_total')} 条（有答案 {c.get('answerable')} / 无答案 {c.get('no_answer')}），"
                 f"工具路由 {c.get('routes_total')} 条（正常 {c.get('normal_routes')} / 越界 {c.get('boundary_routes')}），"
                 f"总引用 {c.get('total_citations')} 次（其中命中标注集合 {c.get('correct_citations')} 次）。")
    lines.append("")
    lines.append("## 指标主表（9 项指标 + 延迟两项）")
    lines.append("")
    lines.append("| # | 指标 | 值 |")
    lines.append("|---|---|---|")
    for i, (key, label) in enumerate(METRIC_LABELS, 1):
        v = metrics[key]
        s = _pct(v) if key.endswith(("coverage", "accuracy", "completeness", "rate")) else f"{v} ms"
        lines.append(f"| {i} | {label} | {s} |")
    lines.append("")
    lines.append("## 越界请求拒绝率（单独成表，按工具拆分）")
    lines.append("")
    lines.append("| 工具 | 越界条数 | 拒绝条数 | 拒绝率 |")
    lines.append("|---|---|---|---|")
    per_tool = c.get("boundary_per_tool", {})
    for tool in sorted(per_tool):
        e = per_tool[tool]
        lines.append(f"| {tool} | {e['total']} | {e['rejected']} | {_pct(e['rejection_rate'])} |")
    lines.append(f"| **整体** | **{c.get('boundary_routes', '-')}** | "
                 f"**{sum(e['rejected'] for e in per_tool.values())}** | "
                 f"**{_pct(metrics['cross_boundary_rejection_rate'])}** |")
    lines.append("")
    lines.append("## 门槛判定")
    lines.append("")
    lines.append("| 门槛 | 结果 |")
    lines.append("|---|---|")
    for name, ok in gate["checks"].items():
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    lines.append("")
    verdict = "全部达标（exit code 0）" if gate["passed"] else "未达标（exit code 1）"
    lines.append(f"**判定：{verdict}**")
    lines.append("")
    return "\n".join(lines)


def write_report(metrics: dict, gate: dict, path: str | Path) -> Path:
    p = Path(path)
    p.write_text(render_report(metrics, gate), encoding="utf-8")
    return p
