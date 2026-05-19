---
name: iotdb-sql-testcase-pipeline
description: Use when Codex needs to turn IoTDB/TimechoDB SQL requirements, design docs, issues, or official manual topics into detailed Markdown cases and .run files, or operate 1C1D/3C3D SQL-test/benchmark environments from provided IoTDB, sql-test, and benchmark directories, including large-data writes, setup/test runs, tree/table config, result masking, artifacts, reports, or screenshots.
---

# IoTDB SQL Testcase Pipeline

## Overview

Use this skill to run the end-to-end IoTDB/TimechoDB SQL testcase workflow in a reusable way: requirement analysis, detailed Markdown cases, automatic `.run` generation, SQL-test result-column masking, remote deployment, 1C1D/3C3D cluster handling, tree/table model configuration, setup/test execution, artifact pullback, and fixed-format reporting.

Always prefer the current repository's `AGENTS.md` if present. It is the project memory and may override stale details in this skill. Never store SSH passwords, tokens, or private key material in generated files.

When the user provides requirement text, a design document, or issue content without official documentation links, proactively search the official TimechoDB/IoTDB user manual for related behavior, syntax, constraints, and edge cases before generating cases. Treat user-supplied links as optional supplements, not required inputs.

## User-Facing Language

Use Simplified Chinese for all user-facing text during this skill workflow: progress updates, operation steps, execution status, failure analysis, confirmation choices, final summaries, Markdown case prose, `.run` Chinese comments, and `execution-report.md`.

Keep commands, file paths, SQL statements, configuration keys, log excerpts, error codes, filenames, and tool-fixed output in their original form. When summarizing English logs or tool output, explain the meaning in Chinese instead of leaving the surrounding operation/result narrative in English.

## Required References

- Read `references/pipeline-rules.md` before generating `.run`, touching remote servers, switching models, restarting IoTDB, executing cases, or writing reports.
- Use `assets/test-execution-report-template.md` as the fixed report shape.
- Use `scripts/lint_case_artifacts.py` before deploying generated Markdown/`.run` artifacts when Python is available.
- Automatically use `scripts/suggest_special_query_masks.py` after SQL-test comparison failures to list `.result`/`.out` differing result columns and produce candidate `special_query.csv` rows. Do not wait for the user to ask for this helper.
- Use `scripts/build_execution_report.py` to create a fixed report from execution metrics when the report does not already exist.

## Test Design Gate

Before generating Markdown cases, perform a real test-design analysis. This is a hard gate: do not jump from requirement text directly to case rows.

1. Decompose the requirement into an atomic `测试点矩阵` first. Include at least: `测试点编号`, `功能/规则`, `影响面`, `正向场景`, `反向/异常场景`, `边界/组合场景`, `权限/配置/模型/集群差异`, `测试数据`, `验证方式`, `稳定性与预期`, and `自动化备注`.
2. Atomic means one observable rule per row. Do not use broad rows such as "权限控制", "Pipe 同步", "配置校验", "性能测试", or "元数据展示" if they contain multiple roles, operations, syntax variants, config values, model differences, or source/target states. Split them until each row can be proven by a concrete action and assertion.
3. Analyze behavior, not just wording. Identify what changed in SQL syntax, DDL, DML, query path, data reads/writes, metadata, system tables, permissions, configuration, restart/reload behavior, cluster behavior, Pipe/sync, performance, compatibility, and failure handling.
4. Apply the generic coverage checklist to every requirement unless it is clearly irrelevant: syntax variants, positive data path, negative/error path, boundary values, NULL/empty data, default vs explicit values, permission grants/denials, config on/off or old/new value, tree/table model difference, single-node/cluster difference, source/target side behavior, compatibility with old syntax, performance/large-data impact, audit/log/error message behavior, and cleanup.
5. For every functional claim, ask what observable action proves it. If the feature is about write, delete, update, query, sync, permissions, configuration, restart, performance, or tools, the case must execute that action and verify the real outcome. `SHOW`, `DESC`, and system-table queries prove metadata only; they cannot substitute for data-path validation.
6. Design paired coverage where meaningful: success/failure, enabled/disabled, with/without permission, valid/invalid input, existing/missing object, default/explicit config, single-node/cluster, source/target side, old/new syntax, and normal/boundary/extreme data.
7. Preserve detail when mapping test points to cases. Do not collapse multiple detailed test points into one vague case. A generated case should normally map to one primary test point; if it maps to multiple IDs, it must contain separate setup, action, assertion, and expected result for each sub-point.
8. Permission-related requirements must be expanded as a matrix: role/user type, privilege scope such as object/database/ANY, operation type such as CREATE/DROP/ALTER/SELECT/INSERT/DELETE, enabled/disabled security mode when relevant, grant path, user switch/login, positive attempt, negative attempt, and cleanup.
9. Sync, Pipe, cluster, benchmark, audit, and performance points must not be silently downgraded to "后续专项" or "人工验证". If they cannot be automated in SQL-test, still generate explicit design cases with required environment, trigger action, evidence, and blocking reason. If they can be automated by wrapper/remote commands/benchmark, generate those artifacts instead of dropping the coverage.
10. Prefer stable assertions. Use exact rows, counts, metadata fields, object existence, SQLSTATE, error code, or stable keywords. Do not depend on complete localized error text when wording may switch between English and Chinese.
11. After generating the matrix but before generating case rows, run a coverage self-review and state gaps: untested requirement rules, metadata-only proof where data-path proof is required, missing negative cases, missing permission/config/model/cluster differences, non-automated cases, and assumptions.
12. List open questions and assumptions before case generation. If ambiguity affects correctness, either ask the user or generate cases under explicit conservative assumptions.

