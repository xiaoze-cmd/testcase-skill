# Pipeline Rules

## Inputs

Collect these before execution. If the user already provides the IoTDB install directory and SQL-test tool directory, verify those paths first and execute against them.

| Field | Required | Notes |
|------|----------|-------|
| Requirement item | Yes | Prefer using it as the local requirement directory name. |
| Version | Yes | Example: `2.0.9.2`, `2.0.10.1`, `1.3.7.3`. |
| Topology | Yes | `1C1D` or `3C3D`. |
| Model | Yes | `table`, `tree`, or both. |
| Source docs | Yes | Requirement/design docs or issue text. Official docs URLs are optional because the skill searches official manuals by default. |
| Local case artifact directory | Yes | Stores the generated Markdown cases, local generated `.run`, wrappers, and `execution-report.md`. If omitted, use `<current workspace>/<requirement-item>/`. |
| Local pullback artifact directory | Yes | Stores files pulled back from SQL-test after execution. If omitted, use `<local case artifact directory>/artifacts/`. |
| IoTDB node hosts | Yes | For `1C1D`, one host. For `3C3D`, all three cluster node hosts are required for stop, cleanup, and restart. |
| SQL-test runner host | Yes | May be the same as one IoTDB node host. |
| SSH identity | Yes | Use `IOTDB_SSH_KEY`, per-node local private key paths, or one confirmed shared key. For `3C3D`, SSH must work for all three nodes. Never write passwords. |
| IoTDB install path | Yes | User may pass it directly. Verify `conf/` and `sbin/` before use. |
| SQL-test tool path | Yes | User may pass it directly. Verify `test.sh` and `user/CONFIG/otf_new.properties`. |

If a requested detail can be discovered safely from local files or the remote server, discover it instead of stopping.

## Local Artifact Layout

Keep local generation and remote execution paths separate.

| Path | Contents |
|------|----------|
| Local case artifact directory | Markdown case file, local generated `.run`, wrapper scripts, command inventory, `execution-report.md`, notes. |
| Remote SQL-test script path | The executable `.run` deployed under `<SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run`. SQL-test must run this remote copy. |
| Local pullback artifact directory | Deployed `.run` copied back from SQL-test, `.result`, `.out`, `result.xml`, logs, `special_query.csv`, screenshots, exported-data summaries. |

Rules:

- If the user provides local directories, use those exact directories and create them when missing.
- If the user does not provide local directories, create `<current workspace>/<requirement-item>/` and `<current workspace>/<requirement-item>/artifacts/`.
- If `Model` is `both`, create separate model subdirectories: `<local case artifact directory>/tree/`, `<local case artifact directory>/table/`, `<local pullback artifact directory>/tree/`, and `<local pullback artifact directory>/table/`.
- Do not write generated cases into the skill repository unless the user explicitly chooses that repository as the local case artifact directory.
- Do not treat the local generated `.run` as executed until it has been deployed to SQL-test.
- After execution, pull the remote `.run` back with the result artifacts so the report records the exact script that ran.

## Official Manual Lookup

When the user supplies requirement text, a design document, or issue content, search the official user manual even if the user does not provide a docs URL. Use the manual findings to improve syntax coverage, boundary cases, error expectations, and model-specific differences.

Default manual roots:

| Model | Manual root |
|------|-------------|
| Tree model | `https://www.timecho.com/docs/zh/UserGuide/latest/` |
| Table model | `https://www.timecho.com/docs/zh/UserGuide/latest-Table/` |
| English fallback | `https://www.timecho-global.com/docs/UserGuide/latest/` |

Lookup rules:

- Search with keywords extracted from the requirement/design/issue, including SQL keywords, function names, config keys, error names, and Chinese/English feature names.
- For `table`, search the table-model manual first; for `tree`, search the tree-model manual first.
- For `both` or unclear model type, search both tree and table manuals and separate model-specific behavior in the cases.
- If a version-specific manual can be reached from the docs site and matches the target version, prefer it. Otherwise use the `latest` manual and note the version gap.
- Treat user-supplied official links as supplements. Do not stop just because no official link was provided.
- Record relevant manual section names or URLs in the Markdown `需求来源` column and in `.run` `-- 来源:` comments when they affect the case design.
- If network access or docs search is unavailable, continue from the supplied requirement/design/issue and explicitly note that the official manual lookup could not be completed.

## Topology Rules

