# Claude Review Brief — Wave 1 Follow-Up

> **ARCHIVAL STATUS:** historical review brief.  
> This document remains as review context, not as an active execution plan.

**Дата:** 2026-04-01  
**Гілка:** `research/methodology-foundation`  
**Repo:** `/Users/sd/projects/networkx-3.6.1`  
**Review mode:** follow-up / delta review after first architecture review

---

## 1. Мета цього рев'ю

Потрібне не повторне рев'ю "з нуля", а **жорстке follow-up review** після першої хвилі виправлень.

Перший review уже є тут:
[ARCHITECTURE_REVIEW_2026-04-01.md](/Users/sd/projects/networkx-3.6.1/project/docs/reviews/ARCHITECTURE_REVIEW_2026-04-01.md)

Тепер треба оцінити:

- що з критичних findings реально закрито;
- що закрито лише формально;
- які нові design smells з'явилися після правок;
- що лишається weakest link перед наступною хвилею.

---

## 2. Що вже змінено після першого review

### 2.1 v2 більше не orphaned

Pipeline тепер працює через `v2`:

- [core_questionnaire_v2.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/core_questionnaire_v2.yaml)
- [questionnaire_v2_fields.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/dictionary/questionnaire_v2_fields.yaml)
- [questionnaire_v2_values.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/dictionary/questionnaire_v2_values.yaml)
- [object_requirements_v2.schema.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/requirements/object_requirements_v2.schema.yaml)
- [build_requirements_model.py](/Users/sd/projects/networkx-3.6.1/project/src/compiler/build_requirements_model.py)
- [compile_graphs.py](/Users/sd/projects/networkx-3.6.1/project/src/compiler/compile_graphs.py)
- [run_pipeline.py](/Users/sd/projects/networkx-3.6.1/project/src/run_pipeline.py)

`v1` файли явно позначені як deprecated reference.

### 2.2 build_requirements_model більше не просто passthrough

Додано:

- version detection;
- reject для `v1` questionnaire;
- archetype resolution;
- archetype defaults merge;
- bool-ish enum normalization;
- compile у `v2` requirements model.

### 2.3 Graphs перестали бути порожніми stub-графами

Зараз у pipeline є non-trivial seed logic:

- archetype-driven physical graph;
- logical zone graph;
- service graph;
- failure-domain graph;
- interface graph.

Sample object зараз реально компілюється в графи з nodes/edges, а не в 1-node placeholders.

### 2.4 Validators більше не pure stubs

Зараз є хоч і ще lightweight, але реальні checks:

- connectivity;
- segmentation;
- resilience;
- power / PoE;
- time.

Додані хоча б кілька cross-field rules, а не лише empty-graph guards.

### 2.5 Role ownership виправлено

`role_views.yaml` синхронізовано з canonical owner/reviewer model із `questionnaire_v2_fields.yaml`.

Також додано explicit role aggregation layer:

- [role_assignments.template.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/role_assignments.template.yaml)
- [examples/sample_object_01/role_assignments.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/role_assignments.yaml)

### 2.6 Annexes більше не bare lists

Annexes переведені у **explicit relaxed contract**:

- [annex_cctv.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_cctv.yaml)
- [annex_iiot.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_iiot.yaml)
- [annex_time.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_time.yaml)
- [annex_ha.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_ha.yaml)

### 2.7 Implementation mapping покрито повністю

[implementation_mapping.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/mappings/implementation_mapping.yaml)
зараз покриває всі core `v2` fields.

### 2.8 Sample end-to-end працює

Орієнтир:

- [questionnaire.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/questionnaire.yaml)
- [requirements.compiled.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/requirements.compiled.yaml)
- [graphs.summary.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/graphs.summary.yaml)
- [validation.summary.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/validation.summary.yaml)
- [pipeline.manifest.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/pipeline.manifest.yaml)

Поточний статус sample run: `ok`, `error_count: 0`, `warning_count: 0`.

---

