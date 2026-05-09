# testcase-skill

这是一个 Codex Skill 仓库，用于 IoTDB/TimechoDB SQL 用例自动化流水线。

## Skill 名称

`iotdb-sql-testcase-pipeline`

这个 skill 用于把 IoTDB/TimechoDB 的需求文档、设计文档、官网章节、issue 或功能目录转换为完整的 SQL 自动化流程：

- 默认根据需求、设计文档或 issue 去官方用户手册检索相关章节，不要求用户额外提供官网链接
- 执行过程中的步骤说明、状态更新、失败分析、确认选项、最终结果和报告正文默认使用中文
- 先生成详细 Markdown 表格形式用例文件
- Markdown 静态检查通过后，自动生成 `.run` 文件
- 按用户指定的本地目录保存 Markdown 用例和本地生成的 `.run`
- 根据用户传入的 IoTDB 安装目录和 SQL-test 工具目录做远端检查
- 支持 `1C1D` 和 `3C3D` 两种执行拓扑
- 支持树模型和表模型，两者配置不同
- `3C3D` 需要提供三台集群节点地址和可用 SSH key；清理、停止、重启会覆盖三台节点
- 如果模型类型是 `both`，会拆成树模型和表模型两套用例、两套 `.run`，并分别执行 setup/test
- 自动同步 IoTDB `dn_rpc_address` 与 SQL-test `iotdbURL`，端口固定为 `6667`
- 根据需要维护 SQL-test `special_query.csv` 屏蔽文件，用于忽略不稳定结果列
- 先跑 `setup` 模式生成 `.result`
- 重启并清理 IoTDB `data`、`logs` 后，再跑 `test` 模式生成 `.out`
- 如果执行后出现 `COMPARE RESULT : FAIL`，自动对比 `.result` 和 `.out` 并列出差异列
- 执行完成后把远端 `.run`、`.result`、`.out`、`result.xml`、日志等拉回到用户指定的本地目录
- 拉回 `.result`、`.out`、`result.xml`、日志、截图，并生成固定格式执行报告

## 安装方式

克隆本仓库，然后把 skill 目录复制到 Codex 的 skills 目录：

```powershell
git clone https://github.com/xiaoze-cmd/testcase-skill.git
Copy-Item -Recurse .\testcase-skill\skills\iotdb-sql-testcase-pipeline $env:USERPROFILE\.codex\skills\
```

安装后重新打开一个 Codex 会话，让 Codex 重新发现 skill 元数据。

## 使用方式

如果想强制指定使用这个 skill，可以显式触发：

```text
Use $iotdb-sql-testcase-pipeline.
```

日常使用不需要写 `Use $iotdb-sql-testcase-pipeline.`。直接描述 IoTDB/TimechoDB SQL 用例生成、`.run` 生成、1C1D/3C3D 执行、树模型/表模型配置、setup/test 执行、报告生成等任务即可隐式触发。只要提供需求、设计文档或 issue 内容，Codex 会默认去官方用户手册检索相关章节；官网链接是可选补充。

触发后，Codex 面向用户展示的内容必须使用中文，包括正在执行什么、执行到哪一步、失败原因、下一步可选项、最终结果和 `execution-report.md` 正文。命令、路径、SQL、配置 key、日志原文、错误码、文件名和工具固定输出可以保留原文。

## 必填信息

执行完整流水线时，建议直接在 prompt 里提供这些信息：

| 字段 | 示例 |
|------|------|
| 执行拓扑 | `1C1D` 或 `3C3D` |
| 模型类型 | `tree`、`table` 或 `both` |
| 本地用例文件目录 | `<本地保存 Markdown 用例和本地 .run 的目录>` |
| 本地拉回产物目录 | `<本地保存远端 .run、.result、.out、result.xml、日志等产物的目录>` |
| IoTDB 安装目录 | `/data/iotdb-enterprise-xxx/iotdb-enterprise-xxx-bin` |
| SQL-test 工具目录 | `/data/iotdb-sql-test-master` |
| SQL-test 执行主机 | `<SQL-test 所在主机 IP>` |
| 1C1D 主机 | `<1C1D 主机 IP>` |
| 3C3D 集群节点 | `<三个集群节点 IP 或主机名>` |
| SSH 用户和 key | `ubuntu`、`IOTDB_SSH_KEY`、三台节点各自的 key，或确认三台共用同一个 key |
| 需求内容 | 需求文档、设计文档或 issue 内容；官网链接可选 |

