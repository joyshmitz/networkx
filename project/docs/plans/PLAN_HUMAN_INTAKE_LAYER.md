# Plan: Human-Facing Intake Layer

**Дата:** 2026-04-02
**Гілка:** `research/methodology-foundation`
**Статус:** revised (GPT Pro + Codex reviews integrated)
**Залежність:** Wave 2 закритий, pipeline stable (138 tests, 9 validators)

---

## 1. Проблема

Pipeline працює. Але він приймає `questionnaire.yaml` як монолітний YAML. У реальності:

- **4 людини** відповідають за різні секції
- Кожна людина має бачити **тільки свої поля** з підказками, controlled values і strictness
- Заповнення має йти **в певному порядку** (metadata → services → constraints → governance)
- Після заповнення потрібен **merge** у canonical questionnaire.yaml
- Після merge — pipeline run → feedback → iterate

Зараз цього шару немає. Людина мусить відкрити raw YAML з 41 полем і знати що з цього її.

---

## 2. Що вже є (і чого не вистачає)

### Є

| Артефакт | Що дає |
|---|---|
| `questionnaire_v2_fields.yaml` | **Source of truth для field ownership.** 41 поле з purpose, strictness, owner_role, reviewer_roles, allowed_values_ref, selection_rule, unknown_policy |
| `role_views.yaml` | Derived navigation artifact: 12 ролей → owned_fields, owns_sections, reviews_sections. Не є окремим source of truth — має бути узгоджений з fields.yaml |
| `role_assignments.template.yaml` | person → roles mapping template |
| `questionnaire_v2_values.yaml` | controlled vocabularies для всіх enum полів |
| `core_questionnaire_v2.yaml` | section → fields structure |
| `QUESTIONNAIRE_WORKFLOW.md` | stages: kickoff → intake → review → normalize → compile |

### Не вистачає

| Що потрібно | Навіщо |
|---|---|
| **Per-person intake guide + response template** | Кожна з 4 людей отримує свій лист з тільки своїми полями |
| **Intake manifest** | Версіонування, staleness detection, reproducibility |
| **Temporal ordering** | Які поля заповнюються першими, які залежать від інших |
| **Structured response format** | Не просто `field: value`, а status + value + comment + source |
| **Two-stage compile** | responses → intake_compiled.yaml → questionnaire.yaml |
| **Status tracker** | Per-field lifecycle: unanswered / answered / tbd / not_applicable / conflict |
| **Owner/reviewer separation** | Owners answer, reviewers comment — structural, not advisory |

---

## 3. Design Decisions

### D0: Intake bundle is versioned and reproducible

Generator emits `intake_manifest.yaml` з:
- `object_id`, `manifest_id`, `generated_at`
- `field_catalog_hash` (SHA256 of questionnaire_v2_fields.yaml)
- `values_hash` (SHA256 of questionnaire_v2_values.yaml)
- `role_assignments_hash` (SHA256 of role_assignments.yaml)
- `expected_persons` list

Кожен response file включає `manifest_id`. Merge tool **rejects stale or mismatched manifests** перед читанням відповідей. Generation fails fast якщо будь-яке поле resolves до нуля або більше одного owner person.

**Чому:** Якщо fields.yaml або role_assignments.yaml змінюється після генерації sheets, merge з старими sheets дасть семантично неправильний результат. Manifest робить це видимим.

### D1: Формат — Markdown guide cards (read-only) + structured response YAML (fillable)

**Чому не Markdown таблиці:** довгі описи, controlled values з поясненнями і selection rules погано рендеряться в таблицях і дають ugly diffs.

**Чому не Excel:** потрібен version control (git), diff-ability, zero dependencies.

**Два артефакти per person:**
- `generated/{person_id}.guide.md` — read-only guide з field cards
- `responses/{person_id}.response.yaml` — fillable structured response