### 1C1D

- Use one host that runs both ConfigNode and DataNode.
- Verify the supplied IoTDB directory on that host.
- Start/stop only that host unless the user supplies a separate SQL-test runner.
- Derive the SQL-test JDBC endpoint from that host's DataNode config unless the user passes an explicit RPC endpoint.

### 3C3D

- Require all three cluster node hosts from the user.
- Verify SSH and the supplied IoTDB directory on all three nodes.
- Read `dn_rpc_address` from one selected DataNode config; SQL-test should connect to that single address.
- Use fixed RPC port `6667`.
- Choose one SQL-test runner host explicitly. It may be one of the three IoTDB node hosts.
- Do not assume the SQL-test runner host is the same as `dn_rpc_address`; always follow the config value.
- Stop, clean `data/` and `logs`, and restart IoTDB on all three cluster nodes. Codex can orchestrate these SSH commands from one local session, but the remote operations must cover every node.

## Directory Verification

Use read-only checks before editing or deleting anything.

```bash
test -d "$IOTDB_DIR"
test -d "$IOTDB_DIR/conf"
test -d "$IOTDB_DIR/sbin"
test -f "$IOTDB_DIR/conf/iotdb-datanode.properties" || true
test -f "$IOTDB_DIR/conf/iotdb-confignode.properties" || true
test -f "$SQL_TEST_DIR/test.sh"
test -f "$SQL_TEST_DIR/user/CONFIG/otf_new.properties"
test -d "$SQL_TEST_DIR/user/scripts"
test -d "$SQL_TEST_DIR/user/result"
```

Do not silently fall back to stale remembered paths when the user supplied explicit directories. If a supplied directory is wrong, report the failed check and stop.

For `3C3D`, run the IoTDB directory checks on all three supplied node hosts. Run the SQL-test directory checks on the SQL-test runner host.

## Markdown Case Requirements

Generate Markdown first from the user material plus the official manual lookup. Save it under the local case artifact directory. The normal full pipeline is automatic: create the Markdown table, self-review and lint it, then generate `.run` without waiting for a separate manual review unless the user requested Markdown-only or review-only mode.

Use a Markdown table. The minimum required columns are:

| Column | Requirement |
|------|-------------|
| 用例编号 | Stable ID, for example `TC-SQL-001`. |
| 用例名称 | Exact validation point. |
| 用例级别 | `P0`, `P1`, or `P2`. |
| 模块类型 | Query, auth, function, table model, tree model, cluster, Pipe, tool, performance, etc. |
| 二级分类 | More specific category. |
| 需求来源 | Requirement, design doc, issue, and relevant official manual section or URL. |
| 前置条件 | Topology, cluster state, permissions, config, model type. |
| 测试数据 | Database, table/timeseries, inserted rows, boundary values. |
| 操作步骤 | Expanded setup, data prep, execution, validation, cleanup. |
| 预期结果 | Exact row count, fields, ordering, error keyword, file count, or metric rule. |
| 清理动作 | `drop database`, `drop table`, `drop user`, file cleanup, etc. |
| 备注 | Risk, constraints, version differences. |
| 测试结果 | Fill after execution. |
| 截图 | Fill after execution when needed. |

Coverage should include P0 positive flows, P1 boundaries/combinations/empty data/NULL/permissions, and P2 errors/compatibility/cluster scenarios. Permission cases must include user creation, grant, login/switch user, verification, and cleanup.

Performance cases must not be simplified. Include data scale, generation method, warm-up, measured iterations, metric, threshold/baseline rule, raw output path, and cleanup/retention policy.

## Automation File Rules

Generate `.run` automatically under the local case artifact directory after the Markdown table passes static checks. Deploy the executable copy to the remote SQL-test script path before execution.

`.run` case pattern:

```sql
-- 用例 TC-SQL-001: exact case name
-- 来源: requirement/design/official docs
-- 预期: exact expected behavior
connect root/TimechoDB@2021;

-- setup
drop database test_xxx;
<<NULL;
create database test_xxx;
<<NULL;

-- table model only
use test_xxx;
<<NULL;

-- data preparation
create table ...;
<<NULL;
insert into ...;
<<NULL;

-- test SQL
select ... order by ...;

-- cleanup
drop database test_xxx;
<<NULL;
```

Markers:

