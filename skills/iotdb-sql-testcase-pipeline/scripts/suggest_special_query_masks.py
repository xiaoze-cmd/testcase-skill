#!/usr/bin/env python3
"""Suggest special_query.csv rows from SQL-test .result/.out differences."""

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
        notes.append("column headers differ; inspect manually")
        return set(), notes

    differing_columns: set[str] = set()
    if len(result.rows) != len(output.rows):
        notes.append(f"row count differs: result={len(result.rows)}, out={len(output.rows)}")

    for left, right in zip(result.rows, output.rows):
        for idx, (left_value, right_value) in enumerate(zip(left, right)):
            if left_value != right_value:
                differing_columns.add(result.columns[idx])
    return differing_columns, notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List SQL-test .result/.out differing columns and suggest special_query.csv rows."
    )
    parser.add_argument("--result", required=True, help="Baseline .result file")
    parser.add_argument("--out", required=True, help="Test .out file")
    parser.add_argument(
        "--include-business-columns",
        action="store_true",
        help="Suggest all differing columns. By default only known volatile columns are suggested.",
    )
    args = parser.parse_args()

    result_blocks = {(normalize_key(b.sql), b.occurrence): b for b in split_blocks(Path(args.result))}
    out_blocks = {(normalize_key(b.sql), b.occurrence): b for b in split_blocks(Path(args.out))}

    suggestions: list[str] = []
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
        print(f"\nSQL: {result_block.sql}")
        if notes:
            for note in notes:
                print(f"  NOTE: {note}")
        if differing_columns:
            print("  Differing result columns: " + ", ".join(sorted(differing_columns)))
            volatile = [
                col for col in sorted(differing_columns) if normalize_col(col) in KNOWN_VOLATILE_COLUMNS
            ]
            if args.include_business_columns:
                mask_cols = sorted(differing_columns)
            else:
                mask_cols = volatile
            if mask_cols:
                row = result_block.sql + ";" + ";".join(mask_cols) + ";"
                suggestions.append(row)
                print("  Suggested special_query.csv row: " + row)
            else:
                print("  No automatic mask suggestion; differing columns look business-related.")

    if suggestions:
        print("\nSuggested special_query.csv additions:")
        for row in suggestions:
            print(row)
    elif not printed_any:
        print("No comparable result table differences found. Tool status lines such as Elapsed Time are ignored.")
    else:
        print("\nNo automatic special_query.csv additions suggested.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
