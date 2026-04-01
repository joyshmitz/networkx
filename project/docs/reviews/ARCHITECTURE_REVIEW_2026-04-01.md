# Architecture / Methodology Review — Skeleton "Network Volume"

**Дата:** 2026-04-01
**Гілка:** `research/methodology-foundation`
**Рев'юер:** Claude (за запитом)

---

## 1. CRITICAL FINDINGS

### CF-1: v2 questionnaire повністю orphaned — нічого в pipeline його не споживає

**Severity: CRITICAL**
**Де:** `specs/questionnaire/core_questionnaire_v2.yaml`, `specs/dictionary/questionnaire_v2_fields.yaml`, `specs/dictionary/questionnaire_v2_values.yaml` vs весь `src/`

Весь Python pipeline (`build_requirements_model.py`, `compile_graphs.py`, validators, reports) працює проти **v1** структури. Schema `object_requirements.schema.yaml` описує v1 поля (booleans замість enums, `[concept, basis, design, implementation, as_built]` замість v2 `[concept, basic_design, detailed_design, build_commission]`, 3 значення `criticality_class` замість 4).

v2 questionnaire, v2 fields, v2 values, role_views, implementation_mapping — це все **мертвий YAML**, який ніхто не парсить і не валідує.

**Чому небезпечно:** Ви будуєте методологію вперед, а machine-readable pipeline відстає. Це класична пастка: documentation-driven design, де документація красива, а рантайм працює на іншій моделі. Коли прийде час реально запустити end-to-end, весь v2 доведеться інтегрувати з нуля.

**Що робити:** Або видалити v1 повністю і переробити schema/pipeline під v2, або зафіксувати explicit migration plan з чеклістом файлів.

---

### CF-2: `build_requirements_model` — це passthrough, а не compiler

**Severity: CRITICAL**
**Де:** `src/compiler/build_requirements_model.py:31-51`

Функція `build_requirements_model()` — це буквально 11 рядків `.get()` з questionnaire payload в requirements model. Жодної нормалізації, жодного inference, жодного archetype resolution, жодного constraint check, жодного enrichment. Слово "compiler" у назві каталогу — misleading.

**Чому небезпечно:** Це створює ілюзію, що між questionnaire і requirements model є transformation layer. Насправді requirements model === questionnaire payload. Це означає, що будь-яка некоректність у questionnaire проходить далі без фільтрації.

**Що робити:** Або чесно назвати це `passthrough` і зафіксувати, що нормалізація — TODO, або визначити хоча б 3-5 реальних normalization rules (archetype → defaults, criticality → minimum resilience, staffing_model → OOB expectations).

---

### CF-3: Graph compilation — це порожні заглушки без аналітичної цінності

**Severity: CRITICAL**
**Де:** `src/compiler/compile_graphs.py`

- `compile_physical_graph` — створює один node з object_id. Це не topology.
- `compile_logical_graph` — створює один node зі строкою zone_model. Це не zone graph.
- `compile_failure_domain_graph` — створює один node зі строкою redundancy_target. Це не failure-domain model.
- `compile_service_graph` — створює ізольовані nodes без edges. Сервіси не зв'язані з інфраструктурою.
- `compile_interface_graph` — єдиний, що створює edges, але вони generic (`network_volume -> service_name`).

**Чому небезпечно:** NetworkX тут не є analysis engine. Він є порожнім контейнером для label-ів. Жоден алгоритм NetworkX (connectivity, shortest path, cut vertices, biconnected components) не може працювати на одному node. Це pseudocode, не skeleton.

**Що робити:** Визначити мінімальну graph seed logic. Наприклад: physical graph має seed від archetype (access switches, uplinks, core). Без цього NetworkX — мертва залежність.

---

### CF-4: Валідатори перевіряють лише "чи граф порожній"

**Severity: HIGH**
**Де:** всі `src/validators/validate_*.py`

- `validate_connectivity`: "Physical graph is empty" — це не connectivity check.
- `validate_segmentation`: "Logical graph has no zone model nodes" — це не segmentation check.
- `validate_resilience`: "Failure-domain graph is empty" — не resilience check.
- `validate_power_ports`: перевіряє лише `poe_required && !power_source_model`.
- `validate_time`: перевіряє лише `timing_required && !sync_protocol`.

