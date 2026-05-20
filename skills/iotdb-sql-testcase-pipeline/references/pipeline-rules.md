# Pipeline Rules

## Inputs

Collect these before generation:

| Field | Required | Notes |
|------|----------|-------|
| Requirement item | Yes | Prefer using it as the local requirement directory name. |
| Version | Yes | Example: `2.0.9.2`, `2.0.10.1`, `1.3.7.3`. |
| Model | Yes | `table`, `tree`, or `both`. |
| Source docs | Yes | Requirement/design docs or issue text. Official docs URLs are optional because the skill searches official manuals by default. |
| Local case artifact directory | Yes | Stores the generated Markdown cases and local artifacts. If omitted, use `<current workspace>/<requirement-item>/`. |
| Benchmark tool path | Required when large data/performance needs benchmark artifacts | Use it as the source for benchmark config or wrapper generation if the user provides it. |

If a requested detail can be discovered safely from local files, discover it instead of stopping.

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
- Record relevant manual section names or URLs in the Markdown `requirements source` column and in `.run` `-- source:` comments when they affect the case design.
- If network access or docs search is unavailable, continue from the supplied requirement/design/issue and explicitly note that the official manual lookup could not be completed.

## Local Artifact Layout

Keep generated cases and generated execution artifacts together in the local workspace.

| Path | Contents |
|------|----------|
| Local case artifact directory | Markdown case file, local generated `.run`, wrapper scripts, benchmark config copies, notes, and local review records. |
| Local model subdirectories | If `Model` is `both`, create separate `tree/` and `table/` subdirectories under the local case artifact directory. |

Rules:

- If the user provides a local directory, use it exactly and create it when missing.
- If the user does not provide a local directory, create `<current workspace>/<requirement-item>/`.
- Do not write generated cases into the skill repository unless the user explicitly chooses that repository as the local case artifact directory.
- The local generated `.run` is a generated artifact only. This skill does not deploy or execute it.

## Test-Point Matrix Requirements

Generate Markdown first from the user material plus the official manual lookup.

Before writing case rows, create an atomic `test-point matrix`. This matrix is the design source for the cases.

Minimum matrix columns:

| Column | Requirement |
|------|-------------|
| Test point ID | Stable ID, for example `TP-SQL-001`. |
| Function / rule | One independently testable rule, not a broad feature area. |
| Impact area | SQL syntax, DDL, DML, query, metadata, system table, permission, config, sync, cluster, performance, tool, or compatibility. |
| Positive scenario | The successful action that proves the rule. |
| Negative / error scenario | Invalid input, missing object, denied permission, disabled config, type mismatch, unsupported syntax, or failure path. |
| Boundary / combined scenario | Default/explicit values, NULL/empty data, old/new syntax, partial columns, source/target combinations, model differences. |
| Permission / config / model / difference | Required privilege, config switch, tree/table difference, source/target difference, or other visible state difference. |
| Test data | Concrete database, table/timeseries, rows, columns, tags, timestamps, volume, and boundary values. |
| Validation method | Exact SQL/action, expected rows/counts/metadata/error/metric, and artifact evidence. |
| Automation note | `.run`, wrapper, benchmark config, design-only, or blocked. |

Atomicity rules:

- Split broad categories such as permission, configuration, sync, cluster, performance, and metadata display into separate rows by operation, role, scope, switch value, model, and source/target state.
- Do not mark a requirement as covered just because a sentence appears in a case. Coverage requires an executable action, concrete data, a stable assertion, and cleanup.
- A case should normally map to one primary test point. If one case covers multiple test points, each point must have its own setup/action/assertion inside the steps.
- If the requirement changes a data path, include DML/query validation. Metadata checks alone are not sufficient.
- If a point is not automatable as an executable case, generate an explicit design case with trigger action, required evidence, and a blocking reason.

After the matrix, create a `test-point expansion table`. Do not skip this table for non-trivial requirements.

Minimum expansion columns:

| Column | Requirement |
|------|-------------|
| Test point ID | The parent TP ID. |
| Child scenario ID | Stable child ID, for example `TP-SQL-037-A`. |
| Child scenario type | Positive, negative, boundary, permission, config, syntax, sync, cluster, performance, audit, or cleanup. |
| Child scenario description | One concrete setup/action/assertion path. |
| Generated case ID | The final TC ID generated from this child scenario. |
| Automated? | `.run`, wrapper, benchmark config, design-only, or blocked. |
| Expansion basis | Why this child case exists, such as permission scope, syntax variant, config value, or source/target state. |

Expansion rules:

