# testcase-skill

这是一个 Codex Skill 仓库，用于 IoTDB/TimechoDB SQL 用例自动化流水线。

## Skill 名称

`iotdb-sql-testcase-pipeline`

这个 skill 用于把 IoTDB/TimechoDB 的需求文档、设计文档、官网章节、issue 或功能目录转换为完整的 SQL 自动化流程：

- 先生成详细 Markdown 表格形式用例文件
- Markdown 静态检查通过后，自动生成 `.run` 文件
- 根据用户传入的 IoTDB 安装目录和 SQL-test 工具目录做远端检查
- 支持 `1C1D` 和 `3C3D` 两种执行拓扑
- 支持树模型和表模型，两者配置不同
- 自动同步 IoTDB `dn_rpc_address` 与 SQL-test `iotdbURL`，端口固定为 `6667`
- 根据需要维护 SQL-test `special_query.csv` 屏蔽文件，用于忽略不稳定结果列
- 先跑 `setup` 模式生成 `.result`
- 重启并清理 IoTDB `data`、`logs` 后，再跑 `test` 模式生成 `.out`
- 拉回 `.result`、`.out`、`result.xml`、日志、截图，并生成固定格式执行报告

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

也可以通过描述 IoTDB/TimechoDB SQL 用例生成、`.run` 生成、1C1D/3C3D 执行、树模型/表模型配置、setup/test 执行、报告生成等任务来隐式触发。

## 必填信息

执行完整流水线时，建议直接在 prompt 里提供这些信息：

| 字段 | 示例 |
|------|------|
| 执行拓扑 | `1C1D` 或 `3C3D` |
| 模型类型 | `tree` 或 `table` |
| IoTDB 安装目录 | `/data/iotdb-enterprise-xxx/iotdb-enterprise-xxx-bin` |
| SQL-test 工具目录 | `/data/iotdb-sql-test-master` |
| SQL-test 执行主机 | `<SQL-test 所在主机 IP>` |
| 1C1D 主机 | `<1C1D 主机 IP>` |
| 3C3D 集群节点 | `<集群任意一个节点 IP>` |
| SSH 用户和 key | `ubuntu`、`IOTDB_SSH_KEY` 或本地 key 路径 |
| 需求内容 | 需求文档、设计文档、官网链接或 issue 内容 |

Codex 会先验证传入的 IoTDB 目录和 SQL-test 目录，再执行后续操作；不会优先使用旧记忆里的路径覆盖用户传入的路径。
针对 `3C3D` 集群测试，只需要提供集群中的任意一个节点 IP，不需要提供三台主机 IP。

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
- 如果 `.out` 中出现 `###### COMPARE RESULT : FAIL ######`，需要先比较 `.result` 和 `.out` 的真实结果列差异，再决定是否写入 `special_query.csv`。
- `Elapsed Time: ...` 这种工具耗时行不是结果列，不要写入 `special_query.csv`；但查询结果列里的 `elapsed_time` 可以作为候选屏蔽列。

可以让 Codex 用辅助脚本先列出差异列：

```text
请使用 scripts/suggest_special_query_masks.py 对比 .result 和 .out，列出真实不同的结果列，并给出建议追加到 special_query.csv 的行。
注意不要把 Elapsed Time 或 COMPARE RESULT : FAIL 这类工具状态行当作屏蔽列。
```

## 1C1D 完整执行 Prompt

复制下面的 prompt，并替换尖括号里的内容：

```text
Use $iotdb-sql-testcase-pipeline.
请在 1C1D 环境执行 IoTDB/TimechoDB SQL 用例自动化完整流水线。

执行要求：
1. 先根据需求生成详细 Markdown 表格形式用例文件。
2. Markdown 静态检查通过后，自动生成 .run 文件，不要停在 Markdown 阶段。
3. 使用我传入的 IoTDB 安装目录和 SQL-test 工具目录，先检查目录是否存在、配置是否正确，再执行操作。
4. 根据模型类型配置 SQL-test：表模型需要 sql_dialect=table，树模型不能保留 sql_dialect=table。
5. 读取 IoTDB 的 dn_rpc_address；SQL-test 的 iotdbURL 要同步成相同 IP，端口固定为 6667。
6. 检查是否存在时间、任务 ID、耗时、节点地址等不稳定列；如有，先备份并更新 user/CONFIG/special_query.csv。
7. 先把 SQL-test 改成 setup 模式并执行，生成 .result。
8. setup 执行完成后，停止 IoTDB，删除 IoTDB 安装目录下的 data 和 logs，再启动 IoTDB。
9. 再把 SQL-test 改成 test 模式执行，生成 .out 并对比 result.xml。
10. 拉回 .result、.out、result.xml、special_query.csv、日志和截图，生成 execution-report.md。

拓扑：1C1D
模型类型：<tree 或 table>
1C1D 主机：<主机 IP>
SQL-test 执行主机：<主机 IP>
SSH 用户：<ubuntu 或其他用户>
SSH key：<IOTDB_SSH_KEY 或本地 key 路径>
IoTDB 安装目录：<远端 IoTDB 安装目录>
SQL-test 工具目录：<远端 /data/iotdb-sql-test-master 等目录>

需求：
<粘贴需求、设计文档、官网链接或 issue 内容>
```

