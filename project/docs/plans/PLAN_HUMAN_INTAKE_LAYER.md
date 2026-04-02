# Plan: Human-Facing Intake Layer

**Дата:** 2026-04-02
**Гілка:** `research/methodology-foundation`
**Статус:** locked for v0 implementation (6 review rounds: GPT Pro + Codex CLI + 4x self-review)
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

---

## 2. Що вже є (і чого не вистачає)

### Є

| Артефакт | Що дає |
|---|---|
| `questionnaire_v2_fields.yaml` | **Source of truth для field ownership.** 41 поле з purpose, strictness, owner_role, reviewer_roles, allowed_values_ref, selection_rule, unknown_policy |
| `questionnaire_v2_values.yaml` | controlled vocabularies. 24 dictionaries, всі ≤227 chars (inline dropdown safe) |
| `core_questionnaire_v2.yaml` | section → fields structure (field_id → section_id mapping) |
| `role_views.yaml` | Derived navigation artifact (не source of truth) |
| `role_assignments.template.yaml` | person → roles mapping template |

### v0 scope

| Що | В scope | Deferred (v1) |
|---|---|---|
| Per-person Excel з descriptive dropdowns | Так | |
| Markdown guide cards (reference) | Так | |
| Compile Excel → questionnaire.yaml | Так | |
| intake_status.yaml/md з ownership table | Так | |
| Derived .response.yaml для git diff | Так | |
| Unassigned fields → `_unassigned.xlsx` | Так | |
| Manifest hash checking | | Так |
| Reviewer .review.xlsx | | Так |
| intake_compiled.yaml intermediate | | Так |
| Evidence enforcement | | Так |
| --mode preview/baseline_ready | | Так |
| Automated validator → person mapping | | Так |
| --preserve-responses for regen | | Так |

---

## 3. Design Decisions

### D1: Excel primary з descriptive dropdowns

**Чому Excel:** dropdown validation (неможливо ввести невалідне), кольорове маркування strictness, offline, zero learning curve. Inline lists достатні — жоден dictionary не перевищує 255 символів.

**Артефакти per person:**
- `intake/responses/{person_id}.xlsx` — **primary fillable**
- `intake/generated/{person_id}.guide.md` — read-only reference
- `intake/responses/{person_id}.response.yaml` — derived at compile (git diff)

**Unassigned fields:** поля без assigned person (process_engineer, iiot_engineer у sample_object_01) → `intake/responses/_unassigned.xlsx`. Координатор заповнює або делегує. Запобігає silent omission критичних полів.

**Три рівні видимості описів значень:**

**Рівень 1 — Dropdown.** Код + коротка назва:
```
segmented — керована сегментація
dmz_centric — DMZ між OT і зовнішнім
strict_isolation — повна ізоляція зон
flat — без сегментації
tbd — ще не визначено
```
Compile парсить все до ` — ` і бере тільки код.

**Рівень 2 — Cell comment (hover).** Повний опис + selection rule:
```
segmented — Зони OT, MGMT та сервісні сегменти розділені
  керованими правилами. Спільна фізична інфраструктура допускається.

Обирайте якщо: об'єкт має кілька сервісів але не потребує
  фізичної ізоляції від зовнішніх систем.

Впливає на: zone model, firewall intent, addressing framework
```

**Рівень 3 — Reference sheet.** Повна таблиця всіх значень з descriptions, selection rules, design impact. Locked, read-only.

**Excel layout:**

```
Row 1: [merged] "Intake Sheet — {person_label_uk} ({object_id})"
Row 2: "Ролі: {roles}  |  Дата генерації: {date}"
Row 3: "Заповніть колонку E. Якщо невідомо — оберіть tbd у колонці F."
Row 4: "Детальний опис полів: intake/generated/{person_id}.guide.md"
Row 5: (empty separator)
Row 6: header row (frozen)
Row 7+: data rows
```