`constraints_hard.yaml` і `constraints_soft.yaml` мають `expression: TBD` для всіх constraint-ів. Валідатори не імплементують жодного з них.

**Що робити:** Або чесно позначити весь `validators/` як stub, або імплементувати хоча б один нетривіальний constraint (наприклад: `if redundancy_target == no_spof && carrier_diversity_target == single_path_allowed → ERROR`).

---

### CF-5: Конфлікти ownership у role_views.yaml — порушення принципу "one field, one owner"

**Severity: HIGH**
**Де:** `specs/questionnaire/role_views.yaml`

Кілька ролей claim ownership на ті самі поля:
- `telemetry_required`: owned by `process_engineer` (line 34) **і** `telemetry_engineer` (line 103)
- `control_required`: owned by `process_engineer` (line 35) **і** `telemetry_engineer` (line 104)
- `timing_required`: owned by `process_engineer` (line 36) **і** `telemetry_engineer` (line 105)
- `sync_protocol`: owned by `network_engineer` (line 56) **і** `telemetry_engineer` (line 106)
- `poe_required` + `poe_budget_class`: owned by `cabinet_power_engineer` (lines 89-90) **і** `video_engineer` (lines 122-123)
- `fat_required` + `sat_required` + `acceptance_evidence_class`: owned by `object_owner` (lines 18-19) **і** `commissioning_engineer` (lines 165-167)
- `security_access` section: `owns_sections` by `network_engineer` (line 46) **і** `cybersecurity_engineer` (line 66)

**Чому небезпечно:** HUMAN_INTERACTION_MODEL.md декларує "one field, one meaning, one owner" — але role_views.yaml порушує це. В реальному workflow це призведе до конфліктів: хто вирішує, якщо process_engineer і telemetry_engineer дали різне значення `telemetry_required`?

**Що робити:** Для кожного поля залишити одного owner. Другу роль зробити reviewer. У v2_fields.yaml owner_role вже визначений — role_views.yaml має бути strictly derived від нього, а не суперечити йому.

---

### CF-6: Schema не відповідає v2 — enum drift і type drift

**Severity: HIGH**
**Де:** `specs/requirements/object_requirements.schema.yaml`

| Аспект | Schema (v1) | v2 Dictionary |
|---|---|---|
| `criticality_class` | `[low, medium, high]` | `[low, medium, high, mission_critical]` |
| `project_stage` | `[concept, basis, design, implementation, as_built]` | `[concept, basic_design, detailed_design, build_commission]` |
| `redundancy_target` | `[none, n_plus_1, no_spof]` | 5 значень: `+uplink_backup, +active_node_backup` |
| `security_zone_model` | `[flat, segmented, strict_isolation]` | `+dmz_centric` |
| Boolean fields | `type: boolean` | v2 використовує `enum yes_no_tbd` |
| `object_profile` section | відсутня | існує в v2 |
| `acceptance_criteria` | `acceptance_rules: array` | v2 має 3 окремі поля |

**Що робити:** Створити `object_requirements_v2.schema.yaml` строго від v2 dictionary.

---

### CF-7: Annexes — second-class citizens

**Severity: MEDIUM-HIGH**
**Де:** `specs/questionnaire/annex_*.yaml`

Усі 4 annexes (cctv, iiot, time, ha) — це по 4 bare field names без жодного field contract: без `strictness`, `owner_role`, `reviewer_roles`, `unknown_policy`, `evidence_required`, `design_impact`, `downstream_impact`, `allowed_values_ref`.

Core v2 fields мають повний 15-атрибутний контракт. Annex fields — просто список строк. Це означає, що annex fields не можуть пройти через той самий validation / ownership / traceability pipeline.

**Що робити:** Або піднести annex fields до того ж field contract що і core, або explicitly зафіксувати, що annexes мають relaxed contract і чому.

---

### CF-8: implementation_mapping.yaml покриває лише 12 з ~30 v2 полів

**Severity: MEDIUM-HIGH**
**Де:** `specs/mappings/implementation_mapping.yaml`