Codex 会先验证传入的 IoTDB 目录和 SQL-test 目录，再执行后续操作；不会优先使用旧记忆里的路径覆盖用户传入的路径。
针对 `3C3D` 集群测试，需要提供三台节点地址。SQL-test 连接仍然只使用配置文件中的一个 `dn_rpc_address:6667`，但停止、清理 `data/logs`、重启必须在三台节点上都执行。

## 本地产物目录

建议在 prompt 里明确指定两个本地目录：

| 目录 | 存放内容 |
|------|----------|
| 本地用例文件目录 | Markdown 用例、本地生成的 `.run`、包装脚本、命令清单、`execution-report.md` |
| 本地拉回产物目录 | 从 SQL-test 拉回的远端 `.run`、`.result`、`.out`、`result.xml`、日志、`special_query.csv`、截图 |

`.run` 的执行位置固定在远端 SQL-test 工具目录下，例如：

```text
<SQL-test 工具目录>/user/scripts/<feature>/<case-name>.run
```

也就是说：先在本地用例文件目录生成 Markdown 和 `.run`，再把 `.run` 部署到 SQL-test 目录执行，执行完后再把远端实际执行的 `.run` 和结果文件一起拉回本地拉回产物目录。

## 默认检索官方用户手册

生成用例时不需要单独提供官网链接。Codex 会根据需求、设计文档或 issue 中的 SQL 关键字、函数名、配置项、错误信息和中英文功能名，默认检索官方用户手册：

| 模型 | 默认手册 |
|------|----------|
| 树模型 | `https://www.timecho.com/docs/zh/UserGuide/latest/` |
| 表模型 | `https://www.timecho.com/docs/zh/UserGuide/latest-Table/` |
| 英文兜底 | `https://www.timecho-global.com/docs/UserGuide/latest/` |

如果模型类型是 `both` 或不明确，会同时检索树模型和表模型手册。生成的 Markdown 用例会在 `需求来源` 中写明相关需求、issue 和官方手册章节；`.run` 文件的 `-- 来源:` 注释也会保留这些来源。

## 关键配置规则

树模型和表模型的 SQL-test 配置不同。

表模型示例：

```properties
DBtype=IOTDB
iotdbURL=jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table
```

树模型示例：

```properties
DBtype=IOTDB
iotdbURL=jdbc:iotdb://<rpc_address>:6667
```

如果 IoTDB DataNode 配置中修改了：

```properties
dn_rpc_address=<rpc_address>
```

那么 SQL-test 的 `iotdbURL` 也必须同步为对应 IP；端口固定使用 `6667`。例如表模型应为：

```properties
iotdbURL=jdbc:iotdb://<rpc_address>:6667?version=V_1_0&sql_dialect=table
```

## 通用功能的树/表双模型执行

如果一个功能同时适用于树模型和表模型，请把模型类型填成 `both`。此时 Codex 必须拆成两套独立产物和两套执行流程：

```text
<本地用例文件目录>/
  tree/
    <case-name>-tree-cases.md
    <case-name>-tree.run
  table/
    <case-name>-table-cases.md
    <case-name>-table.run

<本地拉回产物目录>/
  tree/
    <远端执行的 tree .run>
    *.result
    *.out
    result.xml
    logs/
  table/
    <远端执行的 table .run>
    *.result
    *.out
    result.xml
    logs/
```

执行时不能把树模型和表模型混在一个 `.run` 里，也不能共用一套 SQL-test 配置。完整流程会运行四次 SQL-test：

1. 树模型 `setup`
2. 清理并重启 IoTDB 后，树模型 `test`
3. 切换 SQL-test 为表模型配置后，表模型 `setup`
4. 清理并重启 IoTDB 后，表模型 `test`

如果某个功能只适用于其中一种模型，就填 `tree` 或 `table`，不需要拆两套。

## 结果列屏蔽文件

SQL-test 还有一个结果列屏蔽文件：

