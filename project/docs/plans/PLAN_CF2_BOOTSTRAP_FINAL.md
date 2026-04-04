# Final Plan: Close Remaining CF-2 and Bootstrap Gaps

**Дата:** 2026-04-04  
**Гілка:** `research/methodology-foundation-clean`  
**Статус:** final adjudicated execution plan  
**Related baseline:** `project/docs/reviews/V1_CLOSEOUT_2026-04-03.md`  
**Supersedes for active execution:**  
- `project/docs/plans/PLAN_CF2_BOOTSTRAP_CODEX_FOR_MULTI_MODEL_TRIANGULATION.md`
- `project/docs/plans/PLAN_CF2_BOOTSTRAP_CLADE_FOR_MULTI_MODEL_TRIANGULATION.md`
- `project/docs/plans/PLAN_POST_V1_INTAKE_BOOTSTRAP.md` for the bootstrap slice only

## Призначення

Цей документ є merged і adjudicated execution plan для двох незакритих зон після `v1` closeout:

- `CF-2`: compiler lacks cross-field semantic inference
- bootstrap / init gap у human-facing intake workflow

План свідомо бере за основу сильніші architectural decisions із Codex draft і додає точкові practical improvements із Claude draft там, де вони покращують UX, testability або operator clarity без architectural regressions.

## Repo-Verified Current State

Перед злиттям планів були окремо перевірені кілька factual points, щоб не переносити historical drift у final plan.

### Verified facts

- `project/specs/questionnaire/role_assignments.template.yaml` зараз містить demo assignments, а не clean scaffold.
- `sample_object_02` на поточному baseline має:
  - `7` compiled `tbd` fields;
  - `8` warnings;
  - `2` errors;
  - `5` current assumptions from archetype defaults.
- `preview`, `review` і `evidence` уже йдуть через shared snapshot path.
- `generate` і top-level `compile` досі мають власні entry checks і не користуються shared workspace validation helper.

### Consequences for planning

- Bootstrap не повинен blindly copy current template with demo people.
- Claims about exact post-change warning deltas не слід вважати accepted fact до реального implementation + test run.
- Shared workspace validation потрібно робити не "всюди з нуля", а через винесення reusable checks для `generate`, `compile` і snapshot-backed commands.

## Adjudicated Design Summary

### Decisions

- Cross-field business rules живуть у YAML catalog, не в Python lambdas.
- Compiler має окремо підтримувати:
  - inference for missing / `tbd` fields;
  - contradiction detection for explicit answers that conflict with strong semantic expectations.
- Inferred values можуть покращувати downstream compilation, але не стають confirmed human input.
- Rule execution model має бути deterministic bounded fixpoint, а не hardcoded two-pass.
- `project/intake init` є окремою one-time bootstrap command.
- `object_id` є machine identifier і може explicit override-ити basename workspace path через `--object-id`.
- `object_id` лишається ASCII-safe і валідованим regex-ом.
- Bootstrap materialization повинна зберігати template metadata/rules, але не переносити demo assignees в реальний workspace.

### What is intentionally borrowed from the Claude draft

- concrete source-splitting in `validate_stage_confidence`;
- practical CLI error improvements;
- explicit ASCII validation for `object_id`;
- focused regression tests around operator-facing bootstrap behavior.

## Part 1: Cross-Field Inference and Semantic Consistency

## Why

Current compiler already does useful normalization work:

- detects questionnaire version;
- resolves archetype;
- applies archetype defaults;
- normalizes bool-like values.

But it still lacks two separate capabilities:

1. deterministic gap filling when cross-field evidence makes a `tbd` target unambiguous;
2. explicit contradiction surfacing when a human answer conflicts with strong semantic expectations.

These are related but not identical responsibilities. The final design keeps them distinct.

## Architectural Contract

Compiler flow becomes:

`detect_version -> load_archetypes -> resolve_archetype -> apply_archetype_defaults -> apply_cross_field_inferences -> normalize_boolish_enums -> return`

Validation stays outside compiler:

`build_requirements_model -> validate_requirements_model -> compile_graphs -> validators`

The key contract is:

- inference fills only missing / `tbd` targets;
- contradictions never overwrite explicit answers;
- contradiction findings remain visible to validators / review;
- inferred values flow downstream into graph compilation and validators with explicit provenance;
- inferred values do not increase evidence maturity and do not count as confirmed questionnaire answers.

## Rule Representation

Add YAML rule catalog:

`project/specs/inference/cross_field_rules.yaml`

Each rule record must include:

- `rule_id`
- `mode`: `infer_if_tbd` or `flag_if_conflicts`
- `when`
- `target_section`
- `target_field`
- `reason`
- optional `source_fields`
- `inferred_value` for inference rules

Python keeps only a small evaluator layer for operators such as:

- `eq`
- `in`
- `is_yes`
- `all_of`
- `any_of`
- `not_in`

This preserves YAML-first policy traceability while keeping execution logic simple and testable.

## Inference Semantics

