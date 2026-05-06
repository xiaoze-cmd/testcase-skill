# testcase-skill

这是一个 Codex Skill 仓库，用于 IoTDB/TimechoDB SQL 用例自动化流水线。

## Skill 名称

`iotdb-sql-testcase-pipeline`

这个 skill 用于把 IoTDB/TimechoDB 的需求文档、设计文档、官网章节、issue 或功能目录转换为完整的 SQL 自动化用例流程，包括：

- 生成详细 Markdown 用例表
- 根据已审核的 Markdown 用例生成 `.run` 自动化文件
- 生成前做静态检查
- 部署 `.run` 到远端 SQL 自动化工具目录
- 检查 3C3D 集群状态
- 执行 SQL 自动化工具
- 拉回 `.result`、`.out`、`result.xml`、日志和截图
- 使用固定模板生成执行报告

## 安装方式

克隆本仓库，然后把 skill 目录复制到 Codex 的 skills 目录：

```powershell
git clone https://github.com/xiaoze-cmd/testcase-skill.git
Copy-Item -Recurse .\testcase-skill\skills\iotdb-sql-testcase-pipeline $env:USERPROFILE\.codex\skills\
```

安装后重新打开一个 Codex 会话，让 Codex 重新发现 skill 元数据。

## 使用方式

推荐显式触发：

```text
Use $iotdb-sql-testcase-pipeline.
```

也可以通过描述 IoTDB/TimechoDB SQL 用例生成、`.run` 生成、远端部署、自动化执行、报告生成等任务来隐式触发。

最通用的触发提示词是：

```text
Use $iotdb-sql-testcase-pipeline to turn this IoTDB/TimechoDB requirement and docs into detailed cases, automation files, remote execution, and a fixed report.
```

## 常用触发 Prompt

下面这些 prompt 可以直接复制到 Codex 中使用。

### 只生成 Markdown 用例

```text
Use $iotdb-sql-testcase-pipeline.
根据下面的 IoTDB/TimechoDB 需求生成详细 Markdown SQL 用例表。
必须覆盖 P0/P1/P2、边界值、异常路径、权限差异、清理动作和预期结果。
先不要生成 .run 文件。

需求：
<粘贴需求、设计文档或 issue 内容>
```

### 基于已审核 Markdown 生成 `.run`

```text
Use $iotdb-sql-testcase-pipeline.
基于当前目录中已审核通过的 Markdown 用例生成 SQL 自动化 .run 文件。
生成前先做静态检查；不合格时停止并列出问题。
每条用例必须独立 setup、执行、断言和 cleanup。
```

### 部署并执行 SQL 自动化

```text
Use $iotdb-sql-testcase-pipeline.
把当前需求目录下的 .run 文件部署到远端 SQL 自动化工具目录。
先只读检查目标主机、目标目录、otf_new.properties 和 3C3D 集群状态。
确认无误后执行 SQL 自动化测试，并拉回 .result、.out、result.xml 和日志。
```

### 生成执行报告

```text
Use $iotdb-sql-testcase-pipeline.
根据本次 SQL 自动化执行产物生成 execution-report.md。
必须使用固定报告模板。
只填写执行路径、统计结果、失败明细、截图路径和必要备注。
不要把大量日志粘贴到报告正文。
```

### 执行完整流水线

```text
Use $iotdb-sql-testcase-pipeline.
请按 collect -> analyze -> case-md -> review -> run-gen -> lint -> deploy -> cluster-check -> execute-test -> report 的流程处理这个 IoTDB/TimechoDB SQL 需求。
必须先生成详细 Markdown 用例并通过检查，再生成 .run。
执行远端命令前先确认目标主机、目录、脚本和配置。

需求：
<粘贴需求、设计文档、官网链接或 issue 内容>
```

## 仓库结构

```text
skills/
  iotdb-sql-testcase-pipeline/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
```

## 使用注意事项

- Markdown 用例是 `.run` 文件的来源，不能跳过。
- `.run` 生成前必须做静态检查。
- 不要把 SSH 密码、API token、私钥等敏感信息写入仓库文件。
- 不要在未知正确性的版本上随意固化 `.result` 基准。
- 远端执行前应先确认目标主机、目标目录、目标 `.run` 文件和 `otf_new.properties`。
