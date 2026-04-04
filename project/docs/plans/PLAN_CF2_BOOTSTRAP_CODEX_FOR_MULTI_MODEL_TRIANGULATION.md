# Codex for multi-model-triangulation — Revised Plan: Close Remaining Critical/High Architecture Findings

> **ARCHIVAL STATUS:** superseded triangulation draft.  
> Active execution plan now lives in `project/docs/plans/PLAN_CF2_BOOTSTRAP_FINAL.md`.  
> This document remains in the repo as model-specific review/input traceability.

**Дата:** 2026-04-04  
**Автор:** Codex  
**Статус:** archived; superseded by `project/docs/plans/PLAN_CF2_BOOTSTRAP_FINAL.md`  
**Призначення:** revised execution plan для `multi-model-triangulation` / cross-model review context  
**Scope:** закриття двох залишкових архітектурних зон після `v1` closeout:

- `CF-2`: compiler lacks cross-field semantic inference
- bootstrap / init gap у human-facing intake workflow

## Context

Після `v1` closeout у methodology/intake layer лишаються дві зони, які все ще мають архітектурний борг:

| Finding | Severity | Current State |
| --- | --- | --- |
| `CF-2`: compiler lacks cross-field semantic inference | CRITICAL | archetype defaults і bool normalization уже існують, але semantic inference / contradiction layer ще немає |
| Bootstrap / init gap | HIGH | `project/intake generate` усе ще очікує вже ініціалізований workspace |

Цей revised plan робить чотири важливі корекції до попереднього варіанту:

- inference лишається корисним для pipeline, але не видається за confirmed human input;
- explicit contradictions опрацьовуються окремо, а не ховаються всередині inference;
- rule logic стає traceable і YAML-first;
- bootstrap стає реальним productized entry point замість неявного workaround.

## Design Principles

- Explicit questionnaire answers ніколи не перезаписуються inference logic.
- Inferred values можуть покращувати pipeline usability, але не підвищують evidence maturity самі по собі.
- Business policy повинна жити в YAML specs там, де це практично можливо; Python лишається execution layer.
- CLI contract повинен чітко відділяти одноразову ініціалізацію від повторної регенерації.

---

## Part 1: Cross-Field Inference and Semantic Consistency (`CF-2`)

## Why

Поточний compiler already вміє:

- визначати questionnaire version;
- резолвити archetype;
- підставляти archetype defaults для missing / empty fields;
- нормалізувати bool-like values.

Але він усе ще не вміє дві ключові речі:

1. **deterministic gap filling**
   - коли target field усе ще `tbd` або missing, але cross-field evidence already робить правильне значення однозначним;

2. **semantic contradiction detection**
   - коли людина explicitly відповіла щось, що суперечить сильному cross-field signal.

Обидва механізми потрібні. Перший належить compiler layer. Другий повинен бути окремим consistency layer, який видно у validators / review.

## Scope

Ця частина додає дві пов'язані, але різні можливості:

1. **Inference layer**
   - заповнює тільки `tbd` / missing targets;
   - записує повний provenance;
   - може змінювати downstream graph compilation і validator input.

2. **Consistency layer**
   - не перезаписує explicit answers;
   - створює findings, коли explicit answers конфліктують із strong cross-field expectations.

## Architecture

Compiler flow стає таким:

`detect_version -> load_archetypes -> resolve_archetype -> apply_archetype_defaults -> apply_cross_field_inferences -> normalize_boolish_enums -> return`

Validation лишається outside compiler:

`build_requirements_model -> validate_requirements_model -> compile_graphs -> validators`

Ключова зміна: `apply_cross_field_inferences()` не повинен мутувати вхідний словник in-place як implicit side effect. Він повинен повертати:

- updated normalized requirements
- inference events
- contradiction events, якщо вони виявлені на цьому ж semantic layer

Це зберігає compiler більш чистим і спрощує testability.

## Rule Representation