```text
<SQL-test 工具目录>/user/CONFIG/special_query.csv
```

当某些查询只有部分列会因为时间、节点、任务 ID、耗时、构建信息等因素变化，但其他结果仍需要稳定对比时，不要直接把查询改成 `<<CHECKCODE;`，应优先在 `special_query.csv` 中添加屏蔽列。

写法：

```csv
SQL语句;屏蔽列名;屏蔽列名
```

示例：

```csv
show queries;query_id;start_time;datanode_id;elapsed_time;wait_time_in_server;
show regions;RegionId;CreateTime;TsFileSize;CompressionRatio;InternalAddress;
select * from root.**;Time;
```

注意：

- 第一列 SQL 必须和 `.run` 中的查询语句一致，大小写不敏感，前后空格会被忽略。
- SQL 字段里不要带结尾分号，因为分号是 CSV 分隔符。
- 后面的字段都是需要屏蔽的列名，列名大小写不敏感。
- 如果 SQL 或列名写错，工具通常不会报错，只是屏蔽不生效。
- 必须在 `setup` 模式执行前配置好，否则 `.result` 和 `.out` 可能不是同一套屏蔽规则。
- 如果 `test` 后才发现因为某个不稳定列导致对比失败，应更新 `special_query.csv` 后重新执行 `setup -> 清理重启 -> test`。
- 如果 `.out` 中出现 `###### COMPARE RESULT : FAIL ######`，Codex 会自动比较 `.result` 和 `.out` 的真实结果列差异，再让你选择是否写入 `special_query.csv`。
- `Elapsed Time: ...` 这种工具耗时行不是结果列，不要写入 `special_query.csv`；但查询结果列里的 `elapsed_time` 可以作为候选屏蔽列。

完整执行流程里，Codex 在 `test.sh` 执行后会检查退出码、`result.xml` 和 `.out`。只要发现 `COMPARE RESULT : FAIL` 或失败用例，就会自动运行 `scripts/suggest_special_query_masks.py`，按用例匹配 `.result` 和 `.out`，列出具体是哪条 SQL 的哪些列在 result/out 中不一致，并忽略 `Elapsed Time`、`COMPARE RESULT : FAIL` 这类工具状态行。

分析完成后，用户只需要确认下一步：

1. 再次运行比对。
2. 追加/合并屏蔽列到 `special_query.csv`。

只有在用户选择追加后，Codex 才会备份并更新 `special_query.csv`，然后重新执行 `setup -> 清理重启 -> test`，确保 `.result` 和 `.out` 使用同一套屏蔽规则。

## 1C1D 完整执行 Prompt

复制下面的 prompt，并替换尖括号里的内容：