Відсутні маппінги для: `staffing_model`, `growth_horizon_months`, `control_required`, `local_archiving_required`, `transport_separation_policy`, `remote_access_profile`, `contractor_access_policy`, `audit_logging_required`, `timing_required`, `timing_accuracy_class`, `cabinet_constraint_class`, `environmental_constraint_class`, `poe_required`, `degraded_mode_profile`, `mttr_target_class`, `common_cause_separation_required`, `maintenance_window_model`, `operations_handoff_required`, `asbuilt_package_required`, `fat_required`, `sat_required`, `acceptance_evidence_class`, `evidence_maturity_class`, `waiver_policy_class`.

**Чому небезпечно:** 60%+ полів не мають downstream traceability. Ті поля збираються, але нікуди формально не потрапляють. Це значить, що заповнення їх людьми — марна робота поки mapping не завершений.

---

### CF-9: `generate_handoff_matrix.py` ігнорує DATA_HANDOFF_MATRIX.md і implementation_mapping.yaml

**Severity: MEDIUM**
**Де:** `src/reports/generate_handoff_matrix.py`

Hardcoded 5 consumers з boolean check. Не використовує ні `implementation_mapping.yaml`, ні exchange contract з `DATA_HANDOFF_MATRIX.md`. Не генерує handoff_id, format, version_rule, trace_to_requirements — нічого з того, що методологія вимагає.

---

### CF-10: Import error у `generate_handoff_matrix.py`

**Severity: LOW (but blocking)**
**Де:** `src/reports/generate_handoff_matrix.py:3`

Використовується `dict[str, Any]` у type hint на line 3, але `Any` не імпортований. `from typing import Any` відсутній. Код впаде при виконанні (якщо Python < 3.10 і без `from __future__ import annotations`).

---

## 2. ARCHITECTURE REVIEW

### Що вийшло сильно

1. **Boundary discipline у methodology docs** — чітке розмежування: questionnaire збирає, network volume синтезує, downstream packs деталізують. Ця трирівнева архітектура правильна.

2. **v2 field contract** — 15-атрибутна структура (purpose, strictness, owner_role, reviewer_roles, selection_rule, interpretation_rule, unknown_policy, evidence_required, design_impact, downstream_impact) — це серйозна production-grade специфікація поля. Краще за 90% industrial intake forms.

3. **Unknown policy model** — `forbidden / allowed_with_waiver / allowed_until_stage_gate / informational_only` + strictness levels S1-S4 — це зріла governance модель.

4. **v2 controlled vocabulary** (questionnaire_v2_values.yaml) — dictionaries чисті, selection rules конкретні, meaning однозначний. Немає overlap між значеннями одного dictionary (за винятком `site_specific` catch-all у кількох місцях).

5. **Stage-gated workflow** — 5 stages від `intake_open` до `asbuilt_closed` з мінімальними deliverables — практичний і зрозумілий.

### Що надмірно ускладнено

1. **5 типів графів без justified use case для кожного.** Physical, logical, service, failure_domain, interface — це красиво на папері, але для 3 станцій з кількома десятками вузлів різниця між physical і logical graph може бути мінімальною. Чи справді всі 5 потрібні, чи досить 3 (physical, zone/logical, service overlay)? Failure-domain graph можна вивести з physical + zone topology, а не будувати окремо.

2. **12 ролей у ROLE_MAP** для проєкту з 3 станцій. Реально, одна людина часто виконує 3-4 ролі. Role model формально правильний, але без "role aggregation" механізму (одна людина = кілька ролей) він створить illusion що потрібні 12 окремих спеціалістів.

### Що ще недомислено

1. **Як questionnaire v2 насправді заповнюється?** Ні CLI, ні form, ні template, ні workflow engine. Role views існують у YAML, але немає ні UI, ні навіть Excel/MD шаблону для конкретної ролі.

2. **Archetype → defaults propagation.** `station_archetypes.yaml` має 3 стуба без жодних default field values. Archetype мав би давати sensible defaults для questionnaire: "small_remote_site → telemetry_required: yes, video_required: tbd, staffing_model: remote_ops, redundancy_target: uplink_backup". Зараз archetype — це label, не template.

3. **Версіонування і co-evolution.** Questionnaire v2 і dictionary v2 мають `version: 0.2.0`, але немає version compatibility matrix. Якщо dictionary values зміняться, хто перевалідовує заповнені questionnaires?

