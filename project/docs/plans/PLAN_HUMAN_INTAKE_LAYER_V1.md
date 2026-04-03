# Human-Facing Intake Layer v1

> **ARCHIVAL STATUS:** fulfilled execution plan.  
> `v1` exit condition was satisfied on `2026-04-03`.  
> Current operator guidance lives in `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`.  
> Formal milestone summary lives in `project/docs/reviews/V1_CLOSEOUT_2026-04-03.md`.

**Дата:** 2026-04-02  
**Гілка:** `research/methodology-foundation-clean`  
**Статус:** fulfilled; historical execution record  
**Fulfilled on:** 2026-04-03  
**Superseded prior active plan:** `project/docs/plans/PLAN_HUMAN_INTAKE_LAYER.md`  
**Historical release baseline:** `project/docs/reviews/V0_RELEASE_2026-04-02.md`

## Призначення

Цей документ був активним forward plan для наступної хвилі розвитку human-facing intake layer після формального `v0` release і після materialized `v1` slices:

- `--preserve-responses`
- `preview / baseline_ready`

Він збережений у repo для traceability і показує, у якій послідовності був виконаний `v1`.

План існував для того, щоб:

- зафіксувати точний порядок наступних `v1` slice-ів;
- прибрати двозначність між backlog і execution order;
- задати спільний architectural contract перед новими human-workflow features;
- не допустити scope creep у notifications / external automation / нові intake modes.

## Close-Out Summary

На момент close-out цей план вважається виконаним у повному обсязі.

Підсумковий `v1` baseline включає:

- shared workspace snapshot як один authoritative upstream layer;
- operator-facing `preview`, `review`, і `evidence` поверх спільного snapshot;
- derived review packets і routed reviewer registry;
- advisory evidence status;
- narrow blocking evidence enforcement у `project/intake evidence`;
- deterministic generated artifact index у `reports/workspace.manifest.yaml`;
- останній verify baseline: `project/intake verify` -> `284 passed`.

## Baseline at Plan Start

На цій гілці вже існує executable workflow з такими властивостями:

- `v0` formally released with tag `project-intake-v0`
- canonical operator surface: `project/intake`
- `--preserve-responses` materialized
- `preview / baseline_ready` materialized
- happy-path exemplar: `project/examples/sample_object_01`
- stress-path exemplar: `project/examples/sample_object_02`
- full branch verify after preview slice: `PYTHONPATH=. .venv/bin/python -m pytest project/tests -q` -> `246 passed`

Що лишається незавершеним у `v1`:

- review workflow layer
- deterministic routing from findings to roles / people
- evidence status and later evidence gate

## Architectural Principles

### 1. Canonical source of truth не змінюється

Source of truth і далі живе у:

- `role_assignments.yaml`
- filled intake responses
- compiled `questionnaire.yaml`
- field / value dictionaries
- requirements / pipeline outputs

Жоден новий `v1` slice не створює друге editable source of truth.

### 2. Role-first accountability, person overlay second

- ownership лишається role-based;
- reviewer accountability лишається role-based;
- person mapping є overlay поверх roles;
- якщо `S4` owner і всі reviewers зводяться до однієї людини, потрібен independent second reviewer.

### 3. Один authoritative workspace snapshot contract

Усі наступні `v1` slice-и повинні спиратися на один authoritative `workspace_snapshot` layer.
`preview`, `review` і `evidence` не мають окремо перебудовувати compile / pipeline /
ownership / field-metadata logic.

Snapshot contract повинен:

- мати `schema_version`;
- будуватися один раз на command invocation;
- бути детермінованим за порядком полів, issues і routed items;
- не використовувати persistent cross-run cache у `v1`;
- бути єдиним upstream input для renderer-style reports.

### 4. Generated reports only

Нові `v1` outputs є generated artifacts під `reports/`, а не canonical inputs для ручного редагування.

### 5. Deterministic generated-artifact contract

Кожен новий machine-readable report у `v1` повинен:

- містити `schema_version`;
- мати детермінований порядок списків і records;
- бути discoverable через `reports/workspace.manifest.yaml`;
- бути придатним для safe overwrite при повторній генерації.

### 6. Advisory before blocking

Для evidence layer спершу з'являється advisory status, і лише після стабілізації на exemplars допускається blocking enforcement.

### 7. No external automation in this plan

Цей план не включає:

- email / chat notifications
- external task systems
- workflow bots
- будь-який mutation side effect поза repo artifacts

### 8. Partial diagnostics before command failure

Human-facing commands у цьому плані повинні за можливості писати partial reports
замість раннього exit, якщо workspace data неповна, але structurally valid.

Non-zero exit reserved for:

- malformed inputs;
- unreadable required artifacts;
- broken invariants inside compile / snapshot / render pipeline.

## Revised v1 Order

Замість старого backlog wording:

