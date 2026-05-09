#!/usr/bin/env python3
"""IoTDB SQL Markdown 用例和 .run 产物轻量检查。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_MD_COLUMNS = [
    "用例编号",
    "用例名称",
    "用例级别",
    "模块类型",
    "二级分类",
    "需求来源",
    "前置条件",
    "测试数据",
    "操作步骤",
    "预期结果",
    "清理动作",
    "备注",
    "测试结果",
    "截图",
]

SECRET_PATTERNS = [
    re.compile(r"IoTDB@\d{4,}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----"),
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
]


def check_no_secrets(path: Path, text: str) -> list[str]:
    issues = []
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            issues.append(f"{path}: 可能包含敏感信息：{pat.pattern}")
    return issues


def lint_md(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    issues = check_no_secrets(path, text)
    header_line = next((line for line in text.splitlines() if line.strip().startswith("|") and "用例编号" in line), "")
    for col in REQUIRED_MD_COLUMNS:
        if col not in header_line:
            issues.append(f"{path}: 缺少必需 Markdown 列：{col}")
    if text.count("| TC-") == 0 and "TC-" not in text:
        issues.append(f"{path}: 没有找到稳定的 TC-* 用例编号")
    for term, chinese in [("setup", "准备"), ("cleanup", "清理")]:
        if term not in text.lower() and chinese not in text:
            issues.append(f"{path}: 缺少明确的 {term}/{chinese} 步骤")
    return issues


def split_run_cases(text: str) -> list[str]:
    positions = [m.start() for m in re.finditer(r"(?m)^--\s*用例\s+TC-", text)]
    if not positions:
        return [text] if text.strip() else []
    positions.append(len(text))
    return [text[positions[i] : positions[i + 1]] for i in range(len(positions) - 1)]


def lint_run(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    issues = check_no_secrets(path, text)
    if "connect " not in text.lower():
        issues.append(f"{path}: 缺少 connect 语句")
    if not any(marker in text for marker in ["<<NULL;", "<<SQLSTATE;", "<<CHECKCODE;"]):
        issues.append(f"{path}: 缺少 SQL 自动化标记")
    for idx, case in enumerate(split_run_cases(text), start=1):
        low = case.lower()
        if "drop database" not in low and "drop table" not in low and "delete" not in low:
            issues.append(f"{path}: 第 {idx} 条用例没有可见清理语句")
        if "select " in low and "order by" not in low and "<<CHECKCODE;" not in case:
            issues.append(f"{path}: 第 {idx} 条用例查询结果可能不稳定；请添加 ORDER BY 或说明 CHECKCODE 的必要性")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Markdown 用例和 .run 文件")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    issues: list[str] = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            issues.append(f"{path}: 文件不存在")
            continue
        if path.suffix.lower() == ".md":
            issues.extend(lint_md(path))
        elif path.suffix.lower() == ".run":
            issues.extend(lint_run(path))
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print("检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