4. **Multi-object pipeline.** Все побудовано для одного об'єкта. Для програми з 3 станцій потрібен хоча б program-level view: спільні constraints, shared carriers, common archetypes, cross-site dependencies. Цього немає навіть у планах.

### Де змішані шари

1. **`oob_required` перемістився з `operations` (v1) в `security_access` (v2).** Це boundary decision, але не зафіксоване як migration note. OOB — це і operations, і security concern. Поточне розміщення в security_access суперечить тому, що owner_role = operations_engineer.

2. **`known_unknowns` секція тепер містить governance fields** (`evidence_maturity_class`, `waiver_policy_class`) — це не "unknowns", це governance metadata. Назва секції misleading.

### Terminology drift

- `sync_accuracy_target` (v1 schema) vs `timing_accuracy_class` (v2)
- `degraded_mode_expectation` (v1 schema) vs `degraded_mode_profile` (v2)
- `mttr_target` (v1 schema) vs `mttr_target_class` (v2)
- `remote_access_required` (v1) vs `remote_access_profile` (v2)
- `cabinet_constraints` (v1 array) vs `cabinet_constraint_class` (v2 enum)
- `management_required` (v1) — зникло у v2 без explicit deprecation

### Design smells

1. **`site_specific` catch-all value** у `timing_accuracy_class`, `degraded_mode_profile` — це escape hatch, який у production обов'язково буде зловживатися. Якщо "site_specific" — це valid choice, то controlled vocabulary — ілюзія.

2. **`askoe` у handoff_matrix.py має `enabled = None`** (line 7) — тобто АСКОЕ завжди "baseline". Але АСКОЕ є ключовим споживачем для генеруючих і розподільних об'єктів. Відсутність explicit activation logic — дірка.

---

## 3. CONCRETE REVISIONS

### 3.1 Видалити v1 або створити explicit v1→v2 migration checklist

Зараз маємо подвійний набір:
- `core_questionnaire.yaml` + `fields.yaml` + `values.yaml` + `object_requirements.schema.yaml` — v1
- `core_questionnaire_v2.yaml` + `questionnaire_v2_fields.yaml` + `questionnaire_v2_values.yaml` — v2

Pipeline працює на v1. Методологія описує v2. Це неприпустимий стан.

**Рекомендація:** deprecated-маркер на v1 файли, нова schema для v2, міграція pipeline на v2 field names і enum types.

### 3.2 Role aggregation model

Додати до ROLE_MAP.md або role_views.yaml:

```yaml
role_assignments:
  - person: "Сергій Іваненко"
    roles: [ot_architect, network_engineer]
  - person: "Олена Коваленко"
    roles: [cybersecurity_engineer, operations_engineer]
```

Без цього role model залишається академічним.

### 3.3 Archetype → questionnaire defaults

`station_archetypes.yaml` має давати default values:

```yaml
archetypes:
  - archetype_id: small_remote_site
    defaults:
      staffing_model: remote_ops
      telemetry_required: yes
      video_required: tbd
      redundancy_target: uplink_backup
      oob_required: yes
      support_model: hybrid
```

### 3.4 Rename known_unknowns → split

- `evidence_maturity_class` і `waiver_policy_class` → перенести у `metadata` або нову секцію `governance`
- `known_unknowns` залишити для справжніх unknowns (open questions, required waivers) — як було у v1

### 3.5 Resolve ownership conflicts

Кожне поле — один owner. `questionnaire_v2_fields.yaml` вже має `owner_role`. `role_views.yaml` повинен бути **generated** від fields, а не рукописний з конфліктами.

### 3.6 Complete implementation mapping

Маппінг має покривати 100% полів з `core_questionnaire_v2.yaml`. Поле без downstream mapping — червоний прапор: або воно зайве, або mapping неповний.

### 3.7 Підняти annex fields до повного field contract

Або повний 15-атрибутний контракт, або explicit "annex fields follow relaxed contract: only field_id, type, owner_role, unknown_policy required."

---

## 4. GIT-DIFF STYLE CHANGES

### 4.1 Fix role_views.yaml ownership conflicts