Response YAML format per field:
```yaml
manifest_id: obj_01-intake-v1
person_id: sample_arch
roles: [ot_architect, network_engineer]
answers:
  wan_required:
    status: answered       # unanswered | answered | tbd | not_applicable
    value: 'yes'
    comment: null
    source_ref: "ТЗ розд. 3.2"
  carrier_diversity_target:
    status: tbd
    value: 'tbd'           # NOT null — explicit string 'tbd' for pipeline compatibility
    comment: "Очікуємо відповідь оператора до 2026-04-15"
    source_ref: null
```

**Normalization rules for questionnaire.yaml:**
- `status: answered` → write `value` as-is
- `status: tbd` → write string `'tbd'` (schema accepts tbd for all enums)
- `status: not_applicable` → write string `'tbd'` + record in intake_compiled.yaml that original status was not_applicable. Schema has no `not_applicable` enum value; downstream validators see `tbd` and flag it per stage-confidence rules.
- `status: unanswered` → **omit field** from questionnaire.yaml (truly missing → eligible for archetype defaults in build_requirements_model)

**Чому:** pipeline's `merge_missing_values_tracked` replaces `None` with archetype defaults but preserves string `'tbd'`. Writing `null` for tbd would cause silent default backfill. Writing `'tbd'` for not_applicable is conservative — validators flag it, compiled snapshot preserves the real intent.

**Чому structured:** дозволяє відрізнити untouched від intentionally tbd, зберігає source/evidence, готовий для reviewer workflow.

### D2: Temporal ordering — 3 UX фази

**Фаза 1 — Identity & Scope** (metadata, object_profile, critical_services)
Заповнює: замовник + технолог. Визначає що це за об'єкт і які сервіси в scope.

**Фаза 2 — Constraints & Architecture** (external_transport, security_access, time_sync, power_environment, resilience)
Заповнює: архітектор + кібербезпека + електрика. Потребує scope з Фази 1.

**Фаза 3 — Operations & Governance** (operations, acceptance_criteria, governance)
Заповнює: експлуатація + PM + замовник. Потребує constraints з Фази 2 для MTTR, FAT/SAT.

**Важливо:** archetype resolution (`resolve_archetype_id`) залежить від полів з Фази 1 (video_required, iiot_required, criticality_class) **і** Фази 2 (poe_budget_class, redundancy_target). Тому повна archetype resolution можлива тільки після Фази 2. Preview pipeline run після Фази 1 використовує preliminary archetype на основі наявних полів — результат позначається як indicative.

3 фази — це UX guidance для людей. Pipeline run можливий на будь-якому етапі через `--mode preview`. Результати стають reliable тільки після Фази 2 (constraints відомі → archetype stable → graphs meaningful).

### D3: Compile — two-stage: responses → compiled → canonical questionnaire

Merge tool **не пише напряму** в questionnaire.yaml. Два кроки:

1. `compiled/intake_compiled.yaml` — повний compiled snapshot з answer objects, provenance, status per field
2. `questionnaire.yaml` — normalized pipeline-compatible artifact (тільки section → field → value)

Compile modes:
- `--mode preview` — дозволяє unanswered/tbd поля, pipeline може дати indicative results. compile_intake НЕ перевіряє stage gates — це робить pipeline's `validate_stage_confidence`. Якщо `project_stage: detailed_design` + є tbd поля, pipeline все одно видасть errors через stage-confidence validator.
- `--mode baseline_ready` — compile_intake перевіряє **перед** pipeline run:
  - Всі S4 поля мають бути `answered` (не tbd/unanswered)
  - Всі S3/S4 поля мають `source_ref`
  - Жодних `unanswered` полів (tbd допускається для S1/S2)
  - Missing reviewer sign-off на S3/S4 → warning

**Alignment з pipeline:** compile modes — це pre-flight check. Вони не дублюють stage-confidence validator, а доповнюють його. Pipeline's validator перевіряє stage × evidence_maturity × tbd_count runtime. Compile mode перевіряє intake completeness + evidence coverage before pipeline навіть запускається.

