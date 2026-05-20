# testcase-skill

本仓库包含一个面向 IoTDB/TimechoDB SQL 测试用例生成的 Codex skill。

## Skill 名称

`iotdb-sql-testcase-pipeline`

## 适用场景

当你提供需求文档、设计文档、issue 或官网章节时，这个 skill 会默认：

- 先拆解出尽可能完整的原子测试点
- 再展开成测试点矩阵和测试点扩展表
- 再生成详细的 Markdown 测试用例
- SQL 可执行场景继续输出 `.run`
- 大数据或性能场景改为 benchmark 配置或 wrapper 方案
- 只做测试设计，不做远端执行、部署、清理、回收或报告生成

## 触发提示词

可直接使用下面这段话触发：

```text
请根据我提供的需求文档、设计文档、issue 或官方手册，先拆解出尽可能完整的测试点，再生成详细的 Markdown 测试用例。不要概括覆盖，要尽量展开正反例、边界值、权限、配置、模型差异和联动场景；如果是 SQL 可执行场景，再补充 .run；如果涉及大数据或性能，再改为 benchmark 配置或 wrapper 方案。全程只做测试设计，不做远端执行。
```

## 使用方式

- 直接给需求材料即可，skill 会自动按中文输出
- 如果想显式触发，也可以写：`Use $iotdb-sql-testcase-pipeline`

## 输出物

- 详细 Markdown 用例表
- 需要时输出 `.run`
- 需要时输出 benchmark 配置或 wrapper
- 覆盖自检结论、假设和阻塞项