## Case Expansion Gate

After the atomic test-point matrix is created, expand test points into executable case scenarios before writing the final Markdown case table. This is a second hard gate: do not mechanically generate one case per test point.

1. Treat `测试点` and `用例` as different layers. A test point is a rule or behavior to verify; a case is one concrete setup/action/assertion/cleanup path.
2. Create a `测试点展开表` before the final case table. Include at least: `测试点编号`, `子场景编号`, `子场景类型`, `子场景说明`, `生成用例编号`, `是否自动化`, and `展开依据`.
3. One test point may map to one case only when it contains exactly one positive or negative action, one data set, one assertion, no syntax variants, no permission/config/model/topology differences, and no boundary or paired scenario.
4. If a test point contains any expansion trigger, split it into multiple cases. Common triggers include: `分别`, `任一`, `多种`, `多类`, `多个`, `同时`, `两种`, `三种`, `四类`, `对象级/DB级/ANY`, `true/false`, `开启/关闭`, `旧值/新值`, `源端/接收端`, `发送端/接收端`, `DROP VIEW/DROP TABLE`, `ALTER TABLE/ALTER VIEW`, `冷/热`, `单行/批量/并发`, `缺任一权限`, `pattern/privilege`, `skipIfNoPrivileges`, `源表/视图`, or `正向/反向`.
5. Permission test points must expand by operation, privilege scope, role/user type, security mode, granted/denied state, and cleanup. For example, one permission point that mentions `CREATE/DROP/ALTER/SELECT/INSERT/DELETE` cannot become one case.
6. Config and schema-switch test points must expand by each switch value and transition path, such as true->false, false->true, default value, explicit value, valid value, and invalid value.
7. DDL syntax test points must expand by syntax entry and existence state, such as `DROP VIEW`, `DROP TABLE`, `IF EXISTS`, missing object, existing object, `ALTER VIEW`, and `ALTER TABLE`.
8. Sync/Pipe/cluster test points must expand by source state, target state, pattern, privilege, cascade setting, object existence, and failure mode. If the current environment cannot execute them, still create separate design cases with the blocking reason and required evidence.
9. Performance or large-data test points must expand by workload shape, such as query type, cold/hot run, single/batch/concurrent write, data scale, metric, threshold, benchmark config, and evidence path.
10. The coverage self-review must report: total test points, expanded sub-scenarios, total cases, complex test points that expanded to more than one case, and any test point that remained one-to-one with a reason.

## Workflow

