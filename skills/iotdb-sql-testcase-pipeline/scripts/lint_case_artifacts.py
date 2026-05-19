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
    "一级分类",
    "模块类型",
    "二级分类",
    "需求来源",
    "前置条件",
    "操作数据",
    "测试数据",
    "操作步骤",
    "预期结果",
    "清理动作",
    "备注",
    "测试结果",
    "截图",
]

TEST_POINT_ID_RE = re.compile(r"\b(?:TP|[A-Z]+-TP|TP-SQL)-\d+\b")
CASE_ID_RE = re.compile(r"\b(?:TC|[A-Z]+-TC|TC-SQL)-\d+\b")
DEFERRED_TERMS = ["后续专项", "人工验证", "不纳入本轮", "暂不纳入", "后续验证"]
DEFERRED_REQUIRED_TERMS = ["阻塞原因", "无法自动化", "触发动作", "证据", "验证方式", "wrapper", "benchmark", "远端命令"]

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


def split_md_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def markdown_rows(text: str) -> list[list[str]]:
    return [row for row in (split_md_row(line) for line in text.splitlines()) if row]


def lint_md(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    issues = check_no_secrets(path, text)
    rows = markdown_rows(text)
    header = next((row for row in rows if row and row[0] == "用例编号"), [])
    header_line = "|".join(header)
    for col in REQUIRED_MD_COLUMNS:
        if col not in header_line:
            issues.append(f"{path}: 缺少必需 Markdown 列：{col}")

    case_rows = [row for row in rows if row and CASE_ID_RE.fullmatch(row[0])]
    case_count = len(case_rows)
    if case_count == 0 and not CASE_ID_RE.search(text):
        issues.append(f"{path}: 没有找到稳定的 TC-* 用例编号")

    if "测试点矩阵" not in text and "Test Point Matrix" not in text:
        issues.append(f"{path}: 缺少测试点矩阵；不能直接从需求生成用例表")

    test_point_ids = set(TEST_POINT_ID_RE.findall(text))
    if not test_point_ids:
        issues.append(f"{path}: 缺少 TP-* 测试点编号，无法追踪需求拆解到用例")
    elif case_count and case_count < len(test_point_ids):
        issues.append(f"{path}: 用例数量少于测试点数量，疑似多个测试点被压缩；用例 {case_count} 条，测试点 {len(test_point_ids)} 个")

    priorities = {cell for row in case_rows for cell in row if cell in {"P0", "P1", "P2"}}
    if case_count >= 10 and "P1" not in priorities:
        issues.append(f"{path}: 10 条以上用例缺少 P1 边界/组合覆盖")
    if case_count >= 10 and "P2" not in priorities and "无 P2" not in text:
        issues.append(f"{path}: 10 条以上用例缺少 P2 异常/兼容/集群/性能覆盖；如确实无 P2，请在自检中写明“无 P2”原因")

    for row in case_rows:
        mapped = TEST_POINT_ID_RE.findall("|".join(row))
        if len(set(mapped)) > 3:
            issues.append(f"{path}: {row[0]} 关联测试点过多，疑似把多个独立规则合并到一条用例")

    if any(term in text for term in DEFERRED_TERMS) and not any(term in text for term in DEFERRED_REQUIRED_TERMS):
        issues.append(f"{path}: 存在后续专项/人工验证描述，但缺少阻塞原因、触发动作或证据计划")

    if not any(term in text for term in ["覆盖性自检", "覆盖缺口", "自检"]):
        issues.append(f"{path}: 缺少生成后的覆盖性自检或覆盖缺口说明")

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
