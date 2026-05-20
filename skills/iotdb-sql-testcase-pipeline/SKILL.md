---
name: iotdb-sql-testcase-pipeline
description: Use when Codex needs to turn IoTDB/TimechoDB requirements, design docs, issues, or manual topics into detailed Markdown test cases, atomic test-point matrices, test-point expansion tables, and optional .run/benchmark/wrapper artifacts.
---

# IoTDB SQL Testcase Pipeline

## Overview
This skill is generation-only. It analyzes requirements and produces test design artifacts; it does not perform remote execution, deployment, cleanup, or reporting.

Use Simplified Chinese for user-facing text.

## Required References
- Read `references/pipeline-rules.md` before generating artifacts.
- Use `scripts/lint_case_artifacts.py` to validate Markdown and `.run` artifacts when applicable.

## Test Design Gate
1. Build an atomic test-point matrix first.
2. Analyze behavior, not wording.
3. Prove each claim with an observable action.
4. Design paired coverage.
5. Preserve detail; do not collapse scenarios.
6. Use stable assertions.
7. List assumptions and open questions before generation.

## Case Expansion Gate
1. Distinguish test points from cases.
2. Create a test-point expansion table.
3. One TP maps to one TC only when the point is truly single-action, single-assertion, and has no variants.
4. Split any point containing triggers like `separately`, `true/false`, `on/off`, `DROP VIEW/DROP TABLE`, `ALTER TABLE/ALTER VIEW`, `source/target`, `single/batch/concurrent`, `pattern/privilege`, or `missing any privilege`.
5. Permission, config, DDL, sync, performance, and large-data points normally expand into multiple cases.
6. The coverage self-review must report counts, expansions, gaps, and one-to-one reasons.

## Output Routing
1. SQL-executable scenarios -> Markdown + `.run`.
2. Large-data/performance scenarios -> Markdown + benchmark config or wrapper, plus minimal validation steps if needed.
3. Non-SQL tool scenarios -> Markdown + wrapper.
4. Not enough info or blocked -> Markdown only, with explicit reason.
5. Do not write execution or deployment instructions as if they were completed actions.

## Workflow
1. Collect the requirement item, version, target model, source docs, local artifact directory, and optional benchmark tool path when relevant.
2. Search the official manual by default.
3. Create the local artifact directory; split tree/table outputs when the model is both.
4. Generate the atomic matrix.
5. Generate the expansion table.
6. Generate the detailed Markdown case table.
7. Route each scenario to the appropriate artifact type.
8. Run static checks and revise gaps before finishing.

## Guardrails
- No remote execution, deployment, cleanup, pullback, or report generation.
- Do not treat a requirement sentence as coverage.
- Do not compress complex test points into one case.
- Do not use metadata-only checks as proof of data-path behavior.
- Large data should be routed to benchmark artifacts instead of massive literal inserts.
- If a point cannot be automated, mark it design-only and explain why.

## Output Shape
- Local Markdown case path
- Local artifact path
- Coverage gaps
- Assumptions / blockers
