---
name: iotdb-sql-testcase-pipeline
description: Use when Codex needs to turn IoTDB/TimechoDB SQL requirements, design docs, issues, or official manual topics into detailed Markdown cases and .run files, or operate 1C1D/3C3D SQL-test environments from provided IoTDB and sql-test directories, including default official manual lookup, tree/table config, rpc_address/iotdbURL sync, special_query.csv result masking, setup/test runs, restarts, artifact collection, reports, or screenshots.
---

# IoTDB SQL Testcase Pipeline

## Overview

Use this skill to run the end-to-end IoTDB/TimechoDB SQL testcase workflow in a reusable way: requirement analysis, detailed Markdown cases, automatic `.run` generation, SQL-test result-column masking, remote deployment, 1C1D/3C3D cluster handling, tree/table model configuration, setup/test execution, artifact pullback, and fixed-format reporting.

Always prefer the current repository's `AGENTS.md` if present. It is the project memory and may override stale details in this skill. Never store SSH passwords, tokens, or private key material in generated files.

When the user provides requirement text, a design document, or issue content without official documentation links, proactively search the official TimechoDB/IoTDB user manual for related behavior, syntax, constraints, and edge cases before generating cases. Treat user-supplied links as optional supplements, not required inputs.

## Required References

- Read `references/pipeline-rules.md` before generating `.run`, touching remote servers, switching models, restarting IoTDB, executing cases, or writing reports.
- Use `assets/test-execution-report-template.md` as the fixed report shape.
- Use `scripts/lint_case_artifacts.py` before deploying generated Markdown/`.run` artifacts when Python is available.
- Automatically use `scripts/suggest_special_query_masks.py` after SQL-test comparison failures to list `.result`/`.out` differing result columns and produce candidate `special_query.csv` rows. Do not wait for the user to ask for this helper.
- Use `scripts/build_execution_report.py` to create a fixed report from execution metrics when the report does not already exist.

## Workflow

1. Collect the requirement text, version directory, target topology (`1C1D` or `3C3D`), target model (`table`, `tree`, or both), optional official documentation links, local case artifact directory, local pullback artifact directory, one cluster access host, SQL-test runner host, SSH key path, remote IoTDB install directory, and SQL-test tool directory. If the user passes the IoTDB directory and SQL-test directory, treat those as the first paths to verify and execute against. For `3C3D`, do not require three host IPs; one reachable cluster node is enough.
2. Search the official manual by default:
   - Tree model: `https://www.timecho.com/docs/zh/UserGuide/latest/`
   - Table model: `https://www.timecho.com/docs/zh/UserGuide/latest-Table/`
   - English fallback: `https://www.timecho-global.com/docs/UserGuide/latest/`
   Use the requirement/design/issue keywords plus the model type. If the model is `both` or unclear, search both tree and table manuals. Record the relevant manual sections in the Markdown `需求来源` field and `.run` source comments.
3. Create or enter the local case artifact directory. If the user does not provide one, create a requirement directory named after the requirement item under the current workspace. Put the Markdown case file, local generated `.run`, wrappers, and `execution-report.md` there. Create or enter the local pullback artifact directory for files copied back from SQL-test; default it to `<local case artifact directory>/artifacts`. When the target model is `both`, split local artifacts into separate `tree/` and `table/` subdirectories and generate separate Markdown, `.run`, pullback artifacts, and reports for each model.
4. Verify the remote directories before generation/deployment:
   - IoTDB directory contains expected `conf/` and `sbin/` files.
   - SQL-test directory contains `test.sh`, `user/CONFIG/otf_new.properties`, `user/scripts/`, and `user/result/`.
   - For `3C3D`, verify the supplied cluster access host and choose the SQL-test runner host explicitly.
5. Generate a detailed Markdown table case file first. Then immediately self-review and lint it. In the normal automatic flow, do not wait for a separate manual review before `.run` generation unless the user asked for "Markdown only" or "review first".
6. Generate the automation artifact that matches the target:
   - `.run` for SQL automation tool flows.
   - Shell/PowerShell wrapper when the tested behavior is a tool command such as `export-data.sh`.
   - For model `both`, generate two `.run` files, one for tree model and one for table model. Do not mix tree and table SQL in one `.run`.
7. Run static checks:
   - Markdown table has the required columns.
   - Every automated case has setup, execution, assertions, cleanup, and stable expected output.
   - Long-running or performance cases are clearly marked.
   - No server password or private key material is written to repo files.
8. Read `conf/iotdb-datanode.properties` and derive the SQL-test JDBC endpoint from `dn_rpc_address` plus fixed port `6667`. If `dn_rpc_address` is edited, update `iotdbURL` in `otf_new.properties` to the same IP before executing.
9. Configure SQL-test for the target model:
   - Table model uses `jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table`.
   - Tree model uses exactly `jdbc:iotdb://<rpc_address>:6667`; remove `?version=...` and any other query parameters.