Не зберігати business rules як Python lambdas. Додати YAML rule catalog:

`project/specs/inference/cross_field_rules.yaml`

Кожний rule record повинен містити:

- `rule_id`
- `mode`: `infer_if_tbd` або `flag_if_conflicts`
- `when`
- `target_section`
- `target_field`
- `inferred_value` для inference rules
- `reason`
- optional `source_fields`

Python layer тримає лише невеликий evaluator registry для операторів на кшталт:

- `eq`
- `in`
- `is_yes`
- `all_of`
- `any_of`

Це краще відповідає YAML-first architecture цього repo і дає нормальну traceability для policy review.

## Inference Semantics

Inference rules firing contract:

- rule спрацьовує тільки тоді, коли target missing або `tbd`;
- explicit human answer ніколи не перезаписується;
- inferred value записується з повним provenance;
- inferred value може піти в graph compiler і validators;
- inferred value не вважається confirmed questionnaire answer.

Кожний inference event повинен зберігати щонайменше:

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

## Execution Model

Не hardcode-ити “2 passes”.

Замість цього:

- deterministic rule order;
- bounded fixpoint loop;
- rerun until no new inferences fire;
- `max_passes=4`;
- fail fast, якщо дві rules намагаються inferred different values для того самого target.

Це надійніше, ніж special-case second pass, і краще масштабується, якщо rule set виросте.

## Initial Rule Set

Початковий rule set може покривати ті самі практичні domain relationships, але з чітким поділом між inference і contradiction handling.

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

Мета стартового contradiction set не в повному coverage, а в тому, щоб зробити видимими найнебезпечніші semantic conflicts.

## Stage Confidence Changes

`validate_stage_confidence.py` повинен перестати змішувати archetype defaults та inferred values в одну безлику категорію assumptions.

Потрібно розвести щонайменше:

- `archetype_default_count`
- `inference_count`

Reporting rules:

- concept / basic design messaging може показувати обидві категорії;
- detailed design / build commission не повинні вважати inferred fields “підтвердженими”;
- inferred fields мають лишатися review-required доти, доки вони не стали explicit або не були waived.

Це закриває головний governance risk: inference не повинен штучно робити workspace зрілішим, ніж він є насправді.

## Current Sample Impact

Попередній draft мав factual drift щодо `sample_object_02`.

Поточна repo reality:

- `sample_object_02` зараз має `7` compiled `tbd` fields;
- на цьому sample реально firing only remote-OOB inference;
- warning count повинен впасти на `1`, а не на `2`;
- `stage_confidence` warning про `tbd` fields лишається, бо `tbd_count` усе ще вище threshold.

Отже, test impact потрібно рахувати від поточного baseline, а не від історичного припущення.

## Tests

Додати `project/tests/test_inference_rules.py` з таким coverage:

- кожне inference rule firing only на missing / `tbd`;
- explicit values never overridden;
- fixpoint execution deterministic;
- conflicting inference raises clear error;
- explicit contradictions surface as validator findings;
- repeated runs idempotent і byte-stable.

Оновити `project/tests/test_pipeline_e2e.py` так, щоб assertions відображали current baseline counts.

## Files to Modify

- `project/src/compiler/build_requirements_model.py`
- `project/src/validators/validate_stage_confidence.py`
- `project/src/run_pipeline.py`
- `project/tests/test_pipeline_e2e.py`

## New Files

- `project/src/validators/validate_semantic_consistency.py`
- `project/tests/test_inference_rules.py`
- `project/specs/inference/cross_field_rules.yaml`

---

## Part 2: Bootstrap / Init Command

## Why

Нові користувачі все ще природно запускають:

`project/intake generate <workspace>`

і впираються в bootstrap failure, бо workspace directory і `role_assignments.yaml` already повинні існувати.

Це не docs polish issue. Це product entry-point gap.

## CLI Contract

Додати:

`project/intake init <workspace> [--object-id <id>]`

