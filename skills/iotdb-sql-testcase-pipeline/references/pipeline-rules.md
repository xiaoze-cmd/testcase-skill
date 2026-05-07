# Pipeline Rules

## Inputs

Collect these before execution. If the user already provides the IoTDB install directory and SQL-test tool directory, verify those paths first and execute against them.

| Field | Required | Notes |
|------|----------|-------|
| Requirement item | Yes | Prefer using it as the local requirement directory name. |
| Version | Yes | Example: `2.0.9.2`, `2.0.10.1`, `1.3.7.3`. |
| Topology | Yes | `1C1D` or `3C3D`. |
| Model | Yes | `table`, `tree`, or both. |
| Source docs | Yes | Requirement/design docs, official docs URLs, or issue text. |
| Cluster access host | Yes | One host is enough for both `1C1D` and `3C3D`; for `3C3D`, use any reachable cluster node. |
| SQL-test runner host | Yes | May be the same as the cluster access host. |
| SSH identity | Yes | Use `IOTDB_SSH_KEY` or a local private key path; never write passwords. |
| IoTDB install path | Yes | User may pass it directly. Verify `conf/` and `sbin/` before use. |
| SQL-test tool path | Yes | User may pass it directly. Verify `test.sh` and `user/CONFIG/otf_new.properties`. |

If a requested detail can be discovered safely from local files or the remote server, discover it instead of stopping.

## Topology Rules

### 1C1D

- Use one host that runs both ConfigNode and DataNode.
- Verify the supplied IoTDB directory on that host.
- Start/stop only that host unless the user supplies a separate SQL-test runner.
- Derive the SQL-test JDBC endpoint from that host's DataNode config unless the user passes an explicit RPC endpoint.

### 3C3D

- Do not require three host IPs from the user. One reachable cluster node IP is enough.
- Verify the supplied IoTDB directory on that cluster node.
- Read that node's `dn_rpc_address` from `conf/iotdb-datanode.properties`; SQL-test should connect to that address.
- Use fixed RPC port `6667`.
- Choose one SQL-test runner host explicitly. It may be the same as the cluster access host.
- Do not assume the SQL-test runner host is the same as `dn_rpc_address`; always follow the config value.

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

## Markdown Case Requirements

Generate Markdown first. The normal full pipeline is automatic: create the Markdown table, self-review and lint it, then generate `.run` without waiting for a separate manual review unless the user requested Markdown-only or review-only mode.

Use a Markdown table. The minimum required columns are:

| Column | Requirement |
|------|-------------|
| 用例编号 | Stable ID, for example `TC-SQL-001`. |
| 用例名称 | Exact validation point. |
| 用例级别 | `P0`, `P1`, or `P2`. |
| 模块类型 | Query, auth, function, table model, tree model, cluster, Pipe, tool, performance, etc. |
| 二级分类 | More specific category. |
| 需求来源 | Requirement, design doc, official docs section, or issue. |
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

Generate `.run` automatically after the Markdown table passes static checks.

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

For `3C3D`, do not require three node IPs. The SQL-test runner may be one host while `iotdbURL` points to the `dn_rpc_address` value read from the cluster node config.

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

For `1C1D`, run start/stop on the single IoTDB host. For `3C3D`, run start/stop on the supplied cluster access host; do not demand three host IPs. If `sudo -n` fails, do not embed passwords. Report that passwordless sudo or an interactive secure method is required.

## Setup/Test Execution Sequence

For full automated execution, use the two-phase sequence below to avoid dirty data causing `.result` and `.out` differences.

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
10. Stop IoTDB on the supplied `1C1D` host or supplied `3C3D` cluster access host.
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

13. Restart IoTDB on the supplied `1C1D` host or supplied `3C3D` cluster access host.
14. Re-check process and RPC port `6667`.
15. Set SQL-test execution mode to `test`.
16. Run `./test.sh` again.
17. Pull back `.out`, `result.xml`, test logs, `special_query.csv`, and any updated `.result` references needed for diagnosis.
18. Compare case counts and failures before reporting.

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

When SQL-test reports `###### COMPARE RESULT : FAIL ######`, analyze the actual `.result` and `.out` differences before editing the CSV:

```bash
python scripts/suggest_special_query_masks.py --result path/to/case.result --out path/to/case.out
```

The script lists differing result-table columns and suggests `special_query.csv` rows only for known volatile columns by default. It ignores tool footer/status lines such as `Elapsed Time`. If a difference is in a business column, inspect it manually instead of masking it.

After suggesting mask columns, state the exact SQL and differing columns, then offer two choices:

1. Re-run comparison after another test execution if the difference may be caused by environment noise.
2. Append/merge the suggested mask columns into `special_query.csv`.

Only append after the user chooses that option. Use:

```bash
python scripts/suggest_special_query_masks.py --result path/to/case.result --out path/to/case.out --special-query "$SQL_TEST_DIR/user/CONFIG/special_query.csv" --append
```

## Artifact Collection

Do not claim all cases passed unless:

- The remote command completed.
- Exit code and tool output were checked.
- Result files/logs were pulled back or inspected.
- Case counts reconcile with the generated case list.

Pull back these artifacts when present:

```text
*.result
*.out
result.xml
special_query.csv
*.log
wrapper stdout/stderr
export directories or validation summaries
```

## Fixed Report

Create `execution-report.md` in the requirement directory. Use `assets/test-execution-report-template.md` or `scripts/build_execution_report.py`.

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