**Чому two-stage:** canonical questionnaire не має містити workflow metadata (status, comments, source). Compiled snapshot зберігає все для audit trail.

### D4: Owner/reviewer separation — structural

Owners отримують editable response packs. Reviewers отримують окремі review checklists.

- `responses/{person_id}.response.yaml` — owner values (authoritative)
- `reviews/{person_id}.review.yaml` — reviewer comments/sign-off (advisory)

Merge tool:
- **Hard error** якщо non-owner supplies value для поля
- Reviewer artifacts можуть додавати `review_status` і `review_comment`, але не `value`
- S3/S4 fields: missing review blocks `baseline_ready` але не блокує `preview`

**Чому:** якщо reviewer поля є в тому ж editable файлі що й owner поля — люди будуть редагувати чуже. Warning після факту — слабкий control. Structural separation — правильний.

### D5: Evidence/source first-class, tied to strictness

Кожен answer object має `source_ref`. Правила:
- S3/S4 fields: `source_ref` required для `baseline_ready`
- S1/S2 fields: `source_ref` recommended
- `tbd` / `unanswered` status: `comment` required (причина і хто уточнює)

**Чому:** для industrial methodology evidence — не cosmetic. Потрібно знати чи відповідь з vendor docs, site survey, corporate standard, чи engineering estimate.

### D6: Status model — field lifecycle

| Status | Значення |
|---|---|
| `unanswered` | Template згенерований, відповіді немає |
| `answered` | Owner дав значення |
| `tbd` | Owner explicitly позначив як невирішене |
| `not_applicable` | Поле не стосується цього об'єкта |
| `conflict` | Кілька owners дали різні значення (merge error) |

Deferred statuses (додаються з відповідними features):
- `prefilled_unconfirmed` — коли додамо prefill з archetype/prior station
- `blocked` — коли додамо field-level dependencies
- `needs_review` — коли додамо reviewer sign-off enforcement

### D7: Object-scoped workspace

Filesystem layout per object, не flat:

```
objects/{object_id}/
  role_assignments.yaml
  intake/
    intake_manifest.yaml
    generated/
      {person_id}.guide.md
    responses/
      {person_id}.response.yaml
    reviews/
      {person_id}.review.yaml
  compiled/
    intake_compiled.yaml
  questionnaire.yaml
  reports/
    intake_status.yaml
    intake_status.md
    requirements.compiled.yaml
    graphs.summary.yaml
    validation.summary.yaml
    ...
```

**Чому:** навіть без multi-object coordination, flat layout `intake/person_1.yaml` стає хаосом при 3 станціях, кількох ітераціях і regenerated sheets.

---

## 4. Архітектура

```
questionnaire_v2_fields.yaml  (ownership source of truth)
questionnaire_v2_values.yaml
core_questionnaire_v2.yaml
role_assignments.yaml
         │
         ▼
generate_intake_sheets.py
  ├──► intake_manifest.yaml
  ├──► generated/{person}.guide.md     (read-only, human)
  ├──► responses/{person}.response.yaml (fillable, structured)
  └──► reviews/{person}.review.yaml    (reviewer comment-only)
         │
         ▼ (people fill response files, reviewers add comments)
         │
compile_intake.py
  reads: responses/{person}.response.yaml
         reviews/{person}.review.yaml (optional)
         intake_manifest.yaml
  ├──► compiled/intake_compiled.yaml   (full snapshot + provenance)
  ├──► reports/intake_status.yaml      (machine-readable coverage)
  ├──► reports/intake_status.md        (human-readable dashboard)
  └──► questionnaire.yaml             (normalized, pipeline-compatible)
         │
         ▼
run_pipeline.py questionnaire.yaml
  ├──► reports/ (requirements, graphs, validation)
  └──► feedback → iterate
```

---

## 5. Файли для створення

### Нові скрипти