Призначення:

- `init` — one-time bootstrap command;
- `generate` — regenerate role-based workbooks всередині вже initialized workspace.

## Behavior

`init` повинен:

1. резолвити `object_id` із `--object-id` або fallback до `basename(workspace_path)`;
2. валідовувати `object_id` regex-ом `^[a-z][a-z0-9_-]{1,63}$`;
3. дозволяти path, який не існує, або порожній каталог;
4. відмовлятись, якщо `role_assignments.yaml` already exists;
5. materialize-ити `role_assignments.yaml` із template;
6. явно записувати top-level `object_id`;
7. друкувати короткий next-step message.

Ключова зміна відносно попереднього draft:

- валідовується machine identifier, а не human workspace folder name;
- це дозволяє friendly / Cyrillic directory names, якщо `--object-id` explicit.

## Template Materialization

Не робити blind copy поточного template з demo assignees.

Rendered bootstrap file повинен:

- зберегти template metadata та rules;
- вставити top-level `object_id`;
- замінити demo `assignments` на clean scaffold або clearly TODO-marked starter block.

Інакше новий operator легко отримає workbooks для `pm_01` / `arch_01` / `ops_01`, що є слабким UX.

## Shared Error Handling

Уніфікувати workspace entry checks для:

- `generate`
- `compile`
- `preview`
- `review`
- `evidence`

Потрібно cleanly розрізняти:

- workspace path missing;
- path exists, but is not a directory;
- workspace exists, but `role_assignments.yaml` missing.

`generate` у таких випадках повинен прямо підказувати:

`project/intake init <workspace>`

## Tests

Додати `project/tests/test_init_workspace.py` з таким покриттям:

- happy path;
- already initialized workspace -> clear error;
- empty directory -> success;
- invalid `object_id` -> clear error;
- `--object-id` works with non-ASCII workspace path;
- `init -> generate -> compile` smoke path works in temp workspace.

## Files to Modify

- `project/intake`
- `project/src/intake/generate_intake_sheets.py`
- shared workspace validation helper, якщо винесення спростить reuse
- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`
- `project/README.md`

## New Files

- `project/src/intake/init_workspace.py`
- `project/tests/test_init_workspace.py`

---

## Verification

### Part 1

- `project/intake verify`
- `project/intake demo happy --date 2026-04-02`
- `project/intake demo stress --date 2026-04-02`
- targeted contradiction test: `sample_object_02` still emits timing conflict until explicit fix

### Part 2

- `project/intake verify`
- `tmpdir=$(mktemp -d)`
- `project/intake init "$tmpdir/Нова_станція" --object-id nova_stantsiia`
- `project/intake generate "$tmpdir/Нова_станція" --date 2026-04-02`
- `project/intake compile "$tmpdir/Нова_станція" --date 2026-04-02`

---

## Explicit Non-Goals

- no `--force` re-init
- no interactive prompts
- no archetype/template preset explosion
- no creation of empty `intake/` or `reports/` at init time
- no automatic promotion of inferred values to confirmed evidence

---

## Acceptance Criteria

Цей plan вважається завершеним, коли:

- compiler вміє deterministic inference для missing / `tbd` fields з повним provenance;
- explicit contradictions стають reviewable findings;
- confidence / stage messaging distinguish defaults from inferred data;
- inferred fields не masquerade as confirmed answers;
- `project/intake init` стає documented first command for a new workspace;
- bootstrap працює для real new-user flow без exemplar copying;
- regression suite покриває і semantic inference, і bootstrap entry behavior.

## Closing Note

Цей revised plan свідомо не намагається “розумно автоматизувати все”.

Його задача вужча і практичніша:

- зробити compiler справді semantic, а не лише normalization layer;
- не дозволити inference підмінити confirmed human data;
- прибрати перший UX failure у new workspace onboarding;
- зберегти traceability і operator clarity для подальшого multi-model review.
