# Plan: Human-Facing Intake Layer

**Дата:** 2026-04-02
**Гілка:** `research/methodology-foundation`
**Статус:** final (GPT Pro + Codex + self-review integrated)
**Залежність:** Wave 2 закритий, pipeline stable (138 tests, 9 validators)

---

## 0. Boundary Principles

### Принцип 1 — Методологічна межа

> Опитувальний лист має бути достатньо строгим, щоб не лишати місця двозначності, і достатньо легким, щоб не змушувати респондентів відповідати на питання, які належать уже до етапу технічного проєктування та конфігурування.

| Належить questionnaire (вимоги) | Належить design phase (рішення) |
|---|---|
| "Потрібен зовнішній канал? Так/Ні" | "Скільки VLAN? Який routing?" |
| "Який клас резервування? N+1" | "RSTP чи PRP? Active/standby?" |
| "Потрібне зонування? DMZ?" | "Які конкретні firewall rules?" |
| "Потрібен PTP? Так" | "Який PTP profile? Boundary clock?" |
| "Потрібне PoE? Medium budget" | "Який switch model? Скільки портів PoE++?" |

Questionnaire збирає **що потрібно**, pipeline визначає **як реалізувати**.

### Принцип 2 — Операційна простота

> v0 має бути настільки простим, щоб координатор міг пояснити workflow за 5 хвилин: "Ось твій Excel, заповни, поверни мені, я запущу перевірку."

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

| Що потрібно | v0 | v1 |
|---|---|---|
| Per-person Excel з dropdowns | Так | Так |
| Markdown guide cards (reference) | Так | Так |
| Compile Excel → questionnaire.yaml | Так | Так |
| intake_status.yaml/md | Так | Так |
| Derived .response.yaml для git diff | Так | Так |
| Intake manifest з hash checking | Ні | Так |
| Reviewer .review.xlsx | Ні | Якщо потрібно |
| intake_compiled.yaml intermediate | Ні | Так |
| Evidence enforcement | Ні | Так |
| --mode preview/baseline_ready | Ні (завжди preview) | Так |
| Validator → person feedback mapping | Ручний | Автоматичний |

---

## 3. Design Decisions

### D1: Формат — Excel primary з descriptive dropdowns

**Чому Excel:** dropdown validation для controlled values (неможливо ввести невалідне), кольорове маркування strictness, offline, zero learning curve. 60-70% промислових проєктів використовують Excel для multi-stakeholder intake.

**Три артефакти per person:**
- `responses/{person_id}.xlsx` — **primary fillable artifact** з dropdowns
- `generated/{person_id}.guide.md` — read-only reference guide з field cards
- `responses/{person_id}.response.yaml` — derived від Excel при compile (для git diff)

**Три рівні видимості описів значень:**

**Рівень 1 — Dropdown (момент вибору).** Показує код + коротку назву:
```
segmented — керована сегментація
dmz_centric — DMZ між OT і зовнішнім
strict_isolation — повна ізоляція зон
flat — без сегментації
tbd — ще не визначено
```
Compile парсить все до ` — ` і бере тільки код.

**Рівень 2 — Cell comment (hover після вибору).** Повний опис + selection rule:
```
segmented — Зони OT, MGMT та сервісні сегменти розділені
  керованими правилами. Спільна фізична інфраструктура допускається.

Обирайте якщо: об'єкт має кілька сервісів але не потребує
  фізичної ізоляції від зовнішніх систем.

Впливає на: zone model, firewall intent, addressing framework
```

**Рівень 3 — Reference sheet.** Повна таблиця всіх значень всіх полів з descriptions, selection rules, design impact. Locked, read-only.

**Excel sheet structure:**

| Колонка | Зміст | Editable? |
|---|---|---|
| A: Field ID | `wan_required` | Ні (locked) |
| B: Питання | "Потрібен зовнішній транспорт" | Ні (locked) |
| C: Strictness | `S4` | Ні (locked, кольорове: S4=червоне, S3=помаранчеве, S2=жовте, S1=сіре) |
| D: Фаза | `2` | Ні (locked) |
| E: Значення | dropdown з descriptive labels | **Так** |
| F: Статус | dropdown: tbd / not_applicable / *(порожнє)* | **Так, але зазвичай порожнє** |
| G: Коментар | free text | **Так** |
| H: Джерело | free text (source_ref) | **Так** |

**Column E по типу поля:**
- `enum` fields → data validation dropdown з descriptive labels (code — опис) + `tbd — ще не визначено`
- `string` fields (object_id, object_name) → free text, input message показує purpose
- `integer` fields (growth_horizon_months) → whole number validation (min 0), no dropdown