| Файл | Призначення | Inputs | Outputs |
|---|---|---|---|
| `src/intake/generate_intake_sheets.py` | Генерує manifest + per-person guide cards + response templates + review templates | role_assignments, fields, values | manifest, guides, response templates, review templates |
| `src/intake/compile_intake.py` | Збирає responses у compiled snapshot + normalized questionnaire | response files, manifest | intake_compiled.yaml, questionnaire.yaml, intake_status |

### Нові тести

| Файл | Що тестує |
|---|---|
| `tests/test_generate_intake.py` | Correct fields per person, values included, phases shown, manifest hashes, ownership uniqueness, reviewer fields separate |
| `tests/test_compile_intake.py` | Happy path merge, gaps detection, conflict detection, tbd handling, stale manifest rejection, non-owner value rejection, mode preview vs baseline_ready |

### Нові sample артефакти

| Файл | Що це |
|---|---|
| `examples/sample_object_01/intake/` | Згенеровані intake sheets + sample filled responses |

---

## 6. Деталі реалізації

### 6.1 generate_intake_sheets.py

**Input:** path to object workspace (directory з role_assignments.yaml)

**Logic:**
1. Load role_assignments → person_to_roles mapping (union duplicate person_ids)
2. Load questionnaire_v2_fields → field metadata. **Source of truth for ownership** — не role_views
3. Build person → owned_fields mapping: for each field, find owner_role → find person with that role
4. Ownership validation:
   - If field has >1 owner person → **fail fast** (ambiguous ownership)
   - If field has 0 owner persons → **warning** + field goes into `_unassigned_fields` section in manifest
   - Generator still produces intake sheets for assigned fields. Unassigned fields are listed in manifest and intake_status as coverage gaps.
   - This is consistent with how the existing role_assignments validator already reports unassigned roles as warnings, not errors (validate_role_assignments.py:73-80).
   - **Sample compatibility:** sample_object_01 role_assignments has no process_engineer or iiot_engineer → fields like telemetry_required, control_required, iiot_required are unassigned → listed in manifest, not blocking generation.
5. Load questionnaire_v2_values → value descriptions
6. Load core_questionnaire_v2 → section structure
7. Compute manifest hashes (SHA256 of fields, values, role_assignments content)
8. Write `intake_manifest.yaml`
9. For each person:
   a. Collect owned_fields
   b. Collect reviewer_fields (fields where their roles ∈ reviewer_roles)
   c. Group by section, sort by phase
   d. Write `generated/{person_id}.guide.md` — Markdown field cards
   e. Write `responses/{person_id}.response.yaml` — structured template з `status: unanswered`
   f. Write `reviews/{person_id}.review.yaml` — reviewer checklist template

**Guide card format:**

```markdown
## Фаза 1: Identity & Scope

### staffing_model — Модель кадрового забезпечення

- **Секція:** object_profile
- **Strictness:** S2
- **Навіщо:** Визначає чи об'єкт має постійний персонал, що впливає на OOB, MTTR, remote access
- **Допустимі значення:**
  - `local_ops` — постійний локальний персонал
  - `remote_ops` — керування лише дистанційно
  - `hybrid_ops` — комбінована модель
  - `tbd` — ще не визначено
- **Правило вибору:** Якщо персонал є лише на рівні чергового → remote_ops
- **Якщо невідомо:** Допускається tbd до baseline_ready, потрібен коментар з причиною
- **Джерело/підстава:** required для S3/S4; recommended для S1/S2
- **Рецензенти:** ot_architect
```

### 6.2 compile_intake.py

**Input:** path to object workspace, `--mode preview|baseline_ready`

**Logic:**
1. Load `intake_manifest.yaml`, verify hashes match current spec files
2. Load all `responses/{person_id}.response.yaml`
3. Verify each response has matching `manifest_id`
4. For each field:
   a. Find owner response → extract answer
   b. If non-owner supplied value → **hard error**
   c. If multiple owners answered → **conflict**
   d. Record status: answered / tbd / unanswered / not_applicable
