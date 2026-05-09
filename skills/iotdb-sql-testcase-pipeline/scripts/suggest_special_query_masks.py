#!/usr/bin/env python3
"""根据 SQL-test .result/.out 差异建议 special_query.csv 屏蔽列。"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


BLOCK_RE = re.compile(r"^--\s*\[[^\]]+\]\s*\d+:(.*)$")
HEADER_COL_RE = re.compile(r"^\s*(.*?)\s*\([^)]*\)\s*$")

IGNORED_STATUS_PREFIXES = (
    "Elapsed Time:",
    "###### COMPARE RESULT",
)

KNOWN_VOLATILE_COLUMNS = {
    "time",
    "query_id",
    "queryid",
    "start_time",
    "starttime",
    "elapsed_time",
    "elapsedtime",
    "wait_time_in_server",
    "waittimeinserver",
    "datanode_id",
    "datanodeid",
    "regionid",
    "createtime",
    "create_time",
    "tsfilesize",
    "compressionratio",
    "internaladdress",
    "buildinfo",
    "usage",
    "remainingeventcount",
    "estimatedremainingseconds",
}


@dataclass
class Block:
    sql: str
    occurrence: int
    lines: list[str]


@dataclass
class Table:
    columns: list[str]
    rows: list[list[str]]


@dataclass
class Suggestion:
    sql: str
    columns: list[str]
    row: str


def normalize_key(value: str) -> str:
    return value.strip().lower()


def normalize_col(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", value.strip().lower())


def strip_status_lines(lines: list[str]) -> list[str]:
    stripped: list[str] = []
    for line in lines:
        text = line.strip()
        if any(text.startswith(prefix) for prefix in IGNORED_STATUS_PREFIXES):
            continue
        stripped.append(line.rstrip("\n"))
    return stripped


def split_blocks(path: Path) -> list[Block]:
    counts: dict[str, int] = defaultdict(int)
    blocks: list[Block] = []
    current_sql: str | None = None
    current_lines: list[str] = []

    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        match = BLOCK_RE.match(raw)
        if match:
            if current_sql is not None:
                key = normalize_key(current_sql)
                counts[key] += 1
                blocks.append(Block(current_sql, counts[key], current_lines))
            current_sql = match.group(1).strip()
            current_lines = [raw]
        elif current_sql is not None:
            current_lines.append(raw)

    if current_sql is not None:
        key = normalize_key(current_sql)
        counts[key] += 1
        blocks.append(Block(current_sql, counts[key], current_lines))

    return blocks


def split_pipe_row(line: str) -> list[str]:
    parts = [part.strip() for part in line.split("|")]
    while parts and parts[-1] == "":
        parts.pop()
    while parts and parts[0] == "":
        parts.pop(0)
    return parts


def parse_header(line: str) -> list[str] | None:
    if "|" not in line or "(" not in line or ")" not in line:
        return None
    columns: list[str] = []
    for part in split_pipe_row(line):
        match = HEADER_COL_RE.match(part)
        if not match:
            return None
        columns.append(match.group(1).strip())
    return columns or None


def parse_table(block: Block) -> Table | None:
    lines = strip_status_lines(block.lines)
    header_index = -1
    columns: list[str] | None = None
    for idx, line in enumerate(lines):
        columns = parse_header(line)
        if columns:
            header_index = idx
            break
    if not columns or header_index < 0:
        return None

    rows: list[list[str]] = []
    for line in lines[header_index + 1 :]:
        text = line.strip()
        if not text or text == "}" or text.startswith("总数目") or text.startswith("Total"):
            continue
        if set(text) <= {"-", "|", " "}:
            continue
        if "|" not in line:
            continue
        parts = split_pipe_row(line)
        if len(parts) >= len(columns):
            rows.append(parts[: len(columns)])
    return Table(columns, rows)


def compare_tables(result: Table, output: Table) -> tuple[set[str], list[str]]:
    notes: list[str] = []
    if [normalize_col(c) for c in result.columns] != [normalize_col(c) for c in output.columns]:
        notes.append("列名不一致，需要人工检查")
        return set(), notes

    differing_columns: set[str] = set()
    if len(result.rows) != len(output.rows):
        notes.append(f"行数不一致：result={len(result.rows)}，out={len(output.rows)}")

    for left, right in zip(result.rows, output.rows):
        for idx, (left_value, right_value) in enumerate(zip(left, right)):
            if left_value != right_value:
                differing_columns.add(result.columns[idx])
    return differing_columns, notes


def parse_special_query_row(row: str) -> tuple[str, list[str]]:
    parts = [part.strip() for part in row.rstrip("\n").split(";")]
    while parts and parts[-1] == "":
        parts.pop()
    if not parts:
        return "", []
    return parts[0], [part for part in parts[1:] if part]


def merge_special_query(path: Path, suggestions: list[Suggestion]) -> list[str]:
    existing_lines: list[str] = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    index: dict[str, tuple[int, str, list[str]]] = {}
    for idx, line in enumerate(existing_lines):
        sql, columns = parse_special_query_row(line)
        if sql:
            index[normalize_key(sql)] = (idx, sql, columns)

    changes: list[str] = []
    for suggestion in suggestions:
        key = normalize_key(suggestion.sql)
        if key in index:
            idx, sql, columns = index[key]
            seen = {normalize_col(column) for column in columns}
            added = [column for column in suggestion.columns if normalize_col(column) not in seen]
            if not added:
                changes.append(f"未变更：{suggestion.sql}")
                continue
            merged = columns + added
            existing_lines[idx] = sql + ";" + ";".join(merged) + ";"
            index[key] = (idx, sql, merged)
            changes.append(f"已更新：{suggestion.sql}；新增列 {', '.join(added)}")
        else:
            existing_lines.append(suggestion.row)
            index[key] = (len(existing_lines) - 1, suggestion.sql, suggestion.columns)
            changes.append(f"已新增：{suggestion.row}")

    content = "\n".join(existing_lines)
    if content:
        content += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="列出 SQL-test .result/.out 差异列，并建议 special_query.csv 屏蔽行。"
    )
    parser.add_argument("--result", required=True, help="基准 .result 文件")
    parser.add_argument("--out", required=True, help="测试 .out 文件")
    parser.add_argument(
        "--include-business-columns",
        action="store_true",
        help="建议所有差异列。默认只建议已知不稳定列。",
    )
    parser.add_argument("--special-query", help="user/CONFIG/special_query.csv 路径")
    parser.add_argument(
        "--append",
        action="store_true",
        help="追加或合并建议屏蔽列到 --special-query。只应在用户确认后使用。",
    )
    args = parser.parse_args()
    if args.append and not args.special_query:
        parser.error("--append requires --special-query")

    result_blocks = {(normalize_key(b.sql), b.occurrence): b for b in split_blocks(Path(args.result))}
    out_blocks = {(normalize_key(b.sql), b.occurrence): b for b in split_blocks(Path(args.out))}

    suggestions: list[Suggestion] = []
    printed_any = False
    for key in sorted(set(result_blocks) & set(out_blocks)):
        result_block = result_blocks[key]
        out_block = out_blocks[key]
        result_table = parse_table(result_block)
        out_table = parse_table(out_block)
        if not result_table or not out_table:
            continue

        differing_columns, notes = compare_tables(result_table, out_table)
        if not differing_columns and not notes:
            continue

        printed_any = True
        print(f"\nSQL 语句：{result_block.sql}")
        if notes:
            for note in notes:
                print(f"  提示：{note}")
        if differing_columns:
            print("  差异结果列：" + ", ".join(sorted(differing_columns)))
            volatile = [
                col for col in sorted(differing_columns) if normalize_col(col) in KNOWN_VOLATILE_COLUMNS
            ]
            if args.include_business_columns:
                mask_cols = sorted(differing_columns)
            else:
                mask_cols = volatile
            if mask_cols:
                row = result_block.sql + ";" + ";".join(mask_cols) + ";"
                suggestions.append(Suggestion(result_block.sql, mask_cols, row))
                print("  建议追加的 special_query.csv 行：" + row)
            else:
                print("  未自动建议屏蔽列；差异列看起来是业务结果列，需要人工确认。")

    if suggestions:
        print("\n建议追加到 special_query.csv 的内容：")
        for suggestion in suggestions:
            print(suggestion.row)
        print("\n下一步请选择：")
        print("1. 再次运行比对：如果差异可能来自环境波动，重新执行一次 test 后再比较。")
        if args.special_query:
            append_cmd = (
                f"python {Path(__file__).name} --result {args.result} --out {args.out} "
                f"--special-query {args.special_query} --append"
            )
            if args.include_business_columns:
                append_cmd += " --include-business-columns"
            print("2. 追加/合并屏蔽列到 special_query.csv：")
            print("   " + append_cmd)
        else:
            print("2. 确认后追加/合并屏蔽列到 special_query.csv。")
            print("   使用 --special-query <path> --append 重新运行本脚本。")
        if args.append:
            changes = merge_special_query(Path(args.special_query), suggestions)
            print("\n已应用 special_query.csv 变更：")
            for change in changes:
                print("- " + change)
    elif not printed_any:
        print("没有找到可比较的结果表差异。已忽略 Elapsed Time 等工具状态行。")
    else:
        print("\n没有自动建议追加到 special_query.csv 的内容。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