1. Collect the requirement text, version directory, target topology (`1C1D` or `3C3D`), target model (`table`, `tree`, or both), optional official documentation links, local case artifact directory, local pullback artifact directory, IoTDB node hosts, SQL-test runner host, SSH user/key for each node or one confirmed shared key, remote IoTDB install directory, SQL-test tool directory, and benchmark tool directory when large-volume data generation is needed. If the user does not specify a benchmark runner host, use the SQL-test runner host. If the user passes the IoTDB, SQL-test, or benchmark directory, treat those as the first paths to verify and execute against. For `3C3D`, require all three cluster node hosts so stop, cleanup, and restart can run on every node.
2. Search the official manual by default:
   - Tree model: `https://www.timecho.com/docs/zh/UserGuide/latest/`
   - Table model: `https://www.timecho.com/docs/zh/UserGuide/latest-Table/`
   - English fallback: `https://www.timecho-global.com/docs/UserGuide/latest/`
   Use the requirement/design/issue keywords plus the model type. If the model is `both` or unclear, search both tree and table manuals. Record the relevant manual sections in the Markdown `需求来源` field and `.run` source comments.
3. Create or enter the local case artifact directory. If the user does not provide one, create a requirement directory named after the requirement item under the current workspace. Put the Markdown case file, local generated `.run`, wrappers, and `execution-report.md` there. Create or enter the local pullback artifact directory for files copied back from SQL-test; default it to `<local case artifact directory>/artifacts`. When the target model is `both`, split local artifacts into separate `tree/` and `table/` subdirectories and generate separate Markdown, `.run`, pullback artifacts, and reports for each model.
4. Verify the remote directories before generation/deployment:
   - IoTDB directory contains expected `conf/` and `sbin/` files.
   - SQL-test directory contains `test.sh`, `user/CONFIG/otf_new.properties`, `user/scripts/`, and `user/result/`.
   - For `3C3D`, verify SSH and the supplied IoTDB directory on all three cluster nodes, and choose the SQL-test runner host explicitly.
5. Generate the atomic `测试点矩阵` first, self-review it for missing positive/negative/boundary/permission/config/model/cluster/sync/performance coverage, then generate the `测试点展开表`, and only then generate the detailed Markdown table case file from the expanded scenarios. In the normal automatic flow, do not wait for a separate manual review before `.run` generation unless the user asked for "Markdown only" or "review first".
6. Generate the automation artifact that matches the target:
   - `.run` for SQL automation tool flows.
   - Shell/PowerShell wrapper when the tested behavior is a tool command such as `export-data.sh`.
   - For model `both`, generate two `.run` files, one for tree model and one for table model. Do not mix tree and table SQL in one `.run`.
7. Run static checks:
   - Markdown table has the required columns.
   - Every case maps to one or more test-point matrix IDs.
   - The matrix is not over-compressed: broad categories are split into independently verifiable rows, and one case does not hide many unrelated test points.
   - Complex test points are expanded into multiple sub-scenarios and multiple cases; one-to-one TP->TC mapping is accepted only with a written reason.
   - Every automated case has setup, execution, assertions, cleanup, and stable expected output.
   - Case title, permissions, SQL actions, and expected result are consistent. For example, a case named for `INSERT/DELETE/SELECT` permissions must grant those permissions and execute those SQL actions; do not replace them with unrelated `DROP` or metadata-only operations.
   - Positive data-behavior cases include direct data validation. For data write/delete/query/sync behavior, verify both the operated object and the affected object when they differ.
   - Metadata-only cases are explicitly labeled as metadata validation and are not used as proof of data behavior.
   - Permission, config, sync/Pipe, cluster, performance, and tool cases are either automated or explicitly marked with a concrete blocking reason and evidence plan.
   - Long-running or performance cases are clearly marked.
   - No server password or private key material is written to repo files.
8. Read `conf/iotdb-datanode.properties` and derive the SQL-test JDBC endpoint from `dn_rpc_address` plus fixed port `6667`. If `dn_rpc_address` is edited, update `iotdbURL` in `otf_new.properties` to the same IP before executing.
9. Configure SQL-test for the target model:
   - Table model uses `jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table`.
   - Tree model uses exactly `jdbc:iotdb://<rpc_address>:6667`; remove `?version=...` and any other query parameters.