| Колонка | Зміст | Editable? |
|---|---|---|
| A: Field ID | `wan_required` | Ні (locked) |
| B: Питання | "Потрібен зовнішній транспорт" | Ні (locked) |
| C: Strictness | `S4` | Ні (locked, кольорове: S4=червоне, S3=помаранчеве, S2=жовте, S1=сіре) |
| D: Фаза | `2` | Ні (locked) |
| E: Значення | dropdown (inline list) | **Так** |
| F: Статус | dropdown: tbd / not_applicable | **Так, зазвичай порожнє** |
| G: Коментар | free text | **Так** |
| H: Джерело | free text | **Так** |

Column widths: A=20, B=45, C=8, D=6, E=40, F=18, G=35, H=30.

**Column E по типу поля:**
- `enum` (38 полів) → inline data validation з descriptive labels + `tbd`
- `string` (object_id, object_name — 2 поля) → free text, input message shows purpose
- `integer` (growth_horizon_months — 1 поле) → whole number validation (min 0)

**Status auto-derivation (compile-time):**
- value filled + status empty → `answered`
- value empty + status `tbd` → `tbd`
- value empty + status `not_applicable` → `not_applicable`
- value empty + status empty → `unanswered`
- value filled + status `tbd` → **warning**

### D2: Temporal ordering — 3 UX фази

**Фаза 1 — Identity & Scope** (metadata, object_profile, critical_services)
Заповнює: замовник + технолог.

**Фаза 2 — Constraints & Architecture** (external_transport, security_access, time_sync, power_environment, resilience)
Заповнює: архітектор + кібербезпека + електрика.

**Фаза 3 — Operations & Governance** (operations, acceptance_criteria, governance)
Заповнює: експлуатація + PM + замовник.

**Паралелізм:** фази — рекомендований порядок, не жорсткий gate. Координатор може роздати Phase 2 xlsx якщо Phase 1 scope вже зрозумілий. Жорсткий gate тільки один: baseline_ready (v1) потребує всі 3 фази complete.

**Inter-phase handoff:** після Phase 1 координатор запускає compile. intake_status.md показує scope summary. Summary розсилається з Phase 2 xlsx як context.

**Archetype note:** `resolve_archetype_id` залежить від Фази 1 (video_required, iiot_required, criticality_class) **і** Фази 2 (poe_budget_class, redundancy_target). Preview після Фази 1 дає preliminary archetype. Повна resolution після Фази 2.

### D3: Compile — Excel → questionnaire.yaml

**v0:** compile пише напряму questionnaire.yaml + intake_status. Просто.

**Normalization (Excel → questionnaire.yaml):**
- Emit `version: '0.2.0'` at top
- `answered` → write parsed value code
- `tbd` → write string `'tbd'`
- `not_applicable` → write `'tbd'` + record real status in intake_status
- `unanswered` → omit field (eligible for archetype defaults)
- Emit `known_unknowns: {}` (section without intake fields)
- Validate parsed code against allowed values from values.yaml → error on invalid

**Section reconstruction:** compile loads `core_questionnaire_v2.yaml` для field_id → section_id mapping. Fields від різних persons зібрані в одну section (e.g., metadata from project_manager + object_owner).

### D4: Ownership

**v0:** кожен xlsx містить тільки owned поля. Ownership enforced structurally. Review — verbal/pipeline output inspection.

### D5: Workspace layout

Consistent з existing `examples/`:

```
examples/{object_id}/
  role_assignments.yaml
  intake/
    generated/
      {person_id}.guide.md
    responses/
      {person_id}.xlsx
      {person_id}.response.yaml    ← derived at compile
      _unassigned.xlsx             ← fields without assigned person
  questionnaire.yaml               ← compiled output
  reports/
    intake_status.yaml
    intake_status.md
    requirements.compiled.yaml     ← pipeline outputs
    ...
```

---

## 4. Архітектура (v0)

```
questionnaire_v2_fields.yaml  (field ownership source of truth)
questionnaire_v2_values.yaml  (controlled vocabularies, all ≤255 chars)
core_questionnaire_v2.yaml    (field → section mapping)
role_assignments.yaml         (person → roles)
         │
         ▼
generate_intake_sheets.py examples/{object_id}/
  ├──► intake/generated/{person}.guide.md
  ├──► intake/responses/{person}.xlsx
  └──► intake/responses/_unassigned.xlsx        (if any unassigned fields)
         │
         ▼ (people fill .xlsx)
         │
compile_intake.py examples/{object_id}/
  ├──► intake/responses/{person}.response.yaml  (derived, git-diffable)
  ├──► reports/intake_status.yaml
  ├──► reports/intake_status.md
  └──► questionnaire.yaml                      (pipeline-compatible)
         │
         ▼
run_pipeline.py examples/{object_id}/questionnaire.yaml
  ├──► reports/ (requirements, graphs, validation)
  └──► feedback → iterate (cross-ref with intake_status ownership table)
```