10. Configure `user/CONFIG/special_query.csv` before setup mode when generated cases contain known volatile result columns such as time, query IDs, elapsed time, region IDs, build info, usage, or other environment-dependent columns. Back up the CSV first, then add `SQL;ColumnName;ColumnName` entries that exactly match the query text used in `.run`.
11. Deploy the executable `.run` to the target SQL-test directory using SSH key authentication or an existing secure runtime configuration. The `.run` that SQL-test executes must be under `<SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run`.
12. Execute the two-phase automation flow when the user asks for full execution:
   - Set SQL-test mode to `setup`, execute, and collect `.result` artifacts.
   - Stop IoTDB on the supplied `1C1D` host or supplied `3C3D` cluster access host.
   - Clean only the verified IoTDB `data/` and `logs/` directories.
   - Restart IoTDB, re-check RPC port `6667`, set SQL-test mode to `test`, execute again, and collect `.out`, `result.xml`, and logs.
   - For model `both`, run this full two-phase flow separately for tree and table: tree `setup`, clean/restart, tree `test`, then reconfigure SQL-test for table, table `setup`, clean/restart, table `test`. This means four SQL-test executions total.
13. If the test run exits nonzero, `result.xml` reports failures, or `.out` contains `###### COMPARE RESULT : FAIL ######`, automatically pair the relevant `.result` and `.out` files and run `scripts/suggest_special_query_masks.py`. State the exact SQL and differing result columns, then ask only for the user's decision: re-run comparison, or append/merge suggested mask columns into `special_query.csv`.
14. Pull back the deployed `.run`, `.result`, `.out`, `result.xml`, logs, wrapper output, `special_query.csv`, and any exported data summaries needed for validation into the local pullback artifact directory.
15. Fill `execution-report.md` using the fixed template. Include only metrics, paths, conclusion, failure rows, notes, and screenshots/evidence images.

## Remote Defaults

When the user does not provide a different environment, use the repository memory if available. Common defaults for this project are:

- SSH user: `ubuntu`
- SSH key env var: `IOTDB_SSH_KEY`
- Fallback key path on this workstation: `C:\Users\tiany\.ssh\sql_testcase_automation_ed25519`
- SQL automation host: user-provided SQL-test runner host.
- Common 1C1D topology: one host running both ConfigNode and DataNode.
- Common 3C3D topology: provide any one reachable cluster node; do not require three IPs.
- Local case artifact directory: user-provided path, or `<current workspace>/<requirement-item>/`.
- Local pullback artifact directory: user-provided path, or `<local case artifact directory>/artifacts/`.
- SQL automation root: `/data/iotdb-sql-test-master`
- Script upload path: `/data/iotdb-sql-test-master/user/scripts/<feature>/<case-name>.run`

Treat these as defaults, not facts. Verify active paths and configs on the remote host before execution.

## Guardrails

- Generate detailed Markdown first, then automatically generate `.run` after static checks pass. If the user asks to skip Markdown, explain that this pipeline requires Markdown as the reviewable source of truth.
- Do not require the user to provide official documentation links. Search the official manuals by default and cite relevant manual sections when they influence coverage or expected results. If network access is unavailable, state that gap in the report or final response.
- Do not overwrite `.result` baselines unless the user explicitly asks for setup/baseline generation or full setup/test execution and the version/environment is intentionally under test.
- Do not delete remote IoTDB `data` or `logs` directories unless the user explicitly asks for the setup/test clean restart flow. Before deletion, resolve the absolute paths and verify they are exactly under the supplied IoTDB install directory.
- Do not hardcode SSH passwords. If key-based SSH is unavailable, ask the user to configure a key or provide an interactive secure method.
- For table model cases, create a database and `use <database>` after connecting; after switching users, run `use <database>` again.
- For tree model cases, do not use `use`; use full paths such as `root.test.d1.s1`.
- For SQL-test config, table and tree model are different. Table mode must use `sql_dialect=table`; tree mode must remove everything after port `6667` from `iotdbURL`.
- For model `both`, generate and execute separate tree and table artifacts. Do not run one mixed `.run`, do not reuse one SQL-test config, and do not let one model's `.result` become the other model's baseline.
- Keep DataNode `dn_rpc_address` and SQL-test `iotdbURL` synchronized. The RPC port is fixed to `6667`; SQL-test should connect to `jdbc:iotdb://<dn_rpc_address>:6667...` for table mode and exactly `jdbc:iotdb://<dn_rpc_address>:6667` for tree mode.
- Use `special_query.csv` for column-level result masking when only some output columns are unstable. Do not replace a deterministic query with `<<CHECKCODE;` just to hide one volatile column.
- When `###### COMPARE RESULT : FAIL ######` appears, automatically compare `.result` and `.out` with `scripts/suggest_special_query_masks.py`; do not ask the user to provide a new prompt for the diff helper. List the exact SQL and real differing result-table columns, then offer two choices: re-run comparison, or append/merge the suggested mask columns into `special_query.csv`. Ignore SQL-test status/footer differences such as `Elapsed Time`; they are not `special_query.csv` columns.
- Update `special_query.csv` before setup mode so `.result` and `.out` are generated with the same masked columns. If masking is discovered after a mismatch, update the CSV and rerun the full setup -> clean/restart -> test sequence.
- For performance cases, include data volume, concurrency or loop count, warm-up behavior, measured metric, threshold/baseline rule, cleanup policy, and remote output path.

## Final Response Shape

After running the pipeline, respond concisely with:

- Local Markdown case path.
- Local automation file path.
- Remote deployed path.
- Local pullback artifact directory.
- Execution host and command.
- Result summary: total, passed, failed, blocked, not run, conclusion.
- Local report path and screenshot paths.
- Any blockers or verification gaps.