5. If `--mode baseline_ready`:
   a. S4 fields must be `answered` (not tbd/unanswered)
   b. S3/S4 fields must have `source_ref`
   c. Missing reviewer sign-off on S3/S4 → warning
6. Load reviewer files (optional), attach review_status/comments to compiled output
7. Write `compiled/intake_compiled.yaml` — full snapshot
8. Write `questionnaire.yaml` — normalized (section → field → value only)
9. Write `reports/intake_status.yaml` + `reports/intake_status.md`

**intake_status.yaml format:**
```yaml
total_fields: 41
answered: 28
tbd: 8
unanswered: 3
not_applicable: 2
conflicts: 0
mode: preview
per_person:
  sample_arch: {owned: 14, answered: 10, tbd: 3, unanswered: 1}
  sample_ops_sec: {owned: 12, answered: 8, tbd: 3, unanswered: 1}
phase_readiness:
  phase_1: complete
  phase_2: partial (3 tbd)
  phase_3: incomplete (2 unanswered)
```

### 6.3 Temporal phases

```yaml
phase_1_identity_scope:
  sections: [metadata, object_profile, critical_services]
  owners: [project_manager, object_owner, operations_engineer, process_engineer, video_engineer, iiot_engineer]
  gate: "scope defined — services and identity known, preliminary archetype possible"
  note: "full archetype resolution requires phase 2 fields (poe_budget_class, redundancy_target)"

phase_2_constraints_architecture:
  sections: [external_transport, security_access, time_sync, power_environment, resilience]
  owners: [network_engineer, cybersecurity_engineer, telemetry_engineer, cabinet_power_engineer, ot_architect, operations_engineer]
  depends_on: phase_1
  gate: "constraints fixed — graphs can be compiled meaningfully"

phase_3_operations_governance:
  sections: [operations, acceptance_criteria, governance]
  owners: [operations_engineer, commissioning_engineer, project_manager, object_owner]
  depends_on: phase_2
  gate: "operations and acceptance defined — baseline_ready possible"
  note: "object_owner owns acceptance_evidence_class in acceptance_criteria"
```

---

## 7. Порядок імплементації

| # | Що | Залежності | Тести |
|---|---|---|---|
| 1 | `generate_intake_sheets.py` — manifest + guide cards | specs files | test: manifest hashes, correct fields per person, phases shown |
| 2 | `generate_intake_sheets.py` — response + review templates | step 1 | test: valid YAML, structured answer objects, reviewer separation |
| 3 | `compile_intake.py` — happy path compile | step 2 | test: produces valid questionnaire, intake_compiled, intake_status |
| 4 | `compile_intake.py` — validation: stale manifest, ownership, conflicts | step 3 | test: rejects stale, rejects non-owner values, flags conflicts |
| 5 | `compile_intake.py` — mode preview vs baseline_ready | step 4 | test: preview allows tbd, baseline_ready blocks S4 tbd |
| 6 | Generate sample intake for sample_object_01 | steps 1-2 | manual verification |
| 7 | End-to-end: generate → fill → compile → pipeline | steps 1-5 | test: intake flow produces valid pipeline run |

---

## 8. Що НЕ входить у цей план (deferred)

| Feature | Коли |
|---|---|
| Web UI / forms | Не потрібно для 3 об'єктів |
| Excel generation | Може бути пізніше, MD first |
| Annex-specific intake sheets | Після core intake працює |
| Multi-object coordination | Wave 3+ |
| Prefill from archetype / prior station | Після першого об'єкту пройшов intake |
| Validator-driven follow-up sheets (delta per person) | Після compile_intake stable |
| Field-level dependency graph (depends_on per field) | Якщо section-level phases виявляться замало |
| Automated notifications | Не потрібно для 4 людей |

---

## 9. Success criteria