- reviewer sheets
- evidence enforcement
- validator-to-person automation

цей план затверджує такий execution order:

0. `workspace status snapshot`
1. `review packets`
2. `evidence status` (advisory only)
3. `blocking evidence enforcement` (narrow initial scope)

Примітка:

- старий backlog item `validator-to-person automation` у цьому плані **переформульовано** в deterministic routing inside review packets;
- notifications / integrations лишаються explicitly out of scope.

## Slice 0 — Workspace Status Snapshot

### Ціль

Зібрати один reusable Python layer, який дає цілісний status snapshot для intake workspace і використовується всіма наступними `v1` features.

### Мінімальний Contract

Snapshot повинен містити:

- `schema_version`
- object identity
- compile totals
- unresolved fields by strictness
- owner / reviewer roles
- person resolution from `role_assignments.yaml`
- pipeline issues and blockers
- evidence requirements
- observed evidence signals already present in workspace
- deterministic ordering for fields, issues and routed items

### Recommended Shape

- extract shared module under `project/src/intake/workspace_snapshot.py`
- keep library-first API with pure data builders + thin renderers
- refactor `preview` in this slice to consume the shared snapshot directly
- no standalone public `snapshot` command is required in `v1`
- preferred internal split:
  - `load_workspace_inputs(...)`
  - `build_workspace_snapshot(...)`
  - `render_preview_status(...)`

### Acceptance Criteria

- snapshot is consumable from tests without shelling out
- snapshot correctly resolves `sample_object_01`
- snapshot correctly resolves `sample_object_02`
- unresolved `S4` and pipeline blockers match current preview contract
- `preview` output is generated from the same snapshot contract, not from duplicated logic
- full suite remains green

### Out of Scope

- any user-facing new command
- any mutation of tracked exemplars
- any evidence blocking rule

## Slice 1 — Review Packets

### Ціль

Materialize human-facing review outputs without creating another editable source of truth.

### Key Change vs old idea

Старе формулювання `reviewer sheets` відкидається як надто двозначне. У `v1` потрібні **derived review packets**, а не нові editable spreadsheets.

### Minimum Outputs

- `reports/reviewer_registry.yaml`
- `reports/reviewer_registry.md`
- `reports/review_packet._coordinator.md`
- optional per-person files:
  - `reports/review_packet.<person_id>.md`

### Routing Contract

Each routed item must have a stable identity and deterministic routing outcome:

- `review_item_id` — stable key derived from `object_id + source_kind + source_key + target_role`
- `source_kind` — `field`, `validator_issue`, `evidence_gap`
- `source_key` — `field_id` or stable validator/evidence key
- `priority`
- `next_action`
- `primary_role` / `primary_person`
- `secondary_roles` / `secondary_persons`
- `routing_state`
- `escalation_reason` when no safe direct routing exists

Recommended declarative spec:

- `project/specs/review/validator_routing.yaml`

### Routing Rules

1. field-driven items route via field owner / reviewer contract
2. validator findings first map to explicitly implicated fields
3. if no field mapping exists, use validator-specific fallback owner roles
4. unresolved ownership, reviewer collapse, or ambiguous multi-target routing goes to coordinator

### Required Content

For each routed review item:

- stable `review_item_id`
- source kind / source key
- field id
- current value / status
- strictness
- owner role
- reviewer roles
- resolved owner / reviewer persons
- priority
- next action
- routing state:
  - assigned
  - unassigned owner
  - second reviewer required
  - coordinator escalation
- reason for review:
  - unresolved field
  - pipeline validator finding
  - stage-gate critical field
  - missing evidence

### Operator Surface

Recommended command:

```bash
project/intake review <workspace> [--date YYYY-MM-DD]
```

This command should reuse the shared workspace status snapshot and generate review outputs under `reports/`.

### Acceptance Criteria

- command succeeds on happy-path and stress-path exemplars
- no new canonical input files are introduced
- `_unassigned` / missing role assignments are visible in reports, not only stderr
- `S4` owner-reviewer collapse is represented as `second reviewer required`
- repeated generation for the same workspace yields stable item ordering and stable `review_item_id` values
- coordinator-only items appear in `review_packet._coordinator.md`
- targeted tests cover both assigned and escalation routing

### Out of Scope

- editable reviewer workbooks
- notifications
- changing canonical owner answers from review packets

## Slice 2 — Evidence Status (Advisory)

### Ціль

Make evidence visibility explicit before any blocking enforcement.

### Minimum Outputs

- `reports/evidence_status.yaml`
- `reports/evidence_status.md`

### Minimum Rule

For each selected field, report:

- `evidence_required`
- `evidence_strength`
- `blocking_eligible`
- `review_routing_required`

`evidence_strength` must use an explicit deterministic taxonomy:

- `none`
- `reference_only`
- `structured_ref`
- `workspace_artifact`

Recommended declarative spec:

