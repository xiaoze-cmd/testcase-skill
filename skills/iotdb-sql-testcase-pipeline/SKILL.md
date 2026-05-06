---
name: iotdb-sql-testcase-pipeline
description: Use when Codex needs to turn IoTDB/TimechoDB SQL requirements, design docs, official docs, issue text, or feature directories into detailed Markdown test cases, .run automation files, remote deployment/execution, model switching, cluster restart, result collection, fixed execution reports, or screenshots.
---

# IoTDB SQL Testcase Pipeline

## Overview

Use this skill to run the end-to-end IoTDB/TimechoDB SQL testcase workflow in a reusable way: requirement analysis, detailed Markdown cases, automation file generation, remote deployment, cluster/model handling, execution, artifact pullback, and fixed-format reporting.

Always prefer the current repository's `AGENTS.md` if present. It is the project memory and may override stale details in this skill. Never store SSH passwords, tokens, or private key material in generated files.

## Required References

- Read `references/pipeline-rules.md` before generating `.run`, touching remote servers, switching models, restarting IoTDB, executing cases, or writing reports.
- Use `assets/test-execution-report-template.md` as the fixed report shape.
- Use `scripts/lint_case_artifacts.py` before deploying generated Markdown/`.run` artifacts when Python is available.
- Use `scripts/build_execution_report.py` to create a fixed report from execution metrics when the report does not already exist.

## Workflow

1. Collect the requirement text, version directory, target model (`table` or `tree`), official documentation links, target hosts, SSH key path, remote IoTDB path, and SQL automation tool path. If a URL is provided, fetch the official documentation and cite it in the Markdown case source fields.
2. Create or enter a requirement directory named after the requirement item. Put all local artifacts there.
3. Generate a detailed Markdown table case file first. Do not generate `.run` before the Markdown file exists and passes the required-field/detail checks.
4. Generate the automation artifact that matches the target:
   - `.run` for SQL automation tool flows.
   - Shell/PowerShell wrapper when the tested behavior is a tool command such as `export-data.sh`.
5. Run static checks:
   - Markdown table has the required columns.
   - Every automated case has setup, execution, assertions, cleanup, and stable expected output.
   - Long-running or performance cases are clearly marked.
   - No server password or private key material is written to repo files.
6. Deploy automation artifacts to the target server using SSH key authentication or an existing secure runtime configuration.
7. Check cluster status and ports before changing state. If a model switch or config change is required, back up the remote config first, update only the needed setting, then restart the affected IoTDB nodes.
8. Execute the automation tool or wrapper script. Do not claim success until real output has been collected and checked.
9. Pull back `.result`, `.out`, `result.xml`, logs, wrapper output, and any exported data summaries needed for validation.
10. Fill `execution-report.md` using the fixed template. Include only metrics, paths, conclusion, failure rows, notes, and screenshots/evidence images.

## Remote Defaults

When the user does not provide a different environment, use the repository memory if available. Common defaults for this project are:

- SSH user: `ubuntu`
- SSH key env var: `IOTDB_SSH_KEY`
- Fallback key path on this workstation: `C:\Users\tiany\.ssh\sql_testcase_automation_ed25519`
- SQL automation host: `172.20.70.47`
- 3C3D hosts: `172.20.70.47`, `172.20.70.48`, `172.20.70.49`
- SQL automation root: `/data/iotdb-sql-test-master`
- Script upload path: `/data/iotdb-sql-test-master/user/scripts/<feature>/<case-name>.run`

Treat these as defaults, not facts. Verify active paths and configs on the remote host before execution.

## Guardrails

- Generate detailed Markdown first, then automation files. If the user asks to skip Markdown, explain that this pipeline requires Markdown as the reviewable source of truth.
- Do not overwrite `.result` baselines unless the user explicitly asks for setup/baseline generation and the version is trusted.
- Do not delete remote IoTDB `data` or `logs` directories unless the user explicitly asks.
- Do not hardcode SSH passwords. If key-based SSH is unavailable, ask the user to configure a key or provide an interactive secure method.
- For table model cases, create a database and `use <database>` after connecting; after switching users, run `use <database>` again.
- For tree model cases, do not use `use`; use full paths such as `root.test.d1.s1`.
- For performance cases, include data volume, concurrency or loop count, warm-up behavior, measured metric, threshold/baseline rule, cleanup policy, and remote output path.

## Final Response Shape

After running the pipeline, respond concisely with:

- Local Markdown case path.
- Local automation file path.
- Remote deployed path.
- Execution host and command.
- Result summary: total, passed, failed, blocked, not run, conclusion.
- Local report path and screenshot paths.
- Any blockers or verification gaps.
