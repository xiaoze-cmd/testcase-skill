# Pipeline Rules

## Inputs

Collect these before execution:

| Field | Required | Notes |
|------|----------|-------|
| Requirement item | Yes | Prefer using it as the local directory name. |
| Version | Yes | Example: `2.0.9.2`, `2.0.10.1`, `1.3.7.3`. |
| Model | Yes | `table`, `tree`, or both. |
| Source docs | Yes | Requirement/design docs and official docs URLs. |
| Remote host | Yes | Default SQL runner host is often `172.20.70.47`. |
| SSH identity | Yes | Use `IOTDB_SSH_KEY` or a local private key path; never write passwords. |
| IoTDB install path | Runtime verify | Do not trust stale paths without checking. |
| SQL automation path | Runtime verify | Usually `/data/iotdb-sql-test-master`. |

If a requested detail can be discovered safely from local files or the remote server, discover it instead of stopping.

## Markdown Case Requirements

Use a Markdown table. The minimum required columns are:

| Column | Requirement |
|------|-------------|
| 用例编号 | Stable ID, for example `TC-SQL-001`. |
| 用例名称 | Exact validation point. |
| 用例级别 | `P0`, `P1`, or `P2`. |
| 模块类型 | Query, auth, function, table model, tree model, cluster, Pipe, tool, performance, etc. |
| 二级分类 | More specific category. |
| 需求来源 | Requirement, design doc, official docs section, or issue. |
| 前置条件 | Cluster state, permissions, config, model type. |
| 测试数据 | Database, table/timeseries, inserted rows, boundary values. |
| 操作步骤 | Expanded setup, data prep, execution, validation, cleanup. |
| 预期结果 | Exact row count, fields, ordering, error keyword, file count, or metric rule. |
| 清理动作 | `drop database`, `drop table`, `drop user`, file cleanup, etc. |
| 备注 | Risk, constraints, version differences. |
| 测试结果 | Fill after execution. |
| 截图 | Fill after execution when needed. |

Coverage should include P0 positive flows, P1 boundaries/combinations/empty data/NULL/permissions, and P2 errors/compatibility/cluster scenarios. Permission cases must include user creation, grant, login/switch user, verification, and cleanup.

Performance cases must not be simplified. Include:

- Data scale and generation method.
- Warm-up and measured iterations.
- Metric: latency, throughput, exported row count, file count, or resource usage.
- Threshold rule or comparison baseline.
- Where raw timing/output logs are stored.
- Whether data is retained or cleaned.

## Automation File Rules

Generate automation from reviewed Markdown only.

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

For command-line tools such as `export-data.sh`, generate an executable wrapper script and a command inventory file. The wrapper should log:

- Exact command.
- Start/end time.
- Exit code.
- Export/output directory.
- Validation counts.
- Cleanup or retention policy.

## Remote Execution

Use SSH/SCP with key authentication. Example shape on Windows:

```powershell
$key = $env:IOTDB_SSH_KEY
if (-not $key) { $key = "C:\Users\tiany\.ssh\sql_testcase_automation_ed25519" }
ssh -i $key ubuntu@172.20.70.47 "hostname && date"
scp -i $key local.run ubuntu@172.20.70.47:/tmp/local.run
```

Before deployment:

1. Confirm remote host and user.
2. Confirm SQL automation root exists.
3. Confirm target upload directory.
4. Confirm `user/CONFIG/otf_new.properties` and current model/dialect settings.
5. Back up any config file before editing it.

Default SQL automation paths:

```text
/data/iotdb-sql-test-master/test.sh
/data/iotdb-sql-test-master/user/CONFIG/otf_new.properties
/data/iotdb-sql-test-master/user/scripts/
/data/iotdb-sql-test-master/user/result/
```

Default upload convention:

```text
/data/iotdb-sql-test-master/user/scripts/<feature>/<case-name>.run
```

## Cluster And Model Handling

Always perform read-only checks first:

```bash
ps -ef | grep -E 'ConfigNode|DataNode' | grep -v grep
ss -ltnp | grep 6667 || true
```

Common 3C3D hosts:

```text
172.20.70.47
172.20.70.48
172.20.70.49
```

Common node-level start sequence when no cluster `start-all.sh` exists:

```bash
cd /data/iotdb-enterprise-1.3.7.3-bin-rc1/iotdb-enterprise-1.3.7-SNAPSHOT-bin
sudo -n ./sbin/start-confignode.sh
sudo -n ./sbin/start-datanode.sh
```

Common stop sequence:

```bash
cd /data/iotdb-enterprise-1.3.7.3-bin-rc1/iotdb-enterprise-1.3.7-SNAPSHOT-bin
sudo -n ./sbin/stop-confignode.sh
sudo -n ./sbin/stop-datanode.sh
```

If `sudo -n` fails, do not embed passwords. Report that passwordless sudo or an interactive secure method is required.

For model switching, inspect current SQL automation config and IoTDB config first. Back up the file with a timestamp suffix, change only the needed dialect/model setting, restart IoTDB if the config requires it, then re-check process and RPC port.

## Execution Modes

Use setup/baseline mode only when explicitly requested. Otherwise run test/verification mode.

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

- Requirement, version, execution date, environment.
- Executed script/remote command/log paths/artifact paths.
- Total, passed, failed, blocked, not run, pass rate, conclusion.
- Failure detail rows, or `无`.
- Screenshot/evidence image paths.
- Necessary notes such as data retained/cleaned and version differences.

If screenshots are requested, create or attach at least:

```text
report-screenshot-01-execution.png
report-screenshot-02-artifacts.png
report-screenshot-03-validation.png
```

Screenshots can be terminal captures, rendered report captures, UI captures, or evidence images generated from logs/metrics, but they must correspond to real execution evidence.