```text
请在 1C1D 环境执行 IoTDB/TimechoDB SQL 用例自动化完整流水线。

执行要求：
0. 操作步骤、执行状态、失败分析、用户确认选项、最终结果和 execution-report.md 都用中文表达；命令、路径、SQL、配置 key 和日志原文保留原文。
1. 先根据需求生成详细 Markdown 表格形式用例文件。
2. 不需要我提供官网链接；请根据模型类型默认检索官方用户手册相关章节，并把引用到的章节写入 Markdown 的需求来源和 .run 的来源注释。
3. 如果模型类型是 both，把用例拆成 tree 和 table 两套 Markdown、两套 .run、两套拉回产物；不要混在同一个 .run。
4. Markdown 和本地生成的 .run 保存到“本地用例文件目录”。
5. Markdown 静态检查通过后，自动生成 .run 文件，不要停在 Markdown 阶段。
6. 把 .run 部署到 SQL-test 工具目录下的 user/scripts/<feature>/ 目录执行；执行完后把远端实际执行的 .run 再拉回本地拉回产物目录。
7. 使用我传入的 IoTDB 安装目录和 SQL-test 工具目录，先检查目录是否存在、配置是否正确，再执行操作。
8. 根据模型类型配置 SQL-test：表模型需要 sql_dialect=table，树模型不能保留 sql_dialect=table。
9. 读取 IoTDB 的 dn_rpc_address；SQL-test 的 iotdbURL 要同步成相同 IP，端口固定为 6667。
10. 检查是否存在时间、任务 ID、耗时、节点地址等不稳定列；如有，先备份并更新 user/CONFIG/special_query.csv。
11. 先把 SQL-test 改成 setup 模式并执行，生成 .result。
12. setup 执行完成后，停止 IoTDB，删除 IoTDB 安装目录下的 data 和 logs，再启动 IoTDB。
13. 再把 SQL-test 改成 test 模式执行，生成 .out 并对比 result.xml。
14. 如果模型类型是 both，需要按 tree setup -> tree test -> table setup -> table test 分开执行，期间按模型切换 SQL-test 配置并分别清理重启。
15. 如果发现 COMPARE RESULT : FAIL 或 result.xml 失败，自动对比对应 .result/.out，列出具体 SQL 和差异列，只让我选择“再次运行比对”或“追加屏蔽列到 special_query.csv”。
16. 拉回远端 .run、.result、.out、result.xml、special_query.csv、日志和截图到“本地拉回产物目录”，生成 execution-report.md。

拓扑：1C1D
模型类型：<tree、table 或 both>
本地用例文件目录：<本地保存 Markdown 用例和本地 .run 的目录>
本地拉回产物目录：<本地保存远端 .run、.result、.out、result.xml、日志等产物的目录>
1C1D 主机：<主机 IP>
SQL-test 执行主机：<主机 IP>
SSH 用户：<ubuntu 或其他用户>
SSH key：<IOTDB_SSH_KEY 或本地 key 路径>
IoTDB 安装目录：<远端 IoTDB 安装目录>
SQL-test 工具目录：<远端 /data/iotdb-sql-test-master 等目录>

需求：
<粘贴需求、设计文档或 issue 内容；官网链接可选>
```

## 3C3D 完整执行 Prompt

复制下面的 prompt，并替换尖括号里的内容：

```text
请在 3C3D 环境执行 IoTDB/TimechoDB SQL 用例自动化完整流水线。

执行要求：
0. 操作步骤、执行状态、失败分析、用户确认选项、最终结果和 execution-report.md 都用中文表达；命令、路径、SQL、配置 key 和日志原文保留原文。
1. 先根据需求生成详细 Markdown 表格形式用例文件。
2. 不需要我提供官网链接；请根据模型类型默认检索官方用户手册相关章节，并把引用到的章节写入 Markdown 的需求来源和 .run 的来源注释。
3. 如果模型类型是 both，把用例拆成 tree 和 table 两套 Markdown、两套 .run、两套拉回产物；不要混在同一个 .run。
4. Markdown 和本地生成的 .run 保存到“本地用例文件目录”。
5. Markdown 静态检查通过后，自动生成 .run 文件，不要停在 Markdown 阶段。
6. 把 .run 部署到 SQL-test 工具目录下的 user/scripts/<feature>/ 目录执行；执行完后把远端实际执行的 .run 再拉回本地拉回产物目录。
7. 使用我传入的 IoTDB 安装目录和 SQL-test 工具目录，先检查三台集群节点上的 IoTDB 目录是否存在、配置是否正确，再执行操作。
8. 根据模型类型配置 SQL-test：表模型需要 sql_dialect=table，树模型不能保留 sql_dialect=table。
9. 读取其中一个集群节点配置中的 dn_rpc_address；SQL-test 的 iotdbURL 要同步成相同 IP，端口固定为 6667。
10. SQL-test 可以在指定执行主机上跑，但 iotdbURL 必须指向配置文件里的 dn_rpc_address，不要默认等同于 SQL-test 执行主机。
11. 检查是否存在时间、任务 ID、耗时、节点地址等不稳定列；如有，先备份并更新 user/CONFIG/special_query.csv。
12. 先把 SQL-test 改成 setup 模式并执行，生成 .result。
13. setup 执行完成后，停止三台集群节点上的 IoTDB，分别删除三台节点 IoTDB 安装目录下的 data 和 logs，再启动三台节点。
14. 再把 SQL-test 改成 test 模式执行，生成 .out 并对比 result.xml。
15. 如果模型类型是 both，需要按 tree setup -> tree test -> table setup -> table test 分开执行，期间按模型切换 SQL-test 配置，并且每次清理重启都覆盖三台节点。
16. 如果发现 COMPARE RESULT : FAIL 或 result.xml 失败，自动对比对应 .result/.out，列出具体 SQL 和差异列，只让我选择“再次运行比对”或“追加屏蔽列到 special_query.csv”。
17. 拉回远端 .run、.result、.out、result.xml、special_query.csv、日志和截图到“本地拉回产物目录”，生成 execution-report.md。

拓扑：3C3D
模型类型：<tree、table 或 both>
本地用例文件目录：<本地保存 Markdown 用例和本地 .run 的目录>
本地拉回产物目录：<本地保存远端 .run、.result、.out、result.xml、日志等产物的目录>
3C3D 集群节点 1：<节点 1 IP 或主机名>
3C3D 集群节点 2：<节点 2 IP 或主机名>
3C3D 集群节点 3：<节点 3 IP 或主机名>
SQL-test 执行主机：<主机 IP>
SSH 用户：<ubuntu 或其他用户>
SSH key 节点 1：<IOTDB_SSH_KEY、本地 key 路径，或共用 key>
SSH key 节点 2：<IOTDB_SSH_KEY、本地 key 路径，或共用 key>
SSH key 节点 3：<IOTDB_SSH_KEY、本地 key 路径，或共用 key>
IoTDB 安装目录：<远端 IoTDB 安装目录>
SQL-test 工具目录：<远端 /data/iotdb-sql-test-master 等目录>

需求：
<粘贴需求、设计文档或 issue 内容；官网链接可选>
```