10. Configure `user/CONFIG/special_query.csv` before setup mode when generated cases contain known volatile result columns such as time, query IDs, elapsed time, region IDs, build info, usage, or other environment-dependent columns. Back up the CSV first, then add `SQL;ColumnName;ColumnName` entries that exactly match the query text used in `.run`.
11. For large data setup, use benchmark instead of expanding `.run` with massive `INSERT` statements. Verify the benchmark directory, create a run-specific copied config directory, update benchmark `config.properties` for topology/model/RPC/data scale/table prefix, start or verify IoTDB first, run benchmark, then verify the inserted row count through SQL-test or the IoTDB CLI before continuing.
12. Deploy the executable `.run` to the target SQL-test directory using SSH key authentication or an existing secure runtime configuration. The `.run` that SQL-test executes must be under `<SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run`.
13. Execute the two-phase automation flow when the user asks for full execution:
   - Set SQL-test mode to `setup`, execute, and collect `.result` artifacts.
   - Stop IoTDB on the supplied `1C1D` host, or on all three supplied `3C3D` cluster nodes.
   - Clean only the verified IoTDB `data/` and `logs/` directories on each node being restarted.
   - Restart IoTDB, re-check RPC port `6667` on the SQL-test connection node, set SQL-test mode to `test`, execute again, and collect `.out`, `result.xml`, and logs.
   - For model `both`, run this full two-phase flow separately for tree and table: tree `setup`, clean/restart, tree `test`, then reconfigure SQL-test for table, table `setup`, clean/restart, table `test`. This means four SQL-test executions total.
14. If the test run exits nonzero, `result.xml` reports failures, or `.out` contains `###### COMPARE RESULT : FAIL ######`, automatically pair the relevant `.result` and `.out` files and run `scripts/suggest_special_query_masks.py`. State the exact SQL and differing result columns, then ask only for the user's decision: re-run comparison, or append/merge suggested mask columns into `special_query.csv`.
15. Pull back the deployed `.run`, `.result`, `.out`, `result.xml`, benchmark run config, benchmark logs/results, SQL-test logs, wrapper output, `special_query.csv`, and any exported data summaries needed for validation into the local pullback artifact directory.
16. Fill `execution-report.md` using the fixed template. Include only metrics, paths, conclusion, failure rows, notes, and screenshots/evidence images.

## Remote Defaults

When the user does not provide a different environment, use the repository memory if available. Common defaults for this project are:

- SSH user: `ubuntu`
- SSH key env var: `IOTDB_SSH_KEY`
- Fallback key path on this workstation: `C:\Users\tiany\.ssh\sql_testcase_automation_ed25519`
- SQL automation host: user-provided SQL-test runner host.
- Common 1C1D topology: one host running both ConfigNode and DataNode.
- Common 3C3D topology: provide all three cluster node hosts for stop/clean/start. SQL-test still connects to one `dn_rpc_address:6667` read from the selected DataNode config.
- Local case artifact directory: user-provided path, or `<current workspace>/<requirement-item>/`.
- Local pullback artifact directory: user-provided path, or `<local case artifact directory>/artifacts/`.
- SQL automation root: `/data/iotdb-sql-test-master`
- Script upload path: `/data/iotdb-sql-test-master/user/scripts/<feature>/<case-name>.run`
- Benchmark candidate roots: `/data/iot-benchmark-iotdb-2.0`, `/data/iot-benchmark-2.0/iot-benchmark-iotdb-2.0`, `/data/iot-benchmark-v2/iot-benchmark-iotdb-2.0`

Treat these as defaults, not facts. Verify active paths and configs on the remote host before execution.

## Guardrails