## 3. На чому тепер треба фокусувати рев'ю

Не витрачай час на вже закриті hygiene-пункти, якщо вони справді закриті.
Замість цього бий по тому, що **може лишатися слабким навіть після виправлень**.

### 3.1 Чи не став skeleton "формально правильним, але ще занадто паперовим"

Головне питання:

Чи теперішній pipeline уже схожий на справжній design compiler, чи це все ще mostly methodology framework з thin runtime?

### 3.2 Чи role aggregation реально вирішує проблему

Подивись критично:

- чи `role_assignments.template.yaml` достатній;
- чи цього досить для реального workflow;
- чи не треба stronger governance rules;
- чи не лишився role model надто академічним.

### 3.3 Чи relaxed annex contract — правильний компроміс

Оціни без поблажок:

- чи annexes тепер достатньо строгі;
- чи relaxed contract не став лазівкою для schema erosion;
- чи якісь annex fields уже просяться назад у core;
- чи треба formal promotion rule annex -> core.

### 3.4 Чи role_views і docs тепер справді derived від canonical field contract

Особливо перевір:

- чи немає ще latent ownership drift;
- чи navigation sections (`owns_sections`, `reviews_sections`) не створюють нові двозначності;
- чи docs не розходяться з actual runtime model.

### 3.5 Чи archetype logic уже корисний, а не декоративний

Перевір:

- чи archetype defaults справді meaningful;
- чи topology seed досить добрий як minimal compiled graph;
- чи resolved archetype реально впливає на design, а не тільки красиво пишеться в manifest.

### 3.6 Чи validators не дають false confidence

Це критично.

Оціни:

- де checks ще занадто слабкі;
- де pipeline може показати `ok`, хоча design по суті ще thin;
- які validators наступні потрібно підняти першими;
- які саме поточні `ok`-статуси ще не означають production confidence.

### 3.7 Чи sample object достатньо репрезентативний

Подивись, чи не занадто він "зручний" для pipeline.

Можливо, він:

- занадто чистий;
- не провокує edge cases;
- не тестує real ambiguity;
- не перевіряє conflicting constraints;
- не показує degraded mode pressure.

### 3.8 Чи docs не перегинають у complexity

Після додавання role aggregation і annex contracts перевір:

- чи docs лишилися читабельними;
- чи не починає methodology знову розростатися швидше за runtime;
- чи не з'являється новий gap між theory і executable skeleton.

---

## 4. Що читати в першу чергу

### Previous review

- [ARCHITECTURE_REVIEW_2026-04-01.md](/Users/sd/projects/networkx-3.6.1/project/docs/reviews/ARCHITECTURE_REVIEW_2026-04-01.md)

### Current methodology

- [README.md](/Users/sd/projects/networkx-3.6.1/project/README.md)
- [CORE_QUESTIONNAIRE.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/CORE_QUESTIONNAIRE.md)
- [FIELD_VALUE_DICTIONARY.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/FIELD_VALUE_DICTIONARY.md)
- [HUMAN_INTERACTION_MODEL.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/HUMAN_INTERACTION_MODEL.md)
- [ROLE_MAP.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/ROLE_MAP.md)
- [QUESTIONNAIRE_WORKFLOW.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/QUESTIONNAIRE_WORKFLOW.md)
- [IMPLEMENTATION_MAPPING.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/IMPLEMENTATION_MAPPING.md)
- [NETWORK_VOLUME_STRUCTURE.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/NETWORK_VOLUME_STRUCTURE.md)
- [DATA_HANDOFF_MATRIX.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/DATA_HANDOFF_MATRIX.md)

### Current specs