**Status auto-derivation (compile-time):**
- value filled + status empty → `answered`
- value empty + status `tbd` → `tbd`
- value empty + status `not_applicable` → `not_applicable`
- value empty + status empty → `unanswered`
- value filled + status `tbd` → **warning** (суперечність)

### D2: Temporal ordering — 3 UX фази

**Фаза 1 — Identity & Scope** (metadata, object_profile, critical_services)
Заповнює: замовник + технолог. Визначає що це за об'єкт і які сервіси в scope.

**Фаза 2 — Constraints & Architecture** (external_transport, security_access, time_sync, power_environment, resilience)
Заповнює: архітектор + кібербезпека + електрика. Потребує scope з Фази 1.

**Фаза 3 — Operations & Governance** (operations, acceptance_criteria, governance)
Заповнює: експлуатація + PM + замовник. Потребує constraints з Фази 2.

**Inter-phase handoff:** після збирання Фази 1, координатор запускає compile у preview mode. intake_status.md показує scope summary (object_type, criticality, enabled services). Цей summary розсилається разом з Фазою 2 Excel файлами як context.

**Archetype note:** `resolve_archetype_id` залежить від полів Фази 1 (video_required, iiot_required, criticality_class) **і** Фази 2 (poe_budget_class, redundancy_target). Preview після Фази 1 дає preliminary archetype. Повна resolution — після Фази 2.

### D3: Compile — Excel → questionnaire.yaml

**v0:** compile пише напряму в questionnaire.yaml + intake_status. Просто і зрозуміло.

**v1 (після feedback):** додається intake_compiled.yaml як intermediate snapshot з answer objects, provenance, status per field — для audit trail і evidence review. Compile modes preview/baseline_ready. Evidence enforcement для S3/S4.

**Normalization rules (Excel → questionnaire.yaml):**
- `status: answered` (auto-derived) → write parsed value code as-is
- `status: tbd` → write string `'tbd'` (schema accepts tbd for all enums)
- `status: not_applicable` → write string `'tbd'` + record real status in intake_status
- `status: unanswered` → **omit field** (truly missing → eligible for archetype defaults)

### D4: Owner/reviewer separation

**v0:** Owner xlsx contains only owned fields. Ownership enforced structurally — each person's file has only their fields. Review happens via pipeline output inspection + verbal confirmation. Realistic for 4 people.

**v1 (if needed):** Reviewer .review.xlsx with comment/sign-off fields. Review_status integrated into baseline_ready gate.

### D5: Object workspace layout

Consistent з existing `examples/` convention:

```
examples/{object_id}/
  role_assignments.yaml            ← already exists for samples
  intake/
    generated/
      {person_id}.guide.md
    responses/
      {person_id}.xlsx             ← primary fillable
      {person_id}.response.yaml    ← derived at compile, for git diff
  questionnaire.yaml               ← compiled output
  reports/
    intake_status.yaml
    intake_status.md
    requirements.compiled.yaml     ← pipeline outputs
    graphs.summary.yaml
    validation.summary.yaml
    ...
```

---

## 4. Архітектура (v0)

```
questionnaire_v2_fields.yaml  (ownership source of truth)
questionnaire_v2_values.yaml
core_questionnaire_v2.yaml
role_assignments.yaml
         │
         ▼
generate_intake_sheets.py examples/{object_id}/
  ├──► intake/generated/{person}.guide.md       (read-only reference)
  └──► intake/responses/{person}.xlsx            (primary: dropdowns + comments + colors)
         │
         ▼ (people fill .xlsx files)
         │
compile_intake.py examples/{object_id}/
  ├──► intake/responses/{person}.response.yaml   (derived from xlsx, for git diff)
  ├──► reports/intake_status.yaml                 (machine-readable coverage)
  ├──► reports/intake_status.md                   (human-readable dashboard)
  └──► questionnaire.yaml                        (normalized, pipeline-compatible)
         │
         ▼
run_pipeline.py examples/{object_id}/questionnaire.yaml
  ├──► reports/ (requirements, graphs, validation)
  └──► feedback → iterate (cross-ref errors with intake_status ownership table)
```

**Dependency:** `openpyxl` for Excel generation and parsing.

---

## 5. Файли для створення (v0)

### Скрипти

| Файл | Призначення |
|---|---|
| `src/intake/generate_intake_sheets.py` | Генерує per-person .xlsx з descriptive dropdowns, cell comments, strictness colors + guide.md |
| `src/intake/compile_intake.py` | Парсить .xlsx → questionnaire.yaml + intake_status + derived .response.yaml |

