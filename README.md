# testcase-skill

This repository contains a Codex skill for IoTDB/TimechoDB SQL test-case generation.

## Skill name

`iotdb-sql-testcase-pipeline`

This skill turns IoTDB/TimechoDB requirement docs, design docs, official manual topics, and issues into reviewable test-design artifacts:

- It searches the official manual by default; docs URLs are optional supplements
- It builds an atomic `test-point matrix` first, then a `test-point expansion table`
- It turns the matrix and expansion table into detailed Markdown cases without treating a mention of the requirement sentence as coverage
- It keeps data-path, permission, config, sync, and performance differences visible in the case design
- `SHOW`, `DESC`, and `information_schema` are only used for metadata behavior, not for proving data-path behavior
- It produces detailed Markdown case tables first
- After the Markdown passes static checks, it can route scenarios to `.run`, benchmark config, or wrapper artifacts
- If a test point is not SQL, it can route the scenario to benchmark/wrapper design instead of forcing a `.run`
- It supports both tree and table models, with separate artifacts when `both` is requested
- For large-data scenarios, it routes the workload to benchmark artifacts instead of massive literal `INSERT` blocks

## General design constraints

This skill is a general IoTDB/TimechoDB SQL test-design tool, not a feature-specific template. Every new requirement should be re-analysed from the requirement, design doc, and official manual to produce executable, verifiable, and traceable test points before detailed cases are generated.

Generation rules:

- One test point validates one observable rule; do not compress multiple details into one broad case
- Every functional statement should be provable by SQL, benchmark design, wrapper, logs, or generated artifacts; merely mentioning the requirement sentence is not coverage
- Positive paths should be paired with negative paths where meaningful; default values should be paired with explicit values; permission coverage should include granted, denied, and scope differences
- A complex requirement should not become one test point and one case; it should first be expanded into a test-point expansion table and then into detailed cases
- Pipe, cluster, performance, audit, and large-data content should not be casually marked as a follow-up item; if automation is impossible, state the blocking reason, trigger action, required environment, and evidence plan
- Markdown case tables should include fields such as case name, major category, subcategory, operation data, cleanup, test result, and screenshot

## Usage

To force this skill explicitly:

```text
Use $iotdb-sql-testcase-pipeline.
```

In normal use, just provide the requirement, design doc, or issue. Codex will search the official manual by default and output user-facing text in Simplified Chinese.