- [core_questionnaire_v2.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/core_questionnaire_v2.yaml)
- [role_views.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/role_views.yaml)
- [role_assignments.template.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/role_assignments.template.yaml)
- [annex_cctv.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_cctv.yaml)
- [annex_iiot.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_iiot.yaml)
- [annex_time.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_time.yaml)
- [annex_ha.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/annex_ha.yaml)
- [questionnaire_v2_fields.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/dictionary/questionnaire_v2_fields.yaml)
- [questionnaire_v2_values.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/dictionary/questionnaire_v2_values.yaml)
- [implementation_mapping.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/mappings/implementation_mapping.yaml)
- [object_requirements_v2.schema.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/requirements/object_requirements_v2.schema.yaml)
- [station_archetypes.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/archetypes/station_archetypes.yaml)
- [equipment_catalog.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/archetypes/equipment_catalog.yaml)
- [compatibility_matrix.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/archetypes/compatibility_matrix.yaml)

### Current runtime

- [build_requirements_model.py](/Users/sd/projects/networkx-3.6.1/project/src/compiler/build_requirements_model.py)
- [compile_graphs.py](/Users/sd/projects/networkx-3.6.1/project/src/compiler/compile_graphs.py)
- [validate_connectivity.py](/Users/sd/projects/networkx-3.6.1/project/src/validators/validate_connectivity.py)
- [validate_segmentation.py](/Users/sd/projects/networkx-3.6.1/project/src/validators/validate_segmentation.py)
- [validate_resilience.py](/Users/sd/projects/networkx-3.6.1/project/src/validators/validate_resilience.py)
- [validate_power_ports.py](/Users/sd/projects/networkx-3.6.1/project/src/validators/validate_power_ports.py)
- [validate_time.py](/Users/sd/projects/networkx-3.6.1/project/src/validators/validate_time.py)
- [generate_network_volume_summary.py](/Users/sd/projects/networkx-3.6.1/project/src/reports/generate_network_volume_summary.py)
- [generate_handoff_matrix.py](/Users/sd/projects/networkx-3.6.1/project/src/reports/generate_handoff_matrix.py)
- [run_pipeline.py](/Users/sd/projects/networkx-3.6.1/project/src/run_pipeline.py)

### Sample object

- [questionnaire.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/questionnaire.yaml)
- [role_assignments.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/role_assignments.yaml)
- [requirements.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/requirements.yaml)
- [requirements.compiled.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/requirements.compiled.yaml)
- [graphs.summary.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/graphs.summary.yaml)
- [validation.summary.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/validation.summary.yaml)
- [network_volume_summary.md](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/network_volume_summary.md)
- [handoff_matrix.md](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/handoff_matrix.md)
- [pipeline.manifest.yaml](/Users/sd/projects/networkx-3.6.1/project/examples/sample_object_01/reports/pipeline.manifest.yaml)

---

## 5. Формат відповіді

Почни з findings, не з похвали.

Структура:

1. **Still Critical**
   Що лишається критично слабким після Wave 1.

2. **Fixed vs Only Superficially Fixed**
   Розділи:
   - що реально закрито;
   - що закрито лише формально;
   - де з'явилася false confidence.

3. **New Design Smells**
   Що з’явилося або стало помітним лише після нових правок.

4. **Concrete Revisions**
   Що саме треба змінити далі, без розмитих порад.

5. **Git-Diff Style Suggestions**
   Для найважливіших змін дай конкретні diff-style правки у формулюваннях,
   структурах або contracts.

6. **Next Wave Recommendation**
   Що робити:
   - негайно;
   - другою хвилею;
   - пізніше / annexes / future modules.

---

## 6. Особливі вимоги до рев'ю

- Не повторюй mechanically перший review, якщо пункт уже справді закритий.
- Але якщо він закритий лише формально, назви це прямо.
- Не будь дипломатичним.
- Якщо relaxed annex contract — слабкий компроміс, скажи прямо.
- Якщо role aggregation ще декоративний, скажи прямо.
- Якщо sample object занадто зручний і не тестує реальність, скажи прямо.
- Якщо runtime все ще відстає від docs, скажи прямо.

Короткий фінальний verdict дай у 3 рядки:

- `залишити`
- `переробити`
- `не роздувати далі`
