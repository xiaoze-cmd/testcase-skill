#!/usr/bin/env python3
"""Build a fixed IoTDB SQL testcase execution report."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


def pct(passed: int, total: int) -> str:
    if total <= 0:
        return "0.00%"
    return f"{passed * 100 / total:.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build fixed execution-report.md")
    parser.add_argument("--out-dir", required=True, help="Requirement directory")
    parser.add_argument("--requirement", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--remote-command", default="")
    parser.add_argument("--remote-log", default="")
    parser.add_argument("--remote-artifacts", default="")
    parser.add_argument("--total", type=int, required=True)
    parser.add_argument("--passed", type=int, required=True)
    parser.add_argument("--failed", type=int, default=0)
    parser.add_argument("--blocked", type=int, default=0)
    parser.add_argument("--not-run", type=int, default=0, dest="not_run")
    parser.add_argument("--conclusion", choices=["PASS", "FAIL", "BLOCKED"], required=True)
    parser.add_argument("--failure-row", action="append", default=[], help="Markdown table row without leading/trailing pipe")
    parser.add_argument("--notes", default="无")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = args.failure_row or ["`无` |  |  |  "]

    report = f"""# 测试执行报告

> 固定模板：每次执行后只填写数字、路径、结论和截图。不要重新组织长篇报告。

## 基本信息

| 字段 | 内容 |
|------|------|
| 需求项 | `{args.requirement}` |
| 版本 | `{args.version}` |
| 执行日期 | `{args.date}` |
| 执行环境 | `{args.environment}` |
| 执行脚本 | `{args.script}` |
| 远端命令 | `{args.remote_command or '无'}` |
| 远端日志 | `{args.remote_log or '无'}` |
| 远端产物 | `{args.remote_artifacts or '无'}` |

## 执行结果

| 指标 | 数值 |
|------|------|
| 用例总数 | `{args.total}` |
| 通过 | `{args.passed}` |
| 失败 | `{args.failed}` |
| 阻塞 | `{args.blocked}` |
| 未执行 | `{args.not_run}` |
| 通过率 | `{pct(args.passed, args.total)}` |
| 最终结论 | `{args.conclusion}` |

## 失败明细

| 用例编号 | 结果 | 失败原因 | 日志/截图 |
|----------|------|----------|----------|
"""
    for row in failures:
        report += f"| {row} |\n"

    report += f"""
## 截图

### 执行结果截图

![执行结果](<./report-screenshot-01-execution.png>)

### 产物/日志截图

![产物日志](<./report-screenshot-02-artifacts.png>)

### 数据校验截图

![数据校验](<./report-screenshot-03-validation.png>)

## 备注

- {args.notes}
"""
    (out_dir / "execution-report.md").write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