- `project/specs/evidence/evidence_policy.yaml`

Initial evidence signal may be conservative and use only existing workspace data such as:

- `source_ref`
- non-empty structured references already preserved in compiled responses
- presence of deterministic workspace artifacts explicitly linked from structured refs

### Operator Surface

Recommended command:

```bash
project/intake evidence <workspace> [--date YYYY-MM-DD]
```

This command should consume the shared workspace snapshot and emit only derived reports under `reports/`.

### Rollout Discipline

- start advisory only
- no CLI exit failure because of missing evidence at this slice
- focus first on `S4` and review-relevant fields
- `missing_evidence` may already be exposed as a review reason in review packets

### Acceptance Criteria

- advisory report is generated from exemplars
- missing evidence is surfaced deterministically
- weak or missing evidence does not cause CLI failure at this slice
- zero regression to current compile/preview behavior
- full suite remains green

### Out of Scope

- hard gating
- mandatory evidence registry redesign
- annex-wide evidence expansion

## Slice 3 — Blocking Evidence Enforcement

### Ціль

Add a narrow, explicit evidence gate only after advisory evidence behavior is stable.

### Initial Scope

- selected `S4` fields only
- only when required evidence rule is explicit and tested
- only where signal quality is strong enough to avoid false confidence

### Enforcement Principle

- block on absence of required evidence only for explicitly listed fields
- do not convert advisory evidence status into global blanket failure
- concept-stage warnings alone remain non-blocking unless evidence rule explicitly says otherwise

### Stage Matrix

- `concept`: advisory only
- `basic_design`: advisory only unless an explicit field rule says otherwise and tests prove low false-positive risk
- `detailed_design`: blocking allowed for allowlisted fields with minimum evidence strength
- `build_commission`: blocking allowed for allowlisted fields with minimum evidence strength

### Acceptance Criteria

- exact blocking field set is documented in code and docs
- minimum required evidence strength per blocking field is documented in code and docs
- happy-path exemplar behavior is explicit
- stress-path exemplar behavior is explicit
- at least one dedicated evidence-focused exemplar or targeted fixture exists
- full suite remains green

### Out of Scope

- global evidence gate for all fields
- free-text evidence parsing heuristics
- workflow automation outside repo outputs

## Exemplar Strategy

Current exemplars remain:

- `project/examples/sample_object_01` — happy path
- `project/examples/sample_object_02` — stress path

This plan recommends splitting human-workflow coverage into focused fixtures rather than one overloaded exemplar:

- `project/examples/sample_object_03_review_routing`
- targeted fixtures under `project/tests/fixtures/evidence/`
- optional full-workspace exemplar `project/examples/sample_object_04_evidence_ready` only if fixture coverage is insufficient

Recommended purpose:

- `sample_object_03_review_routing`
  - unassigned owner role
  - `S4` owner/reviewer collapse requiring second reviewer
  - coordinator escalation routing
- `tests/fixtures/evidence/`
  - missing evidence
  - reference-only evidence
  - structured-ref / workspace-artifact positive cases
- `sample_object_04_evidence_ready`
  - end-to-end evidence-positive behavior with pipeline still green

## Artifact Policy

Default rule for new `v1` artifacts:

- generated under `reports/`
- machine-readable + human-readable pair whenever reasonable
- every machine-readable artifact includes `schema_version`
- every generation refreshes `reports/workspace.manifest.yaml`
- excluded from happy-path golden set unless explicitly promoted later
- allowed to overwrite prior generated reports for the same workspace

Tracked-vs-ephemeral rule:

- do not auto-promote new `v1` reports into tracked exemplar set
- exemplar refresh remains explicit and intentional

## Verify Matrix

Every slice in this plan must define:

- targeted tests
- operator smoke command if a new command is introduced
- full branch verify
- fixed-date repeatability check where applicable
- mutation-scope check for canonical inputs vs generated reports

Baseline verify command:

```bash
PYTHONPATH=. .venv/bin/python -m pytest project/tests -q
```

Recommended per-slice smoke style:

```bash
project/intake review project/examples/sample_object_01 --date 2026-04-02
```

or equivalent raw Python command if no operator surface exists yet.

## Explicit Non-Goals

This plan does **not** include:

- notifications
- email delivery
- chat delivery
- task/ticket creation
- methodology expansion unrelated to current workflow execution
- new intake modes
- redefinition of `baseline_ready`
- replacement of role-based accountability with person-based accountability

## Exit Condition for This Plan

This `v1` plan is considered fulfilled when:

- shared workspace status snapshot exists and is reused;
- review packets exist and are operator-usable;
- advisory evidence status exists;
- initial blocking evidence enforcement exists in narrow tested scope;
- full branch verify remains green;
- generated artifact contract remains deterministic and discoverable, and boundaries remain intact.

Status at close-out: satisfied on `2026-04-03`.