| Marker | Meaning |
|------|---------|
| `<<NULL;` | Do not record or compare output. Use for cleanup/setup. |
| `<<SQLSTATE;` | Expected error. Include error keyword in comments. |
| `<<CHECKCODE;` | Check success code only. Use only when result set is unstable by nature. |

Hard requirements:

- Every case cleans up before and after.
- Cases do not share mutable state.
- Object names use a test prefix and are unique enough to avoid pollution.
- Positive queries should have deterministic output, usually with `order by`.
- Table model cases run `use <database>` after connect and after user switch.
- Tree model cases use full paths and avoid `use`.
- Long-running/performance cases are separated from normal regression files.

For command-line tools such as `export-data.sh`, generate an executable wrapper script and a command inventory file. The wrapper should log exact command, start/end time, exit code, output directory, validation counts, and cleanup/retention policy.

## Tree/Table Model Configuration

Tree and table models use different SQL-test and SQL rules.

When `Model` is `both`, split the work into two independent model pipelines. Generate separate Markdown case files, separate `.run` files, separate remote script paths, separate pullback artifact directories, and separate reports or report sections for tree and table. Do not mix tree and table SQL in one `.run`, and do not execute both models with one `otf_new.properties` configuration.

### Table Model

- `otf_new.properties` must connect with table dialect:

```properties
DBtype=IOTDB
iotdbURL=jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table
```

- `.run` should create a database and then run `use <database>;`.
- Table definitions must distinguish `TAG`, `ATTRIBUTE`, and `FIELD`.
- After switching users, run `use <database>;` again before table SQL.

### Tree Model

- Do not keep `sql_dialect=table` in `iotdbURL`.
- Remove everything after the port. Tree-model SQL-test URLs must not contain `?version=...` or any other query parameters.

```properties
DBtype=IOTDB
iotdbURL=jdbc:iotdb://<rpc_address>:6667
```

- `.run` must not use `use <database>;`.
- Use full paths such as `root.test.d1.s1`.
- `create database` must not use table-model assumptions.

### Both Models

For requirements that are common to both tree and table models:

- Generate `tree/<case-name>-tree-cases.md` and `tree/<case-name>-tree.run`.
- Generate `table/<case-name>-table-cases.md` and `table/<case-name>-table.run`.
- Deploy the tree `.run` and table `.run` to distinct SQL-test script paths, for example:

```text
<SQL_TEST_DIR>/user/scripts/<feature>/tree/<case-name>-tree.run
<SQL_TEST_DIR>/user/scripts/<feature>/table/<case-name>-table.run
```

- Configure SQL-test as tree model only while executing the tree `.run`.
- Configure SQL-test as table model only while executing the table `.run`.
- Run full isolation per model: setup, stop IoTDB, clean verified `data/` and `logs/`, restart, test.
- Execute SQL-test four times total: tree setup, tree test, table setup, table test.
- Keep `.result`, `.out`, `result.xml`, logs, and `special_query.csv` pullbacks separated by model.
- If tree and table expected behavior differs, document the difference in each model's Markdown `预期结果` and `.run` source comments.

## RPC Address And SQL-test URL Sync

Before running SQL-test, inspect DataNode RPC config:

```bash
grep -E '^dn_rpc_address=' "$IOTDB_DIR/conf/iotdb-datanode.properties"
```

Rules:

- `dn_rpc_address` is the IP SQL-test should connect to unless the user passes a different reachable RPC endpoint.
- The RPC port is fixed as `6667`; do not ask the user to provide a port.
- If you edit `dn_rpc_address`, update `iotdbURL` in `otf_new.properties` to the same IP.
- Ensure table-model `iotdbURL` is `jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table`.
- Ensure tree-model `iotdbURL` is exactly `jdbc:iotdb://<rpc_address>:6667`.
- Do not preserve `?version=...` for tree model.

Example: if DataNode config contains:

```properties
dn_rpc_address=<rpc_address>
```

Then table-model SQL-test config should use:

```properties
iotdbURL=jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table
```

For `3C3D`, require all three node hosts for lifecycle operations. The SQL-test runner may be one host while `iotdbURL` points to the single `dn_rpc_address` value read from the selected cluster node config.

Back up config files before editing:

```bash
cp "$IOTDB_DIR/conf/iotdb-datanode.properties" "$IOTDB_DIR/conf/iotdb-datanode.properties.bak.$(date +%Y%m%d%H%M%S)"
cp "$SQL_TEST_DIR/user/CONFIG/otf_new.properties" "$SQL_TEST_DIR/user/CONFIG/otf_new.properties.bak.$(date +%Y%m%d%H%M%S)"
```