**Dependency:** `openpyxl`

**CLI:**
```bash
# Generate
python src/intake/generate_intake_sheets.py examples/station_alpha/

# Compile
python src/intake/compile_intake.py examples/station_alpha/

# Pipeline
python src/run_pipeline.py examples/station_alpha/questionnaire.yaml
```

Координатор виконує всі 3 кроки. Люди заповнюють тільки .xlsx.

---

## 5. Файли

### Скрипти

| Файл | Призначення |
|---|---|
| `src/intake/generate_intake_sheets.py` | Per-person .xlsx (dropdowns, comments, colors) + guide.md + _unassigned.xlsx |
| `src/intake/compile_intake.py` | Parse .xlsx → questionnaire.yaml + intake_status + derived .response.yaml |

### Тести

| Файл | Що тестує |
|---|---|
| `tests/test_generate_intake.py` | Fields per person, dropdown labels, cell comments, strictness colors, field types, unassigned xlsx |
| `tests/test_compile_intake.py` | Excel parsing, status auto-derivation, multi-person section assembly, gaps, conflicts, value validation, normalization, version/known_unknowns emit |

---

## 6. Деталі реалізації

### 6.1 generate_intake_sheets.py

**Input:** object workspace path

**Logic:**
1. Load role_assignments → person_to_roles (union duplicate person_ids)
2. Load questionnaire_v2_fields → field metadata (**ownership source of truth**)
3. Build person → owned_fields: field.owner_role → find person with that role
4. Ownership validation:
   - field >1 owner person → **fail fast**
   - field 0 owner persons → **warning** + add to unassigned list
5. Load questionnaire_v2_values → value dictionaries
6. Load core_questionnaire_v2 → section structure, build field→section + field→phase mapping
7. For each person:
   a. Collect owned_fields, group by section, sort by phase
   b. Write `intake/responses/{person_id}.xlsx`:
      - Title/instruction rows (rows 1-5)
      - Header row 6 (frozen)
      - Data rows 7+: field_id, label_uk, strictness, phase, value, status, comment, source_ref
      - Column E: inline data validation with descriptive labels (`code — label_uk`)
      - Column E cell comments: full value descriptions + selection_rule + design_impact
      - Column F: inline data validation `tbd / not_applicable`
      - Conditional formatting: row fill by strictness (S4=red, S3=orange, S2=yellow, S1=grey)
      - Columns A-D: locked (sheet protection with unlocked E-H)
      - All cells: Text number format (prevents Excel auto-format of yes→TRUE)
      - Sheet `_reference`: full value dictionary (locked)
   c. Write `intake/generated/{person_id}.guide.md`
8. If unassigned fields exist: write `intake/responses/_unassigned.xlsx` (same format)

### 6.2 compile_intake.py

**Input:** object workspace path

**Logic:**
1. Load core_questionnaire_v2 → build field_id → section_id mapping
2. Load questionnaire_v2_fields → allowed_values_ref per field
3. Load questionnaire_v2_values → allowed codes per dictionary
4. Find all .xlsx in `intake/responses/` (including _unassigned.xlsx)
5. For each xlsx: parse `intake` sheet (skip rows 1-5, header row 6, data from row 7)
6. For each data row:
   a. Extract field_id (A), raw_value (E), status (F), comment (G), source_ref (H)
   b. Parse value: if contains ` — ` → take prefix as code; else use full value
   c. Validate code against allowed values → **error** on invalid
   d. Auto-derive status from value + status columns
7. Build global field → {value, status, comment, source_ref, person_id} mapping
8. Validate: field answered by >1 person → **conflict error**
9. Write `intake/responses/{person_id}.response.yaml` per person (derived)
10. Reconstruct questionnaire.yaml:
    - `version: '0.2.0'`
    - For each section in core_questionnaire_v2 order:
      - For each field in section: emit value per normalization rules
    - `known_unknowns: {}`
