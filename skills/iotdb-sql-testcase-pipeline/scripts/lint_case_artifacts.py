#!/usr/bin/env python3
"""Lightweight lint for IoTDB SQL testcase Markdown and .run artifacts."""

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
            issues.append(f"{path}: contains possible secret: {pat.pattern}")
    return issues


def lint_md(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    issues = check_no_secrets(path, text)
    header_line = next((line for line in text.splitlines() if line.strip().startswith("|") and "用例编号" in line), "")
    for col in REQUIRED_MD_COLUMNS:
        if col not in header_line:
            issues.append(f"{path}: missing required Markdown column: {col}")
    if text.count("| TC-") == 0 and "TC-" not in text:
        issues.append(f"{path}: no stable TC-* case IDs found")
    for term in ["setup", "cleanup"]:
        if term not in text.lower() and {"setup": "清理", "cleanup": "清理"}[term] not in text:
            issues.append(f"{path}: expected explicit {term} steps")
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
        issues.append(f"{path}: missing connect statement")
    if not any(marker in text for marker in ["<<NULL;", "<<SQLSTATE;", "<<CHECKCODE;"]):
        issues.append(f"{path}: missing SQL automation markers")
    for idx, case in enumerate(split_run_cases(text), start=1):
        low = case.lower()
        if "drop database" not in low and "drop table" not in low and "delete" not in low:
            issues.append(f"{path}: case {idx} has no visible cleanup statement")
        if "select " in low and "order by" not in low and "<<CHECKCODE;" not in case:
            issues.append(f"{path}: case {idx} query may have unstable output; add ORDER BY or justify CHECKCODE")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint testcase Markdown and .run files")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    issues: list[str] = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            issues.append(f"{path}: file does not exist")
            continue
        if path.suffix.lower() == ".md":
            issues.extend(lint_md(path))
        elif path.suffix.lower() == ".run":
            issues.extend(lint_run(path))
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print("lint passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