## Remote Deployment

Use SSH/SCP with key authentication. Example shape on Windows:

```powershell
$key = $env:IOTDB_SSH_KEY
if (-not $key) { $key = "C:\Users\tiany\.ssh\sql_testcase_automation_ed25519" }
ssh -i $key ubuntu@<host> "hostname && date"
scp -i $key local.run ubuntu@<host>:/tmp/local.run
```

Before deployment:

1. Confirm remote host and user.
2. Confirm SQL-test root exists.
3. Confirm target upload directory.
4. Confirm `user/CONFIG/otf_new.properties` and current model/dialect settings.
5. Back up any config file before editing it.

Upload convention:

```text
<SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run
```

After deployment, record both paths:

```text
local generated .run: <local case artifact directory>/<case-name>.run
remote executed .run: <SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run
```

## Cluster Start/Stop

Always perform read-only checks first:

```bash
ps -ef | grep -E 'ConfigNode|DataNode' | grep -v grep
ss -ltnp | grep 6667 || true
```

Common node-level start sequence when no cluster `start-all.sh` exists:

```bash
cd "$IOTDB_DIR"
sudo -n ./sbin/start-confignode.sh
sudo -n ./sbin/start-datanode.sh
```

Common stop sequence:

```bash
cd "$IOTDB_DIR"
sudo -n ./sbin/stop-confignode.sh
sudo -n ./sbin/stop-datanode.sh
```

For `1C1D`, run start/stop on the single IoTDB host. For `3C3D`, run start/stop on all three supplied cluster nodes and keep node-specific logs. If `sudo -n` fails on any node, do not embed passwords. Report that passwordless sudo or an interactive secure method is required for that node.

## Setup/Test Execution Sequence

For full automated execution, use the two-phase sequence below to avoid dirty data causing `.result` and `.out` differences.

If `Model` is `both`, run the full sequence once for tree and once for table, with SQL-test configuration switched between models. Do not skip the clean restart between the tree setup/test pair or the table setup/test pair.

1. Generate Markdown cases.
2. Generate `.run` automatically from the checked Markdown.
3. Lint Markdown and `.run`.
4. Deploy `.run` to `<SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run`.
5. Configure `otf_new.properties` for topology, model, and synchronized `iotdbURL`.
6. Configure `user/CONFIG/special_query.csv` if any query has volatile columns that should be ignored in `.result`/`.out` comparison.
7. Set SQL-test execution mode to `setup`. The exact property key must be verified in `otf_new.properties` or `test.sh`; commonly it is a setup/test mode flag.
8. Run:

```bash
cd "$SQL_TEST_DIR"
./test.sh
```

9. Collect generated `.result` files and setup logs.
10. Stop IoTDB on the supplied `1C1D` host, or on all three supplied `3C3D` cluster nodes.
11. Resolve and verify cleanup paths before deletion:

```bash
cd "$IOTDB_DIR"
pwd
test -d "$IOTDB_DIR/data" && test -d "$IOTDB_DIR/logs"
```

12. Delete only the verified IoTDB data/log directories:

```bash
rm -rf "$IOTDB_DIR/data" "$IOTDB_DIR/logs"
```

13. Restart IoTDB on the supplied `1C1D` host, or on all three supplied `3C3D` cluster nodes.
14. Re-check processes on every restarted node and RPC port `6667` on the SQL-test connection node.
15. Set SQL-test execution mode to `test`.
16. Run `./test.sh` again.
17. Pull back the remote executed `.run`, `.out`, `result.xml`, test logs, `special_query.csv`, and any updated `.result` references needed for diagnosis into the local pullback artifact directory. For `both`, use the model-specific pullback directory.
18. If the test command exits nonzero, `result.xml` reports failures, or any `.out` contains `###### COMPARE RESULT : FAIL ######`, automatically run the result masking analysis described below. Do not ask the user to trigger the diff script with another prompt.
19. Compare case counts and failures before reporting.

Do not skip the restart and cleanup between setup and test unless the user explicitly requests a faster non-isolated run.

## Result Column Masking

SQL-test uses `user/CONFIG/special_query.csv` to hide selected result columns before writing or comparing `.result` and `.out`. Use it when the query result is meaningful but one or more columns are expected to differ between setup and test runs, such as time, query ID, elapsed time, DataNode ID, region creation time, build info, usage, estimated remaining seconds, or environment-specific internal addresses.