```diff
--- a/project/specs/questionnaire/role_views.yaml
+++ b/project/specs/questionnaire/role_views.yaml
@@ -32,10 +32,10 @@
     owned_fields:
       - telemetry_required
       - control_required
-      - timing_required
       - local_archiving_required
     downstream_packs_of_interest:
       - telemetry_transport_pack
+      - video_transport_pack
       - commissioning_pack
 
   - role_id: network_engineer
@@ -44,17 +44,14 @@
     owns_sections:
       - external_transport
-      - security_access
       - time_sync
     reviews_sections:
       - resilience
       - operations
+      - security_access
     owned_fields:
       - wan_required
       - carrier_diversity_target
       - transport_separation_policy
-      - security_zone_model
-      - oob_required
       - sync_protocol
       - timing_accuracy_class
@@ -96,10 +93,9 @@
   - role_id: telemetry_engineer
     label_uk: Інженер телеметрії / АСКОЕ
-    owns_sections:
-      - critical_services
-      - time_sync
     reviews_sections:
+      - critical_services
+      - time_sync
       - security_access
     owned_fields:
-      - telemetry_required
-      - control_required
       - timing_required
-      - sync_protocol
@@ -116,9 +112,8 @@
     reviews_sections:
       - power_environment
       - external_transport
     owned_fields:
       - video_required
-      - local_archiving_required
-      - poe_required
-      - poe_budget_class
```

### 4.2 Rename known_unknowns → split governance out

```diff
--- a/project/specs/questionnaire/core_questionnaire_v2.yaml
+++ b/project/specs/questionnaire/core_questionnaire_v2.yaml
@@ -78,10 +78,14 @@
       - fat_required
       - sat_required
       - acceptance_evidence_class
 
-  - id: known_unknowns
+  - id: governance
     required: true
     fields:
       - evidence_maturity_class
       - waiver_policy_class
+
+  - id: known_unknowns
+    required: false
+    fields: []
+    note: "Open questions and waivers are tracked in the waiver register, not as questionnaire fields."
```

### 4.3 Add deprecation markers to v1

```diff
--- a/project/specs/questionnaire/core_questionnaire.yaml
+++ b/project/specs/questionnaire/core_questionnaire.yaml
@@ -1,4 +1,6 @@
 version: 0.1.0
+deprecated: true
+superseded_by: core_questionnaire_v2.yaml
 questionnaire_id: core_questionnaire
```

```diff
--- a/project/specs/dictionary/fields.yaml
+++ b/project/specs/dictionary/fields.yaml
@@ -1,2 +1,4 @@
 version: 0.1.0
+deprecated: true
+superseded_by: questionnaire_v2_fields.yaml
 fields:
```

### 4.4 Fix generate_handoff_matrix.py missing import

```diff
--- a/project/src/reports/generate_handoff_matrix.py
+++ b/project/src/reports/generate_handoff_matrix.py
@@ -1,4 +1,6 @@
 from __future__ import annotations
 
+from typing import Any
+
 def generate_handoff_matrix(requirements: dict[str, Any]) -> str:
```

### 4.5 Mark build_requirements_model as passthrough explicitly

```diff
--- a/project/src/compiler/build_requirements_model.py
+++ b/project/src/compiler/build_requirements_model.py
@@ -29,8 +29,9 @@
 
 def build_requirements_model(questionnaire: dict[str, Any]) -> dict[str, Any]:
-    """Convert questionnaire payload into a normalized requirements model.
+    """PASSTHROUGH: Copy questionnaire sections into requirements model without transformation.
 
-    Current behavior is intentionally conservative:
-    - keep section boundaries visible;
-    - avoid inferred values that are not explicitly present;
-    - reserve room for future normalization rules.
+    TODO: This function currently performs no normalization. Future versions should:
+    - apply archetype defaults for missing fields;
+    - derive implicit constraints (e.g., criticality_class:high -> minimum redundancy_target);
+    - validate cross-field consistency before emitting the model;
+    - reject unresolvable unknown combinations per stage gate.
     """
```

---

## 5. RECOMMENDED NEXT WAVE

### Негайно (Wave 0 — hygiene)

1. **Deprecate v1 explicitly.** Маркувати v1 файли. Створити `object_requirements_v2.schema.yaml` строго від v2 dictionary.
2. **Fix role ownership conflicts** у role_views.yaml — підпорядкувати до v2_fields.yaml.
3. **Fix import bug** у generate_handoff_matrix.py.
4. **Complete implementation_mapping.yaml** — покрити 100% v2 полів.
5. **Split `known_unknowns`** — governance metadata окремо.

