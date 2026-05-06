# testcase-skill

This repository contains a Codex skill for IoTDB/TimechoDB SQL testcase automation.

## Skill

`iotdb-sql-testcase-pipeline`

Use this skill when you want Codex to turn IoTDB/TimechoDB requirements, design docs, official docs, issue text, or feature directories into:

- detailed Markdown testcase tables
- `.run` SQL automation files
- static checks before deployment
- remote deployment and SQL automation execution
- pulled-back `.result`, `.out`, `result.xml`, logs, screenshots, and fixed execution reports

## Install

Clone this repository, then copy the skill folder into your Codex skills directory:

```powershell
git clone https://github.com/xiaoze-cmd/testcase-skill.git
Copy-Item -Recurse .\testcase-skill\skills\iotdb-sql-testcase-pipeline $env:USERPROFILE\.codex\skills\
```

After installation, start a new Codex session so the skill metadata can be discovered.

## How To Use

You can trigger the skill explicitly with `$iotdb-sql-testcase-pipeline`, or implicitly by asking for IoTDB/TimechoDB SQL testcase generation, `.run` generation, deployment, execution, or report generation.

The most reliable form is:

```text
Use $iotdb-sql-testcase-pipeline to turn this IoTDB/TimechoDB requirement and docs into detailed cases, automation files, remote execution, and a fixed report.
```

## Trigger Prompts

Copy one of these prompts when starting a task.

### Generate Markdown Testcases

```text
Use $iotdb-sql-testcase-pipeline.
根据下面的 IoTDB/TimechoDB 需求生成详细 Markdown SQL 用例表。必须覆盖 P0/P1/P2、边界值、异常路径、权限差异、清理动作和预期结果；先不要生成 .run 文件。

需求：
<粘贴需求、设计文档或 issue 内容>
```

### Generate `.run` From Reviewed Markdown

```text
Use $iotdb-sql-testcase-pipeline.
基于当前目录中已审核通过的 Markdown 用例生成 SQL 自动化 .run 文件。生成前先做静态检查；不合格时停止并列出问题。每条用例必须独立 setup、执行、断言和 cleanup。
```

### Deploy And Execute

```text
Use $iotdb-sql-testcase-pipeline.
把当前需求目录下的 .run 文件部署到远端 SQL 自动化工具目录，先只读检查目标主机、目标目录、otf_new.properties 和 3C3D 集群状态，再执行 SQL 自动化测试，拉回 .result、.out、result.xml 和日志。
```

### Build Execution Report

```text
Use $iotdb-sql-testcase-pipeline.
根据本次 SQL 自动化执行产物生成 execution-report.md，必须使用固定报告模板，只填写执行路径、统计结果、失败明细、截图路径和必要备注，不要把大量日志粘贴到正文。
```

### Full Pipeline

```text
Use $iotdb-sql-testcase-pipeline.
请按 collect -> analyze -> case-md -> review -> run-gen -> lint -> deploy -> cluster-check -> execute-test -> report 的流程处理这个 IoTDB/TimechoDB SQL 需求。必须先生成详细 Markdown 用例并通过检查，再生成 .run；执行远端命令前先确认目标主机、目录、脚本和配置。

需求：
<粘贴需求、设计文档、官网链接或 issue 内容>
```

## Repository Layout

```text
skills/
  iotdb-sql-testcase-pipeline/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
```