### Тести

| Файл | Що тестує |
|---|---|
| `tests/test_generate_intake.py` | Correct fields per person, dropdowns have descriptive labels, cell comments present, strictness colors, field types (enum/string/integer), unassigned fields warning |
| `tests/test_compile_intake.py` | Excel parsing, status auto-derivation, happy path merge, gaps, conflicts, normalization rules, derived YAML correctness |

### CLI usage

```bash
# Step 1: Generate intake sheets for an object
python src/intake/generate_intake_sheets.py examples/station_alpha/

# Step 2: After people fill .xlsx files, compile into questionnaire
python src/intake/compile_intake.py examples/station_alpha/

# Step 3: Run pipeline on compiled questionnaire
python src/run_pipeline.py examples/station_alpha/questionnaire.yaml
```

Координатор виконує всі 3 кроки. Люди заповнюють тільки .xlsx.

---

## 6. Деталі реалізації

### 6.1 generate_intake_sheets.py

**Input:** path to object workspace (directory з role_assignments.yaml)

**Logic:**
1. Load role_assignments → person_to_roles mapping (union duplicate person_ids)
2. Load questionnaire_v2_fields → field metadata. **Source of truth for ownership**
3. Build person → owned_fields: for each field, find owner_role → find person with that role
4. Ownership validation:
   - >1 owner person → **fail fast**
   - 0 owner persons → **warning**, field listed as unassigned in intake_status
5. Load questionnaire_v2_values → value descriptions for dropdowns and comments
6. Load core_questionnaire_v2 → section → fields mapping for phase grouping
7. For each person:
   a. Collect owned_fields, group by section, sort by phase
   b. Write `responses/{person_id}.xlsx`:
      - Sheet `intake`: fields table з locked metadata columns + editable value/status/comment/source
      - Column E: data validation from named range on `_values` sheet (descriptive labels)
      - Cell comments on column E: full description + selection_rule + design_impact
      - Conditional formatting: row background by strictness
      - Column F: data validation `tbd / not_applicable` (usually left empty)
      - Sheet `_values`: all enum value lists as named ranges (code — description format)
      - Sheet `_reference`: full value dictionary table (locked)
   c. Write `generated/{person_id}.guide.md`: Markdown field cards for deep context

**Dropdown label format:** `{code} — {label_uk}`
Example: `segmented — керована сегментація`

**Cell comment format:**
```
{label_uk}

{value_1_code} — {value_1_description}
{value_2_code} — {value_2_description}
...

Правило вибору: {selection_rule}
Впливає на: {design_impact}
```

### 6.2 compile_intake.py

**Input:** path to object workspace

**Logic:**
1. Load all `intake/responses/{person_id}.xlsx` — parse `intake` sheet (openpyxl)
2. For each row: extract field_id (col A), raw_value (col E), status (col F), comment (col G), source (col H)
3. Parse value: if raw_value contains ` — `, take everything before it as code
4. Auto-derive status:
   - value present + status empty → `answered`
   - value empty + status `tbd` → `tbd`
   - value empty + status `not_applicable` → `not_applicable`
   - value empty + status empty → `unanswered`
   - value present + status `tbd` → **warning** logged
5. Build field → answer mapping across all persons
6. Validate: field answered by >1 person → conflict error
7. Normalize into questionnaire.yaml sections:
   - `answered` → write value
   - `tbd` → write `'tbd'`
   - `not_applicable` → write `'tbd'` (record real status in intake_status)
   - `unanswered` → omit (eligible for archetype defaults)
8. Write derived `intake/responses/{person_id}.response.yaml` (for git diff)
9. Write `questionnaire.yaml`
10. Write `reports/intake_status.yaml` + `reports/intake_status.md`