Inference firing contract:

- a rule fires only if target is missing or `tbd`;
- explicit human answers are never overwritten;
- concrete archetype defaults are also never overwritten by inference;
- each inference event is recorded with full provenance;
- downstream graph compilation may consume inferred values;
- inferred values remain review-required until explicitly confirmed or waived.

Each inference event must include at least:

- `kind: inference`
- `rule_id`
- `section`
- `field_id`
- `original_value`
- `assumed_value`
- `source_fields`
- `pass_index`
- `review_required: true`
- `source: inference:<rule_id>`

## Consistency Layer

Add a dedicated semantic consistency validator:

`project/src/validators/validate_semantic_consistency.py`

Its job is not to mutate data. Its job is to turn explicit semantic conflicts into reviewable findings.

Examples:

- `remote_ops` with `oob_required = no`
- `timing_accuracy_class in {tens_of_us, sub_us}` with `sync_protocol != ptp`
- `criticality_class in {high, mission_critical}` with `redundancy_target = none`
- `security_zone_model in {dmz_centric, strict_isolation}` with `audit_logging_required = no`

This keeps "we inferred a plausible default" separate from "the human answered something contradictory".

## Execution Model

Do not hardcode `2` passes.

Use:

- deterministic rule order;
- bounded fixpoint loop;
- rerun until no new inferences fire;
- `max_passes = 4`;
- fail fast if different rules try to infer different values for the same target.

This is the smallest model that scales beyond the currently known single cascade without overengineering.

## Initial Rule Set

### `infer_if_tbd`

- `metadata.criticality_class in {high, mission_critical} -> resilience.redundancy_target = n_plus_1`
- `object_profile.staffing_model == remote_ops -> security_access.oob_required = yes`
- `critical_services.video_required = yes -> power_environment.poe_required = yes`
- `critical_services.iiot_required = yes AND critical_services.video_required = yes -> power_environment.poe_budget_class = heavy`
- `time_sync.timing_required = yes AND timing_accuracy_class in {tens_of_us, sub_us} -> time_sync.sync_protocol = ptp`
- `time_sync.timing_required = yes AND timing_accuracy_class not in {tens_of_us, sub_us} -> time_sync.sync_protocol = ntp`
- `security_access.security_zone_model in {strict_isolation, dmz_centric} -> security_access.audit_logging_required = yes`
- `critical_services.control_required = yes -> time_sync.timing_required = yes`

### `flag_if_conflicts`

- `remote_ops AND oob_required = no`
- `timing_accuracy_class in {tens_of_us, sub_us} AND sync_protocol != ptp`
- `criticality_class in {high, mission_critical} AND redundancy_target = none`
- `security_zone_model in {dmz_centric, strict_isolation} AND audit_logging_required = no`

## Stage Confidence and Governance

`validate_stage_confidence.py` must stop collapsing all assumptions into one source bucket.

At minimum it must distinguish:

- `archetype_default_count`
- `inference_count`

Reporting must communicate:

- concept/basic-design output may mention both categories;
- inferred values are still assumptions, not confirmations;
- inferred values do not make a workspace appear more mature than it really is.

Adopt the Claude draft's practical message split, but keep the stronger governance rule from the Codex draft: inferred values never masquerade as confirmed data.

## Test Strategy

Add:

- `project/tests/test_inference_rules.py`

Cover:

- each inference rule fires when condition is met and target is `tbd`/missing;
- explicit value is never overwritten;
- archetype default blocks inference;
- deterministic fixpoint behavior;
- conflicting inference attempts raise a clear error;
- contradiction findings are surfaced by the semantic consistency validator;
- repeated runs are idempotent and byte-stable.

Update:

- `project/tests/test_pipeline_e2e.py`

Adjust assertions against the verified current baseline instead of historical assumptions.

Do not pre-commit to exact warning deltas in the plan text. The implementation must prove the resulting counts.

## Part 2: Bootstrap / Init Command

## Why

New operators naturally try:

`project/intake generate <workspace>`

as the first command for a new object and currently hit a bootstrap failure. This is not a docs polish issue. It is a product entry-point gap.

## CLI Contract

Add:

`project/intake init <workspace> [--object-id <id>]`

Semantics:

- `init` is a one-time bootstrap command;
- `generate` regenerates workbooks inside an already initialized workspace.

This keeps the CLI understandable and avoids overloading `generate` with bootstrap semantics.

## `object_id` Semantics

Use:

- explicit `--object-id` when provided;
- otherwise fallback to `basename(workspace_path)`.

Validate `object_id` against:

`^[a-z][a-z0-9_-]{1,63}$`

This gives the best of both drafts:

- machine-safe identifiers remain strict;
- human-facing workspace directory names may still be friendly or non-ASCII when `--object-id` is explicit.

## Init Behavior

`init` must:

1. resolve and validate `object_id`;
2. allow a path that does not yet exist;
3. allow an existing empty directory;
4. fail if `role_assignments.yaml` already exists;
5. materialize `role_assignments.yaml` from template;
6. write top-level `object_id`;
7. print a short next-step message.