1. Для sample_object_01 генеруються per-person guide cards + response templates + review templates
2. Кожна людина бачить тільки свої owned поля з повним контекстом
3. Owner/reviewer файли структурно розділені
4. Manifest з hashes забезпечує reproducibility
5. Compile tool збирає responses у questionnaire.yaml
6. Preview mode дозволяє pipeline run з tbd полями
7. Baseline_ready mode блокує якщо S4 fields unresolved
8. Gaps, conflicts, per-person coverage видно в intake_status
9. Pipeline приймає compiled questionnaire і дає validation output

---

## 10. Ризики

| Ризик | Mitigation |
|---|---|
| Поля без owner_role → field resolves до 0 persons | Generator warns + lists in manifest as unassigned (not fail-fast — compatible with incomplete role_assignments) |
| Поле з owner_role assigned до 2+ persons | Generator fails fast |
| Specs змінились після generation | Manifest hash mismatch → compile rejects |
| Non-owner edits value | Compile hard error |
| YAML formatting errors від ручного редагування | Compile validates YAML parsing per file |
| Людям незручно редагувати YAML | Guide cards для читання, response YAML має minimal structure |
| Review workflow ігнорується | Baseline_ready mode blocks without S3/S4 review |

---

## 11. GPT Pro Review Integration Log

### Прийнято повністю (wholeheartedly agree)

1. **Intake manifest + versioning** (change #1) — hash-based staleness detection, fail-fast on ownership gaps
2. **Field cards замість таблиць** (change #2) — tables are the wrong abstraction for rich field metadata
3. **Structured response YAML** (change #2) — status/value/comment/source_ref per field
4. **Owner/reviewer separation** (change #4) — structural, not advisory; hard error for non-owner values
5. **Object-scoped workspace** (change #9) — low cost, prevents flat layout chaos
6. **Evidence first-class** (change #6) — source_ref tied to strictness; required for S3/S4

### Прийнято частково (somewhat agree)

7. **Two-stage compile** (change #5) — intake_compiled.yaml as intermediate. Прийнято, але compile modes обмежені до preview/baseline_ready (без додаткових modes).
8. **Expanded status model** (change #10) — 5 statuses для v1 (unanswered, answered, tbd, not_applicable, conflict). Решта (blocked, prefilled_unconfirmed, stale_template, needs_review, missing_source, invalid) додаються з features що їх потребують.
9. **Field dependency graph** (change #3) — section-level phases достатні для 41 поля. Per-field depends_on deferred. Якщо phases виявляться грубими — додамо.

### Відкладено (agree but defer)

10. **Prefill from archetype/prior station** (change #7) — потрібно спочатку пройти перший intake без prefill, зібрати feedback
11. **Validator-driven follow-up sheets** (change #8) — потрібен field_id у validator outputs (partially є), defer until compile_intake stable
12. **Property-based tests for merge determinism** (change #10) — додамо після basic test coverage

### Відхилено

Нічого не відхилено. Всі 10 changes прийняті повністю або частково/deferred.

---

## 12. Codex Review Integration Log

5 findings від Codex, всі адресовані:

1. **P1: tbd/not_applicable normalization** — `status: tbd` → write `'tbd'` string (not null). `status: not_applicable` → write `'tbd'` string + record real status in compiled snapshot. `status: unanswered` → omit field (eligible for archetype defaults). Prevents silent backfill and schema failures.

2. **P1: Phase 1 gate misleading** — Gate text corrected. Archetype resolution depends on phase 2 fields (poe_budget_class, redundancy_target). Phase 1 preview gives preliminary archetype only. Full resolution after phase 2.

3. **P1: preview/baseline_ready vs stage-confidence** — Compile modes are pre-flight checks, not replacements for pipeline validators. Stage-confidence validator runs regardless of compile mode. Documented that later-stage objects with tbd fields will fail in pipeline even in preview mode.

4. **P2: object_owner in phase 3** — Added to phase 3 owners list. Owns acceptance_evidence_class in acceptance_criteria.

5. **P2: Fail-fast breaks sample** — Changed from fail-fast to warning for 0-owner fields. Unassigned fields listed in manifest and intake_status. Compatible with sample_object_01 which has no process_engineer/iiot_engineer.
