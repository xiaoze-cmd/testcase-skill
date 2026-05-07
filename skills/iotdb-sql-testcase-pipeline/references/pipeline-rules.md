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
| Remote host list | Yes | One host for `1C1D`; three hosts for `3C3D`. |
| SQL-test runner host | Yes | May be the same as an IoTDB node; default to the first host only after verification. |
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

- Use three hosts. Each host may run both ConfigNode and DataNode.
- Verify the supplied IoTDB directory on all three hosts.
- Run node-level start/stop commands on all three hosts.
- Choose one SQL-test runner host explicitly. If not supplied, use the first verified host.
- Choose one DataNode RPC endpoint for SQL-test. It must match the chosen DataNode's `dn_rpc_address` and `dn_rpc_port`.

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
iotdbURL=jdbc:iotdb://<rpc_address>:<rpc_port>?version=V_1_0&sql_dialect=table
```

- `.run` should create a database and then run `use <database>;`.
- Table definitions must distinguish `TAG`, `ATTRIBUTE`, and `FIELD`.
- After switching users, run `use <database>;` again before table SQL.

### Tree Model

- Do not keep `sql_dialect=table` in `iotdbURL`.

```properties
DBtype=IOTDB
iotdbURL=jdbc:iotdb://<rpc_address>:<rpc_port>?version=V_1_0
```

- `.run` must not use `use <database>;`.
- Use full paths such as `root.test.d1.s1`.
- `create database` must not use table-model assumptions.

## RPC Address And SQL-test URL Sync

Before running SQL-test, inspect DataNode RPC config:

```bash
grep -E '^(dn_rpc_address|dn_rpc_port)=' "$IOTDB_DIR/conf/iotdb-datanode.properties"
```

Rules:

- `dn_rpc_address` is the IP SQL-test should connect to unless the user passes a different reachable RPC endpoint.
- `dn_rpc_port` is the port SQL-test should connect to; default is usually `6667`, but verify the file.
- If you edit `dn_rpc_address`, update `iotdbURL` in `otf_new.properties` to the same IP.
- If you edit `dn_rpc_port`, update `iotdbURL` to the same port.
- Preserve unrelated JDBC parameters.
- Ensure `sql_dialect=table` exists only for table model.

Example: if DataNode config contains:

```properties
dn_rpc_address=172.20.70.49
dn_rpc_port=6667
```

Then table-model SQL-test config should use:

```properties
iotdbURL=jdbc:iotdb://172.20.70.49:6667?version=V_1_0&sql_dialect=table
```

For `3C3D`, do not assume the SQL-test runner host is the same as the RPC endpoint. The SQL-test runner may be host A while the selected DataNode RPC endpoint is host B; `iotdbURL` must still point to the selected DataNode's `dn_rpc_address`.

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
ssh -i $key ubuntu@172.20.70.47 "hostname && date"
scp -i $key local.run ubuntu@172.20.70.47:/tmp/local.run
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

For `1C1D`, run start/stop on the single IoTDB host. For `3C3D`, run start/stop on all three IoTDB hosts. If `sudo -n` fails, do not embed passwords. Report that passwordless sudo or an interactive secure method is required.

## Setup/Test Execution Sequence

For full automated execution, use the two-phase sequence below to avoid dirty data causing `.result` and `.out` differences.

1. Generate Markdown cases.
2. Generate `.run` automatically from the checked Markdown.
3. Lint Markdown and `.run`.
4. Deploy `.run` to `<SQL_TEST_DIR>/user/scripts/<feature>/<case-name>.run`.
5. Configure `otf_new.properties` for topology, model, and synchronized `iotdbURL`.
6. Set SQL-test execution mode to `setup`. The exact property key must be verified in `otf_new.properties` or `test.sh`; commonly it is a setup/test mode flag.
7. Run:

```bash
cd "$SQL_TEST_DIR"
./test.sh
```

8. Collect generated `.result` files and setup logs.
9. Stop IoTDB on the `1C1D` node or all `3C3D` nodes.
10. Resolve and verify cleanup paths before deletion:

```bash
cd "$IOTDB_DIR"
pwd
test -d "$IOTDB_DIR/data" && test -d "$IOTDB_DIR/logs"
```

11. Delete only the verified IoTDB data/log directories:

```bash
rm -rf "$IOTDB_DIR/data" "$IOTDB_DIR/logs"
```

12. Restart IoTDB on the `1C1D` node or all `3C3D` nodes.
13. Re-check process and RPC port.
14. Set SQL-test execution mode to `test`.
15. Run `./test.sh` again.
16. Pull back `.out`, `result.xml`, test logs, and any updated `.result` references needed for diagnosis.
17. Compare case counts and failures before reporting.

Do not skip the restart and cleanup between setup and test unless the user explicitly requests a faster non-isolated run.

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

If screenshots are requested, create or attach at least:

```text
report-screenshot-01-execution.png
report-screenshot-02-artifacts.png
report-screenshot-03-validation.png
```

Screenshots can be terminal captures, rendered report captures, UI captures, or evidence images generated from logs/metrics, but they must correspond to real execution evidence.