11. Write `reports/intake_status.yaml` + `reports/intake_status.md`

**intake_status.md:**
```markdown
# Intake Status — {object_id}

Answered: 28/41 (68%) | TBD: 8 | Unanswered: 3 | N/A: 2

## Scope Summary
- Object type: generation
- Criticality: high
- Services: telemetry, control, video

## Per Person
| Person | Roles | Owned | Answered | TBD | Unanswered |
|--------|-------|-------|----------|-----|------------|
| arch_01 | ot_architect, network_engineer | 14 | 10 | 3 | 1 |

## Phase Readiness
- Phase 1 (Identity): complete
- Phase 2 (Constraints): partial — 3 tbd
- Phase 3 (Operations): incomplete — 2 unanswered

## Unassigned Fields
- telemetry_required (owner_role: process_engineer)

## Field Ownership Table
| Field | Section | Owner Person | Status | Value |
|-------|---------|-------------|--------|-------|
| wan_required | external_transport | arch_01 | answered | yes |
```

### 6.3 Phase mapping

```yaml
phase_1: [metadata, object_profile, critical_services]
phase_2: [external_transport, security_access, time_sync, power_environment, resilience]
phase_3: [operations, acceptance_criteria, governance]
```

---

## 7. Порядок імплементації (v0)

| # | Що | Тести |
|---|---|---|
| 1 | generate: manifest-free Excel з dropdowns + comments + colors | fields per person, dropdowns, comments, colors, field types |
| 2 | generate: guide.md + _unassigned.xlsx | guide content, unassigned fields present |
| 3 | compile: parse xlsx → questionnaire.yaml | happy path, normalization, version/known_unknowns, section reconstruction |
| 4 | compile: validation + status + derived yaml | status auto-derivation, value validation, conflicts, multi-person sections, derived yaml |
| 5 | e2e: generate → fill → compile → pipeline | compiled output accepted by pipeline, validation runs |

---

## 8. Success criteria (v0)

1. Per-person .xlsx з descriptive dropdowns + cell comments + strictness colors
2. Dropdown: `code — опис` для кожного значення; cell comment: повний опис + selection rule
3. String/integer поля правильний тип validation
4. Unassigned fields → `_unassigned.xlsx`
5. Excel title row з person name, object_id, instruction, guide path
6. Compile: .xlsx → questionnaire.yaml з правильною section reconstruction
7. Status auto-derived від value presence
8. Value validation against controlled vocabulary
9. intake_status.md: coverage, phases, ownership table
10. Pipeline приймає compiled output

---

## 9. Ризики

| Ризик | Mitigation |
|---|---|
| 0 owner persons | Warning + _unassigned.xlsx |
| >1 owner person | Fail fast |
| Excel auto-format (yes→TRUE) | Text number format on all cells; compile validates against allowed values |
| .xlsx corrupted / wrong format | Compile checks openpyxl load |
| .xlsx binary in git | Derived .response.yaml is diffable |
| Dropdown label parse fails | Fallback to full cell value; validate against allowed set |
| Specs change after fill | v0: regenerate + re-fill. v1: --preserve-responses |
| Multi-person section | Compile merges fields by field→section mapping |

---

## 10. Review Log

6 rounds: GPT Pro (10 revisions) + Codex CLI (5 findings) + 4x self-review.

Key decisions from reviews:
- v0/v1 split (build minimum, add after real feedback)
- Excel primary (industrial lingua franca, 60-70% adoption)
- CSV rejected (no validation, no dropdowns)
- Inline lists sufficient (all dictionaries ≤255 chars)
- Named ranges / _values sheet not needed for v0
- Boundary principle: questionnaire = requirements, not design
- Three-level descriptions: dropdown → comment → reference sheet
- Auto-derive status (no double-entry)
- Unassigned fields → _unassigned.xlsx (not silently omitted)
- Section reconstruction via core_questionnaire_v2 field→section mapping
- Phases are guidance, not hard gates (parallel OK)
- Reviewer xlsx deferred (verbal review sufficient for 4 people)