Required post-init message:

```text
Workspace initialized. Edit role_assignments.yaml, then run:
project/intake generate <workspace>
```

## Template Materialization

Do not blindly copy the current template assignments.

Rendered `role_assignments.yaml` must:

- preserve template metadata and rules;
- inject top-level `object_id`;
- replace demo `assignments` with either:
  - an empty list; or
  - an explicitly TODO-marked starter scaffold.

The key constraint is the same either way: no demo personas should leak into real workspace bootstrap.

## Shared Workspace Validation

Unify workspace entry checks across:

- `generate`
- `compile`
- `preview`
- `review`
- `evidence`

The helper must distinguish:

- workspace path missing;
- path exists but is not a directory;
- workspace exists but `role_assignments.yaml` is missing;
- workspace exists but required generated inputs are missing for a later command.

This is not a full redesign of every command. It is a reuse and consistency pass around entry checks and operator messages.

## Operator-Facing Error Handling

Bring forward the Claude draft's concrete UX improvements.

At minimum:

- `generate` on missing workspace should suggest `project/intake init <workspace>`;
- `compile` should clearly differentiate:
  - missing workspace;
  - missing `role_assignments.yaml`;
  - missing `.xlsx` responses.

Snapshot-backed commands should keep their shared entry-point behavior but use the same user-facing vocabulary.

## Bootstrap Test Strategy

Add:

- `project/tests/test_init_workspace.py`

Cover:

- happy path;
- already initialized workspace -> clear error;
- empty directory -> success;
- invalid `object_id` -> clear error;
- `--object-id` with non-ASCII workspace path;
- `init -> generate -> compile` smoke path in a temp workspace.

Update docs:

- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`
- `project/README.md`

## Files to Modify

### Part 1

- `project/src/compiler/build_requirements_model.py`
- `project/src/run_pipeline.py`
- `project/src/validators/validate_stage_confidence.py`
- `project/tests/test_pipeline_e2e.py`
- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`

### Part 2

- `project/intake`
- `project/src/intake/generate_intake_sheets.py`
- `project/src/intake/compile_intake.py`
- `project/src/intake/workspace_snapshot.py`
- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`
- `project/README.md`

## New Files

- `project/specs/inference/cross_field_rules.yaml`
- `project/src/validators/validate_semantic_consistency.py`
- `project/tests/test_inference_rules.py`
- `project/src/intake/init_workspace.py`
- `project/src/intake/workspace_validation.py`
- `project/tests/test_init_workspace.py`

## Recommended Implementation Order

1. Add repo-safe bootstrap contract with `init` and `--object-id`.
2. Materialize clean scaffold from the current role-assignment template.
3. Extract shared workspace validation helper and route command entry checks through it.
4. Add YAML-driven inference rule loader/evaluator.
5. Wire `apply_cross_field_inferences()` into compiler flow.
6. Add semantic consistency validator and route it through pipeline validators.
7. Update `validate_stage_confidence` source messaging.
8. Update docs and regression tests against verified current baseline.

This order removes the first-user UX failure early while preserving the stronger architectural sequence for CF-2.

## Verification

### Part 1

- `project/intake verify`
- `project/intake demo happy --date 2026-04-02`
- `project/intake demo stress --date 2026-04-02`
- targeted semantic consistency test proving explicit contradiction remains visible

### Part 2

- `project/intake verify`
- `tmpdir=$(mktemp -d)`
- `project/intake init "$tmpdir/Нова_станція" --object-id nova_stantsiia`
- `project/intake generate "$tmpdir/Нова_станція" --date 2026-04-02`
- `project/intake compile "$tmpdir/Нова_станція" --date 2026-04-02`

## Explicit Non-Goals

- no `--force` re-init
- no interactive wizard
- no automatic promotion of inferred values to confirmed evidence
- no preset explosion for archetypes/templates
- no creation of empty `intake/` or `reports/` directories at init time
- no broad redesign of evidence, routing, or external automation

## Acceptance Criteria

This plan is complete when:

- compiler performs deterministic inference for missing / `tbd` targets with full provenance;
- explicit semantic contradictions surface as reviewable findings;
- confidence reporting distinguishes archetype defaults from inferred data;
- inferred values remain assumptions and do not look like confirmed human answers;
- `project/intake init` is the documented first command for a new workspace;
- bootstrap works for a real new-user flow without exemplar copying;
- workspace entry checks are consistent across intake commands;
- regression tests cover both semantic inference and bootstrap behavior;
- docs reflect the new operator entry point and the status of inferred values.

## Closing Note

This final plan does not try to maximize automation for its own sake.

Its purpose is narrower and more defensible:

- make compiler behavior genuinely semantic rather than only normalizing;
- keep policy traceable and reviewable;
- avoid governance drift where inference looks like confirmation;
- remove the first-command UX failure for new workspaces;
- preserve operator clarity while the workflow grows.