Format:

```csv
sql;column_name;column_name
```

Examples:

```csv
show queries;query_id;start_time;datanode_id;elapsed_time;wait_time_in_server;
show regions;RegionId;CreateTime;TsFileSize;CompressionRatio;InternalAddress;
select * from root.**;Time;
```

Rules observed from the SQL-test implementation:

- The file path is `<SQL_TEST_DIR>/user/CONFIG/special_query.csv`.
- The first field is the SQL text. It must exactly match the `.run` query text after trimming, ignoring case.
- Do not include the SQL terminator semicolon as part of the SQL field. The semicolon is the CSV delimiter.
- Fields after the SQL are column names to mask. Column name matching is case-insensitive.
- Multiple columns are separated by English semicolons.
- A trailing semicolon is allowed.
- If the SQL does not match or a column name is wrong, the mask silently has no effect.
- Back up `special_query.csv` before editing.
- Update this file before setup mode. If a mismatch is found after test mode because a volatile column was not masked, update `special_query.csv`, clear generated artifacts for that case, and rerun setup -> clean/restart -> test.
- Prefer `special_query.csv` for column-level masking. Use `<<CHECKCODE;` only when the whole query result is inherently unstable or not useful for comparison.
- Do not add SQL-test footer/status lines such as `Elapsed Time` or `###### COMPARE RESULT : FAIL ######` to `special_query.csv`. They are tool output, not query result columns.
- A query result column named `elapsed_time` may be a valid mask candidate for statements such as `show queries`; the footer line `Elapsed Time: ...` is not.

When SQL-test reports `###### COMPARE RESULT : FAIL ######`, automatically analyze the actual `.result` and `.out` differences before editing the CSV. This is part of the execution flow; the user should not need to provide a second prompt just to run the helper.

```bash
python scripts/suggest_special_query_masks.py --result path/to/case.result --out path/to/case.out
```

Pair files by case basename from the generated artifacts. If multiple cases fail, run the helper for each result/out pair and summarize each failing SQL separately. If a pair is missing, report the missing artifact instead of skipping the analysis silently.

The script lists differing result-table columns and suggests `special_query.csv` rows only for known volatile columns by default. It ignores tool footer/status lines such as `Elapsed Time`. If a difference is in a business column, inspect it manually instead of masking it.

After suggesting mask columns, state the exact SQL and differing columns, then stop for only this decision:

1. Re-run comparison after another test execution if the difference may be caused by environment noise.
2. Append/merge the suggested mask columns into `special_query.csv`.

Only append after the user chooses that option. Back up `special_query.csv` first, then use:

```bash
python scripts/suggest_special_query_masks.py --result path/to/case.result --out path/to/case.out --special-query "$SQL_TEST_DIR/user/CONFIG/special_query.csv" --append
```

After appending mask columns, rerun the isolated setup -> clean/restart -> test sequence so `.result` and `.out` are generated with the same mask rules.

## Artifact Collection

Do not claim all cases passed unless:

- The remote command completed.
- Exit code and tool output were checked.
- Result files/logs were pulled back or inspected.
- Case counts reconcile with the generated case list.

Pull back these artifacts when present:

```text
*.run
*.result
*.out
result.xml
special_query.csv
*.log
wrapper stdout/stderr
export directories or validation summaries
```

## Fixed Report

Create `execution-report.md` in the local case artifact directory. Use `assets/test-execution-report-template.md` or `scripts/build_execution_report.py`.

Reports must stay short. Fill only:

- Requirement, version, execution date, topology, model, execution environment.
- IoTDB directory, SQL-test directory, executed script, remote command, log paths, artifact paths.
- Total, passed, failed, blocked, not run, pass rate, conclusion.
- Failure detail rows, or `无`.
- Screenshot/evidence image paths.
- Necessary notes such as setup/test mode, data/log cleanup, baseline source, and version differences.
- Mention any `special_query.csv` masking entries added for this run.

If screenshots are requested, create or attach at least:

```text
report-screenshot-01-execution.png
report-screenshot-02-artifacts.png
report-screenshot-03-validation.png
```

Screenshots can be terminal captures, rendered report captures, UI captures, or evidence images generated from logs/metrics, but they must correspond to real execution evidence.