## 3C3D 完整执行 Prompt

复制下面的 prompt，并替换尖括号里的内容：

```text
Use $iotdb-sql-testcase-pipeline.
请在 3C3D 环境执行 IoTDB/TimechoDB SQL 用例自动化完整流水线。

执行要求：
1. 先根据需求生成详细 Markdown 表格形式用例文件。
2. Markdown 静态检查通过后，自动生成 .run 文件，不要停在 Markdown 阶段。
3. 使用我传入的 IoTDB 安装目录和 SQL-test 工具目录，先检查该集群节点上的目录是否存在、配置是否正确，再执行操作。
4. 根据模型类型配置 SQL-test：表模型需要 sql_dialect=table，树模型不能保留 sql_dialect=table。
5. 读取该节点配置中的 dn_rpc_address；SQL-test 的 iotdbURL 要同步成相同 IP，端口固定为 6667。
6. SQL-test 可以在指定执行主机上跑，但 iotdbURL 必须指向配置文件里的 dn_rpc_address，不要默认等同于 SQL-test 执行主机。
7. 检查是否存在时间、任务 ID、耗时、节点地址等不稳定列；如有，先备份并更新 user/CONFIG/special_query.csv。
8. 先把 SQL-test 改成 setup 模式并执行，生成 .result。
9. setup 执行完成后，停止该集群节点上的 IoTDB，删除该 IoTDB 安装目录下的 data 和 logs，再启动 IoTDB。
10. 再把 SQL-test 改成 test 模式执行，生成 .out 并对比 result.xml。
11. 拉回 .result、.out、result.xml、special_query.csv、日志和截图，生成 execution-report.md。

拓扑：3C3D
模型类型：<tree 或 table>
3C3D 集群节点：<集群任意一个节点 IP>
SQL-test 执行主机：<主机 IP>
SSH 用户：<ubuntu 或其他用户>
SSH key：<IOTDB_SSH_KEY 或本地 key 路径>
IoTDB 安装目录：<远端 IoTDB 安装目录>
SQL-test 工具目录：<远端 /data/iotdb-sql-test-master 等目录>

需求：
<粘贴需求、设计文档、官网链接或 issue 内容>
```

## 只生成用例和 `.run` 的 Prompt

如果暂时不执行远端环境，只想生成文件：

```text
Use $iotdb-sql-testcase-pipeline.
根据下面的 IoTDB/TimechoDB 需求生成详细 Markdown 表格形式 SQL 用例文件。
Markdown 静态检查通过后，继续自动生成 .run 文件。
先不要部署和执行远端环境。

模型类型：<tree 或 table>

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
- 默认是 Markdown 检查通过后自动生成 `.run`。
- 远端执行前必须确认目标主机、IoTDB 安装目录、SQL-test 工具目录、目标 `.run` 文件和 `otf_new.properties`。
- 树模型和表模型配置不同，不能混用 `sql_dialect=table`。
- 修改 IoTDB `dn_rpc_address` 后，必须同步 SQL-test `iotdbURL`；端口固定为 `6667`。
- 树模型 `iotdbURL` 只保留到 `jdbc:iotdb://<rpc_address>:6667`，端口后不能带 `?version=...` 或其他参数。
- 只有部分列不稳定时，优先用 `special_query.csv` 屏蔽对应列，不要直接用 `<<CHECKCODE;` 放弃整条查询结果对比。
- setup/test 双阶段执行之间需要重启 IoTDB，并清理 verified IoTDB 目录下的 `data` 和 `logs`。
- 不要把 SSH 密码、API token、私钥等敏感信息写入仓库文件。