### Wave 1 — skeleton that actually compiles

6. **Migrate pipeline to v2.** build_requirements_model, schema, validators — все на v2 field names, enum types (yes_no_tbd замість boolean), нові секції.
7. **Archetype defaults.** station_archetypes.yaml з default field values. build_requirements_model застосовує archetype defaults для полів без відповіді.
8. **One real normalization rule.** Наприклад: `if criticality_class in [high, mission_critical] and redundancy_target == none -> inject warning`.
9. **One real graph seed.** Physical graph: від archetype і equipment_catalog створити хоча б access-core-uplink topology seed. Щоб NetworkX мав що аналізувати.
10. **Annex field contracts** — піднести до повного v2 format.

### Wave 2 — production concerns

11. **Role aggregation model** — mapping persons → roles.
12. **Multi-object / program view** — cross-site constraints, shared carriers.
13. **Brownfield / migration annex** — explicitly.
14. **Site survey input template** — формалізувати what we need from field.
15. **Variant scoring / trade-off matrix** — коли archetype дає кілька варіантів, як обирати.
16. **Sample object end-to-end** на v2 — один повний yaml → requirements → graphs → validation → reports.

### Wave 3+ (annexes / future modules)

17. As-built / drift detection model
18. Lifecycle: firmware, certificates, spares register
19. Service-intent model (what does the network promise, not just how it's built)
20. Common-cause failure modeling (beyond boolean `common_cause_separation_required`)
21. RACI matrix generator від role_views
22. Change control / governance workflow engine
23. FAT/SAT checklist generator від commissioning_pack
24. Observability / monitoring baseline

---

## ВЕРДИКТ

### Залишити без змін
- **Методологічні markdown docs** (CORE_QUESTIONNAIRE.md, FIELD_VALUE_DICTIONARY.md, HUMAN_INTERACTION_MODEL.md, NETWORK_VOLUME_STRUCTURE.md, DATA_HANDOFF_MATRIX.md, IMPLEMENTATION_MAPPING.md, QUESTIONNAIRE_WORKFLOW.md) — вони зрілі, boundary discipline правильна, формулювання чисті.
- **v2 field contract structure** (15 атрибутів) — production-grade якість.
- **v2 controlled vocabulary** (questionnaire_v2_values.yaml) — чистий, конкретний, з selection rules.
- **Stage gate model** і **unknown policy model** — зрілі governance конструкції.
- **Waiver schema** — достатня для поточного етапу.

### Переробити обов'язково
- **Pipeline (весь `src/`)** — переписати під v2 model. Зараз це v1 passthrough.
- **object_requirements.schema.yaml** — створити v2 версію.
- **role_views.yaml** — виправити ownership конфлікти, зробити derived від v2_fields.
- **implementation_mapping.yaml** — покрити 100% полів.
- **station_archetypes.yaml** — додати default values, без них archetypes марні.
- **Annex field definitions** — підняти до повного contract.
- **known_unknowns секція v2** — розділити governance і справжні unknowns.

### Видалити або радикально спростити
- **v1 файли** (`core_questionnaire.yaml`, `fields.yaml`, `values.yaml`) — або deprecate explicitly, або видалити. Паралельне існування v1/v2 без migration — це технічний борг, що маскується під "поступову еволюцію".
- **5 типів графів → 3.** failure_domain graph можна вивести з physical + zone. interface graph — це по суті handoff matrix в graph form. Залишити physical, logical/zone, service overlay.
- **`site_specific` catch-all values** — або видалити і додати окремі конкретні enum values, або зафіксувати mandatory `site_specific_note` field що вимагає explanation. Без цього controlled vocabulary — фікція.

---

**Bottom line:** Методологічний фундамент — серйозний і production-worthy. v2 field contract — краще за більшість industrial intake frameworks. Але між методологією і pipeline — прірва. Pipeline досі живе у v1 світі і виконує passthrough + trivial graph stubs. Доки ця прірва не закрита, skeleton — це добре написана документація, а не design compiler. Фокус наступного кроку: не додавати нові шари методології, а привести існуючий pipeline у відповідність до того, що вже описано.