**intake_status.md format:**
```markdown
# Intake Status — {object_id}

Answered: 28/41 (68%) | TBD: 8 | Unanswered: 3 | N/A: 2

## Scope Summary (Phase 1)
- Object type: generation
- Criticality: high
- Services: telemetry, control, video

## Per Person
| Person | Roles | Owned | Answered | TBD | Unanswered |
|--------|-------|-------|----------|-----|------------|
| arch_01 | ot_architect, network_engineer | 14 | 10 | 3 | 1 |
| ...

## Phase Readiness
- Phase 1 (Identity): complete
- Phase 2 (Constraints): partial — 3 tbd
- Phase 3 (Operations): incomplete — 2 unanswered

## Unassigned Fields
- telemetry_required (owner_role: process_engineer — no person assigned)

## Field Ownership Table (for error cross-reference)
| Field | Owner Person | Status | Value |
|-------|-------------|--------|-------|
| wan_required | arch_01 | answered | yes |
| redundancy_target | arch_01 | answered | none |
| ...
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

### v0 — minimum viable (до першого реального intake)

| # | Що | Тести |
|---|---|---|
| 1 | `generate_intake_sheets.py` — per-person .xlsx з descriptive dropdowns + cell comments + strictness colors | correct fields per person, dropdowns match values with descriptions, cell comments present, field types handled |
| 2 | `generate_intake_sheets.py` — guide.md generation | guide has all owned fields with full context |
| 3 | `compile_intake.py` — parse xlsx → questionnaire.yaml + intake_status | happy path, status auto-derivation, gaps, normalization rules |
| 4 | `compile_intake.py` — conflict detection + derived .response.yaml | conflicts flagged, derived yaml matches excel |
| 5 | e2e: generate → fill sample → compile → pipeline | pipeline accepts compiled output, validation runs |

### v1 — після feedback від першого реального intake

| # | Що |
|---|---|
| 6 | Manifest hashing + stale rejection |
| 7 | Reviewer .review.xlsx separation |
| 8 | intake_compiled.yaml intermediate з evidence tracking |
| 9 | --mode preview vs baseline_ready з source_ref enforcement |
| 10 | Automated validator → person feedback mapping |
| 11 | --preserve-responses for regeneration after spec changes |

---

## 8. Що НЕ входить (deferred)

| Feature | Коли |
|---|---|
| Web UI / forms | Не потрібно для 3 об'єктів |
| Annex-specific intake sheets | Після core intake працює |
| Multi-object coordination | Wave 3+ |
| Prefill from archetype / prior station | Після першого об'єкту пройшов intake |
| Field-level dependency graph | Якщо section-level phases замало |
| Automated notifications | Не потрібно для 4 людей |

---

## 9. Success criteria (v0)

1. Для sample_object_01 генеруються per-person .xlsx з descriptive dropdowns + guide.md
2. Dropdowns показують `code — опис` для кожного значення
3. Cell comments містять повний опис + selection rule + design impact
4. Strictness кольорово маркований (S4 червоне → S1 сіре)
5. Кожна людина бачить тільки свої owned поля
6. String/integer поля мають правильний тип validation замість dropdown
7. Compile збирає .xlsx → questionnaire.yaml з правильною normalization
8. Status auto-derived: filled value = answered, explicit tbd/not_applicable потрібно тільки коли нема значення
9. intake_status.md показує coverage, phase readiness, ownership table
10. Pipeline приймає compiled questionnaire і дає validation output

---

## 10. Ризики

| Ризик | Mitigation |
|---|---|
| Поля без owner_role → 0 persons | Warning + listed as unassigned (not fail-fast) |
| Поле assigned до 2+ persons | Fail fast |
| Excel auto-format (yes→TRUE, dates) | All value cells as Text format; compile validates against allowed values |
| .xlsx corrupted або saved as .xls | Compile checks file format |
| .xlsx is binary in git | Derived .response.yaml is the diffable artifact |
| Someone edits .response.yaml directly | Overwritten on every compile from .xlsx |
| Dropdown label parsing fails | Compile falls back to full cell value if no ` — ` separator |
| Specs change after partial fill | v0: regenerate + re-fill. v1: --preserve-responses carries forward matching fields |

---

## 11. Review Integration Log

### GPT Pro (10 revisions)

Прийнято: manifest versioning, field cards, structured responses, owner/reviewer separation, object-scoped workspace, evidence first-class. Partially: two-stage compile, expanded statuses, field dependencies. Deferred: prefill, follow-up sheets, property-based tests.

### Codex CLI (5 findings)

Fixed: tbd/not_applicable normalization, phase 1 gate (archetype needs phase 2), preview/baseline_ready alignment, object_owner in phase 3, fail-fast breaks sample.

### Self-review (7 changes)

Integrated: auto-derive status, field type handling (enum/string/integer), cell comments over sheet switching, Excel-specific risks, stale "MD first" removed, D4 xlsx refs, regeneration story.

### Discussion outcomes

- Excel chosen as primary format (research: industrial lingua franca)
- CSV rejected (awkward middle ground: no validation, no dropdowns)
- v0/v1 split: build minimum → real data → feedback → add features
- Boundary principle: questionnaire = requirements, not design decisions
- Three-level value descriptions: dropdown labels → cell comments → reference sheet