- Do not generate detailed cases directly from a requirement summary. First produce and review a test-point matrix; if the matrix is missing, stop and create it.
- Do not generate a feature-specific shortcut skill or one-off rule set. This skill must handle arbitrary IoTDB/TimechoDB SQL requirements with the generic test-design framework; use examples only to sharpen universal rules.
- Do not let the test-point matrix become a high-level outline. Split each requirement into independently verifiable rules before generating cases, especially for permissions, config switches, model differences, sync/Pipe, cluster behavior, large data, and error handling.
- Do not mechanically generate one case for one test point. After the matrix, expand every test point into sub-scenarios and cases; one-to-one TP->TC mapping is valid only for a truly single-action, single-assertion point with no variants.
- Generate detailed Markdown first, then automatically generate `.run` after static checks pass. If the user asks to skip Markdown, explain that this pipeline requires Markdown as the reviewable source of truth.
- Do not treat "the requirement sentence is mentioned" as coverage. A case covers a point only when its SQL/action, data, assertion, and expected result directly prove that point.
- Do not use `SHOW`, `DESC`, or `information_schema` checks to prove data-path behavior. Use them for metadata behavior only, and add direct DML/query/sync validation when the requirement changes data behavior.
- Do not let case names drift from implementation. If a title says write, delete, query, sync, permission, config, or performance, the steps must execute that behavior and verify its result.
- Do not mark broad areas as "后续专项", "人工验证", or "本轮不纳入" unless the generated artifact states the blocking reason, required environment, planned trigger action, expected evidence, and whether a wrapper/benchmark/remote command can automate it.
- Do not accept a generated Markdown table that omits `用例名称`, `一级分类`, `二级分类`, `操作数据`, `清理动作`, `测试结果`, or `截图`. The detailed Markdown table is the source of truth for `.run` generation.
- Do not require the user to provide official documentation links. Search the official manuals by default and cite relevant manual sections when they influence coverage or expected results. If network access is unavailable, state that gap in the report or final response.
- Do not overwrite `.result` baselines unless the user explicitly asks for setup/baseline generation or full setup/test execution and the version/environment is intentionally under test.
- Do not delete remote IoTDB `data` or `logs` directories unless the user explicitly asks for the setup/test clean restart flow. Before deletion, resolve the absolute paths and verify they are exactly under the supplied IoTDB install directory.
- For `3C3D`, lifecycle operations are cluster-wide: verify SSH to all three nodes, stop IoTDB on all three, delete only each node's verified `data/` and `logs/`, and restart all three. Do not clean/restart just one node.
- Do not hardcode SSH passwords. If key-based SSH is unavailable, ask the user to configure a key or provide an interactive secure method.
- For table model cases, create a database and `use <database>` after connecting; after switching users, run `use <database>` again.
- For tree model cases, do not use `use`; use full paths such as `root.test.d1.s1`.
- For SQL-test config, table and tree model are different. Table mode must use `sql_dialect=table`; tree mode must remove everything after port `6667` from `iotdbURL`.
- For model `both`, generate and execute separate tree and table artifacts. Do not run one mixed `.run`, do not reuse one SQL-test config, and do not let one model's `.result` become the other model's baseline.
- Keep DataNode `dn_rpc_address` and SQL-test `iotdbURL` synchronized. The RPC port is fixed to `6667`; SQL-test should connect to `jdbc:iotdb://<dn_rpc_address>:6667...` for table mode and exactly `jdbc:iotdb://<dn_rpc_address>:6667` for tree mode.
- Use `special_query.csv` for column-level result masking when only some output columns are unstable. Do not replace a deterministic query with `<<CHECKCODE;` just to hide one volatile column.
- For large-data setup, use benchmark to write data and keep `.run` focused on DDL, query assertions, and validation. Do not generate hundreds of thousands or millions of literal `INSERT` rows in `.run`.
- When `###### COMPARE RESULT : FAIL ######` appears, automatically compare `.result` and `.out` with `scripts/suggest_special_query_masks.py`; do not ask the user to provide a new prompt for the diff helper. List the exact SQL and real differing result-table columns, then offer two choices: re-run comparison, or append/merge the suggested mask columns into `special_query.csv`. Ignore SQL-test status/footer differences such as `Elapsed Time`; they are not `special_query.csv` columns.
- Update `special_query.csv` before setup mode so `.result` and `.out` are generated with the same masked columns. If masking is discovered after a mismatch, update the CSV and rerun the full setup -> clean/restart -> test sequence.
- For performance cases, include data volume, concurrency or loop count, warm-up behavior, measured metric, threshold/baseline rule, cleanup policy, and remote output path.

## Final Response Shape

After running the pipeline, respond concisely in Chinese with:

- 本地 Markdown 用例路径。
- 本地自动化文件路径。
- 远端部署路径。
- 本地拉回产物目录。
- 执行主机和命令。
- 结果汇总：总数、通过、失败、阻塞、未执行、结论。
- 本地报告路径和截图路径。
- 阻塞项或验证缺口。