- `test point` is not equal to `case`. A TP may produce one TC only if it contains one action, one data set, one assertion, no variants, no paired result, and no environment difference.
- If a TP includes multiple values or words such as `separately`, `any of`, `multiple`, `several`, `at the same time`, `two kinds`, `three kinds`, `four kinds`, `object-level/DB-level/ANY`, `true/false`, `on/off`, `old/new`, `source/target`, `DROP VIEW/DROP TABLE`, `ALTER TABLE/ALTER VIEW`, `cold/hot`, `single/batch/concurrent`, `missing any privilege`, `pattern/privilege`, or `skipIfNoPrivileges`, it must normally produce multiple child scenarios and multiple cases.
- Permission TPs expand by role/user type, privilege scope, operation, security mode, granted state, denied state, user switch/login, and cleanup.
- Config TPs expand by each switch value and transition path: default, explicit, true, false, true->false, false->true, valid, invalid.
- DDL syntax TPs expand by command entry and object state: `DROP VIEW`, `DROP TABLE`, `IF EXISTS`, no `IF EXISTS`, existing object, missing object, `ALTER VIEW`, `ALTER TABLE`.
- Sync/Pipe TPs expand by source object, target object, pattern, privilege, cascade setting, target existence, and failure mode.
- Performance TPs expand by workload shape: query type, cold/hot run, single/batch/concurrent write, data scale, metric, threshold, benchmark config, and evidence path.
- The coverage self-review must report total TP count, expanded child-scenario count, final TC count, complex TP IDs that expanded to more than one TC, and any remaining TP->TC one-to-one mappings with reasons.

## Markdown Case Requirements

Use a Markdown table. The minimum required columns are:

| Column | Requirement |
|------|-------------|
| Case ID | Stable ID, for example `TC-SQL-001`. |
| Case name | Exact validation point. |
| Priority | `P0`, `P1`, or `P2`. |
| Major category | Major feature category, for example query, permissions, metadata, sync, performance, tool, table model, or tree model. |
| Module type | Query, auth, function, table model, tree model, cluster, Pipe, tool, performance, etc. |
| Subcategory | More specific category. |
| Requirements source | Requirement, design doc, issue, and relevant official manual section or URL. |
| Preconditions | State, permissions, config, or model type when relevant. |
| Operation data | Exact database/table/timeseries/user/file/config names and input rows or values. |
| Test data | Database, table/timeseries, inserted rows, boundary values. |
| Steps | Expanded setup, data prep, execution, validation, cleanup. |
| Expected result | Exact row count, fields, ordering, error keyword, file count, or metric rule. |
| Cleanup | `drop database`, `drop table`, `drop user`, file cleanup, etc. |
| Notes | Risk, constraints, version differences. |
| Test result | Fill after execution or leave as design placeholder. |
| Screenshot | Fill after execution when needed or leave as design placeholder. |

Coverage should include P0 positive flows, P1 boundaries/combinations/empty data/NULL/permissions/config differences, and P2 errors/compatibility/performance scenarios. Permission cases must include user creation, grant, login/switch user, verification, negative attempt when meaningful, and cleanup when that is part of the design.

Generate a coverage self-review after the table. It must list missing or intentionally non-automated points, metadata-only validations, missing negative cases, missing permission/config/model differences, assumptions, and any cases routed to benchmark or wrapper artifacts.

Performance cases must not be simplified. Include data scale, generation method, warm-up, measured iterations, metric, threshold/baseline rule, raw output path, and retention policy when those are relevant.

## Artifact Routing

- SQL-executable scenarios -> Markdown + `.run`.
- Large-data/performance scenarios -> Markdown + benchmark config or wrapper, plus minimal validation steps if needed.
- Non-SQL tool scenarios -> Markdown + wrapper.
- Not enough info or blocked -> Markdown only, with explicit reason.

## `.run` Rules

When a scenario is routed to `.run`, generate it as a reviewable artifact only.

- Use `<<NULL;`, `<<SQLSTATE;`, and `<<CHECKCODE;` consistently.
- Every case should have setup, test SQL, validation, and cleanup sections in the generated script.
- Table-model cases use `use <database>` after connect; tree-model cases use full paths.
- Large data should not be expanded into massive literal `INSERT` blocks; route that workload to benchmark artifacts.

## Benchmark Large-Data Artifacts

When a requirement needs large-volume data or performance coverage, generate a benchmark config copy or wrapper instead of massive SQL literals.

- Document the workload shape, model, data scale, metric, threshold, and validation SQL.
- Prefer a copied config or wrapper artifact over editing a shared benchmark config in place.
- The generated benchmark artifact is reviewable output only; this skill does not run it.

## Guardrails

- No remote execution, deployment, cleanup, pullback, or report generation.
- Do not collapse complex test points into one case.
- Do not use metadata-only checks as proof of data-path behavior.
- Do not treat a requirement sentence as coverage.
- Do not generate result-comparison or special-query-mask workflows.
- If a point cannot be automated, mark it design-only and explain why.