## 只生成用例和 `.run` 的 Prompt

如果暂时不执行远端环境，只想生成文件：

```text
根据下面的 IoTDB/TimechoDB 需求生成详细 Markdown 表格形式 SQL 用例文件。
操作步骤、执行状态、失败分析、最终结果和生成文件正文都用中文表达；命令、路径、SQL、配置 key 和日志原文保留原文。
不需要我提供官网链接；请根据模型类型默认检索官方用户手册相关章节，并把引用到的章节写入 Markdown 的需求来源和 .run 的来源注释。
Markdown 静态检查通过后，继续自动生成 .run 文件。
先不要部署和执行远端环境。

模型类型：<tree、table 或 both>
本地用例文件目录：<本地保存 Markdown 用例和本地 .run 的目录>

需求：
<粘贴需求、设计文档或 issue 内容；官网链接可选>
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
- 面向用户的过程说明、步骤、结果、失败原因、确认选项和报告正文都应使用中文；不要把执行过程总结成英文。
- 默认是 Markdown 检查通过后自动生成 `.run`。
- Markdown 用例和本地生成的 `.run` 放在“本地用例文件目录”；远端实际执行的 `.run` 必须放在 SQL-test 工具目录的 `user/scripts/<feature>/` 下。
- 模型类型是 `both` 时必须拆成 tree/table 两套 Markdown、两套 `.run`、两套产物目录；完整执行需要四次 SQL-test：tree setup、tree test、table setup、table test。
- `3C3D` 必须提供三台节点地址和可用 SSH key。SQL-test 只连接一个 `dn_rpc_address:6667`，但停止、清理、重启要覆盖三台节点。
- 执行完成后需要把远端实际执行的 `.run` 和 `.result`、`.out`、`result.xml`、日志等一起拉回“本地拉回产物目录”。
- 远端执行前必须确认目标主机、IoTDB 安装目录、SQL-test 工具目录、目标 `.run` 文件和 `otf_new.properties`。
- 树模型和表模型配置不同，不能混用 `sql_dialect=table`。
- 修改 IoTDB `dn_rpc_address` 后，必须同步 SQL-test `iotdbURL`；端口固定为 `6667`。
- 树模型 `iotdbURL` 只保留到 `jdbc:iotdb://<rpc_address>:6667`，端口后不能带 `?version=...` 或其他参数。
- 只有部分列不稳定时，优先用 `special_query.csv` 屏蔽对应列，不要直接用 `<<CHECKCODE;` 放弃整条查询结果对比。
- setup/test 双阶段执行之间需要重启 IoTDB，并清理 verified IoTDB 目录下的 `data` 和 `logs`。
- 不要把 SSH 密码、API token、私钥等敏感信息写入仓库文件。
