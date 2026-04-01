# Follow-Up Architecture Review — Wave 1 Delta

**Дата:** 2026-04-01
**Гілка:** `research/methodology-foundation`
**Рев'юер:** Claude (за запитом)
**Контекст:** Delta review після першої хвилі виправлень
**Попередній review:** [ARCHITECTURE_REVIEW_2026-04-01.md](ARCHITECTURE_REVIEW_2026-04-01.md)

---

## 1. STILL CRITICAL

### SC-1: Pipeline дає `status: ok, error_count: 0, warning_count: 0` для concept-stage design — це false confidence

**Severity: CRITICAL**

Sample object — generation site, `criticality_class: high`, `redundancy_target: n_plus_1`, `common_cause_separation_required: yes`, `evidence_maturity_class: mixed`, `project_stage: concept`. Pipeline каже: все добре, 0 помилок, 0 попереджень.

Це неможливий result для concept stage. На concept stage:

- evidence ще `mixed` — дані ненадійні;
- transport path ще не верифікований в полі;
- PoE budget ще не перевірений фізично;
- common-cause separation не підтверджена site survey;
- MTTR target `four_hours` ще не має сервісного контракту.

Жоден validator не перевіряє stage-vs-confidence consistency. Pipeline ловить internal contradictions (high criticality + no redundancy), але не каже: "ваша впевненість не відповідає стадії проєкту".

**Чому критично:** Головний ризик цього skeleton — не помилки у графах, а те, що він каже `ok` коли повинен казати `caution: concept-stage confidence, N assumptions unverified`. Якщо цей pipeline потрапить у production, люди будуть використовувати `status: ok` як sign-off evidence. А цей `ok` нічого не означає на concept stage.

### SC-2: Archetype resolution — primitive heuristic, що дає неправильні результати

**Severity: HIGH**

`build_requirements_model.py:55-64`:

```python
if services.get("iiot_required") == "yes":
    return "mixed_iiot_site"
if services.get("video_required") == "yes" or power_environment.get("poe_budget_class") in {"medium", "heavy"}:
    return "video_heavy_site"
return "small_remote_site"
```

Проблеми:

- **Generation site + criticality=high + n_plus_1 + remote_ops + dual_carrier + no_video + no_iiot → `small_remote_site`**. Це абсурд.
- Archetype не враховує `criticality_class`, `redundancy_target`, `staffing_model`, `object_type`.
- Topology seed і defaults для високо-критичних non-video/non-iiot об'єктів будуть wrong.

### SC-3: Annexes — dead YAML для pipeline

**Severity: HIGH**

4 annex файли мають гарні contracts. Але:

- `run_pipeline.py` не читає жоден annex;
- `build_requirements_model.py` не перевіряє, чи active annex поля заповнені;
- `compile_graphs.py` не використовує annex data;
- жоден validator не перевіряє annex consistency.

Коли `video_required: yes`, pipeline не перевіряє, чи є `camera_count_estimate`, `retention_profile` тощо. Annex contract — правильна ідея, але зараз це методологія, а не runtime.

### SC-4: Role assignments ніде не споживаються

**Severity: MEDIUM-HIGH**

`role_assignments.yaml` існує для sample object. `role_assignments.template.yaml` задає правила. Але:

- `run_pipeline.py` не читає `role_assignments.yaml`;
- жоден validator не перевіряє S4 conflict rule (owner == reviewer → need second reviewer);
- handoff matrix не показує person, тільки role.

---

## 2. FIXED vs ONLY SUPERFICIALLY FIXED

### Реально закрито

| Перший Review Finding | Status | Обґрунтування |
|---|---|---|
| CF-1: v2 orphaned | **CLOSED** | Pipeline працює на v2. detect/reject v1. Schema v2 існує. |
| CF-2: Passthrough compiler | **MOSTLY CLOSED** | Archetype resolution, defaults merge, bool normalization, version detection. Не passthrough. |
| CF-3: Empty graph stubs | **CLOSED** | Physical: 9 nodes/7 edges. Logical: 5/4. Service: 9/8. Failure domain: 6/2. Interface: 5/4. Real seed + enrichment. |
| CF-5: Ownership conflicts | **CLOSED** | role_views.yaml синхронізований з v2_fields.yaml. `derived_from` note, no more dual ownership. |
| CF-6: Schema drift | **CLOSED** | `object_requirements_v2.schema.yaml` існує, pipeline validates against it. |
| CF-8: Mapping incomplete | **CLOSED** | 47 полів покриті. Handoff matrix генерується від mapping. |
| CF-9: Handoff ignores mapping | **CLOSED** | `generate_handoff_matrix.py` reads `implementation_mapping.yaml`, generates real matrix. |
| CF-10: Import error | **CLOSED** | Fixed. |

### Закрито формально — false confidence лишається

| Finding | Status | Деталі |
|---|---|---|
| CF-4: Validators only check empty | **SUPERFICIALLY CLOSED** | Real cross-field rules додані (criticality vs redundancy, PTP vs equipment, bridges, zone consistency). Але stage-confidence validation відсутня. |
| CF-7: Annexes second-class | **PARTIALLY CLOSED** | Relaxed contract задано і задокументовано. Але pipeline їх не споживає (SC-3). |
| Archetype logic (prev review §2) | **SUPERFICIALLY CLOSED** | Defaults meaningful (39 fields per archetype), topology seeds real. Але selection ігнорує criticality, redundancy, object_type. |
| Role aggregation (prev review §2) | **SUPERFICIALLY CLOSED** | Template exists, sample has it, rules documented. Zero runtime validation. |

---

## 3. NEW DESIGN SMELLS

### DS-1: `requirements.compiled.yaml` ≡ input questionnaire для well-formed inputs

Порівняння `questionnaire.yaml` з `requirements.compiled.yaml`: **ідентичні** (плюс два штампи `questionnaire_version` і `resolved_archetype` у metadata).

Archetype defaults і bool normalization працюють лише для missing/TBD полів. Sample object не має missing/TBD → build_requirements_model залишається passthrough для нього.

Наслідок: неможливо побачити, що компілятор щось робить, поки sample object "занадто чистий".

### DS-2: Service graph створює zone nodes без зв'язку з logical graph

`compile_service_graph()` використовує string literals `"OT"`, `"MGMT"`, `"DMZ"`, `"EXTERNAL"` як node IDs. Ці ж strings є у logical graph. Але service graph — окремий DiGraph.

Код для telemetry:

```python
graph.add_edge(service_node, "DMZ" if zone_model in {"dmz_centric", "strict_isolation"} else "EXTERNAL", path_role="transport")
```

Hardcoded fallback на `EXTERNAL` навіть якщо EXTERNAL zone не існує у logical graph. Consistency між графами не гарантована.

### DS-3: Sample object — ідеальний happy path, не test case

Sample object (`sample_object_01`):

- **Всі поля заповнені** — жодного TBD. Archetype defaults не активуються.
- **Жоден annex не задіяний** — `video_required: yes`, але CCTV annex не заповнений.
- **Конфліктів немає** — high criticality + n_plus_1 + dual_carrier + dmz_centric = максимально consistent.
- **concept stage** але evidence `mixed` — ніхто не перевіряє що це ненадійно.
- **Degraded mode = telemetry_survives** — найменш суперечлива опція.

Цей object не тестує: TBD-heavy intake, conflicting constraints, annex activation, role S4 conflict, edge archetype fallback.

### DS-4: `site_specific` catch-all досі в словнику

`timing_accuracy_class` і `degraded_mode_profile` мають `site_specific` як valid value. Перший review зафіксував. Нічого не змінилось. Controlled vocabulary з escape hatch — не controlled vocabulary.

### DS-5: Failure domain graph — floating abstraction

Failure domain graph: nodes `power_primary`, `cabinet_primary`, `carrier_a` etc. Але:

- nodes не mapped до physical nodes (яке обладнання в якому domain?);
- `validate_resilience` перевіряє bridges на physical і carrier count на failure graph — але ніколи не перевіряє чи physical nodes розподілені по failure domains;
- можна мати `no_spof`, 2 carrier domains, 0 bridges — pipeline каже `ok` — але якщо обидва switch-і на одному UPS, це невидимо.

### DS-6: Нуль тестів

Весь runtime (`model_utils.py`, `build_requirements_model.py`, `compile_graphs.py`, 5 validators, 2 reports, `run_pipeline.py`) — без тестів. Refactoring або rename поля у YAML не має safety net.

---

## 4. CONCRETE REVISIONS

### 4.1 Додати stage-confidence validator

Новий validator `validate_stage_confidence`:

- `project_stage == concept` + `evidence_maturity_class in {assumption_heavy, mixed}` → warning з confidence_level: indicative;
- `project_stage == concept` + будь-який S4 field is TBD → error;
- `project_stage in {detailed_design, build_commission}` + `evidence_maturity_class == assumption_heavy` → error;
- output: explicit `confidence_level: indicative | provisional | binding` у validation summary.

### 4.2 Виправити archetype resolution

Додати `criticality_class` і `redundancy_target` у heuristic. Додати 4-й archetype `resilient_telemetry_site` у `station_archetypes.yaml` для high-criticality non-video/non-iiot sites.

### 4.3 Додати sample_object_02 — stress test

Мінімальний "dirty" sample:

```yaml
version: 0.2.0
metadata:
  object_id: sample_object_02
  object_name: Remote Metering Point
  object_type: utility_process
  project_stage: concept
  criticality_class: high
critical_services:
  telemetry_required: 'yes'
  control_required: 'tbd'
  video_required: 'no'
  iiot_required: 'no'
  local_archiving_required: 'tbd'
resilience:
  redundancy_target: none           # contradiction with high criticality
  common_cause_separation_required: 'tbd'
governance:
  evidence_maturity_class: assumption_heavy
  waiver_policy_class: provisional
```

Pipeline MUST produce errors/warnings для цього sample.

### 4.4 Validation summary — confidence level

```yaml
status: ok
error_count: 0
warning_count: 0
confidence_level: indicative
confidence_note: "concept stage with mixed evidence — results are indicative, not binding"
issues: []
```

### 4.5 Annex activation check

Validator що generує warning коли `video_required: yes` але CCTV annex data absent. Аналогічно для iiot, timing, HA.

### 4.6 Cross-graph consistency

Validator що перевіряє: service graph zone nodes ⊆ logical graph nodes. Failure domain nodes мають ref до physical equipment.

### 4.7 Прибрати `site_specific` catch-all

Або видалити і додати конкретні значення, або зробити `site_specific` + обов'язковий `site_specific_note` field.

---

## 5. GIT-DIFF STYLE SUGGESTIONS

### 5.1 Stage-confidence у validation summary

```diff
--- a/project/src/run_pipeline.py
+++ b/project/src/run_pipeline.py
@@ summarize_validation
+CONFIDENCE_MAP = {
+    "concept": {"assumption_heavy": "indicative", "mixed": "indicative", "mostly_confirmed": "provisional", "field_verified": "provisional"},
+    "basic_design": {"assumption_heavy": "indicative", "mixed": "provisional", "mostly_confirmed": "provisional", "field_verified": "binding"},
+    "detailed_design": {"assumption_heavy": "indicative", "mixed": "provisional", "mostly_confirmed": "binding", "field_verified": "binding"},
+    "build_commission": {"assumption_heavy": "indicative", "mixed": "provisional", "mostly_confirmed": "binding", "field_verified": "binding"},
+}
+
+
+def derive_confidence_level(requirements: dict[str, Any]) -> str:
+    stage = requirements.get("metadata", {}).get("project_stage", "concept")
+    maturity = requirements.get("governance", {}).get("evidence_maturity_class", "assumption_heavy")
+    return CONFIDENCE_MAP.get(stage, {}).get(maturity, "indicative")
```

У `main()` після `summarize_validation`:

```diff
+    validation_summary["confidence_level"] = derive_confidence_level(requirements)
```

### 5.2 Archetype resolution — criticality fallback

```diff
--- a/project/src/compiler/build_requirements_model.py
+++ b/project/src/compiler/build_requirements_model.py
@@ resolve_archetype_id
 def resolve_archetype_id(questionnaire: dict[str, Any]) -> str:
     services = questionnaire.get("critical_services", {})
     power_environment = questionnaire.get("power_environment", {})
+    metadata = questionnaire.get("metadata", {})
+    resilience = questionnaire.get("resilience", {})
 
     if services.get("iiot_required") == "yes":
         return "mixed_iiot_site"
     if services.get("video_required") == "yes" or power_environment.get("poe_budget_class") in {
         "medium",
         "heavy",
     }:
         return "video_heavy_site"
+    if metadata.get("criticality_class") in {"high", "mission_critical"} or resilience.get(
+        "redundancy_target"
+    ) in {"n_plus_1", "no_spof"}:
+        return "resilient_telemetry_site"
     return "small_remote_site"
```

### 5.3 Service graph — guard zone existence

```diff
--- a/project/src/compiler/compile_graphs.py
+++ b/project/src/compiler/compile_graphs.py
@@ compile_service_graph
+    wan_required = is_yes(requirements.get("external_transport", {}).get("wan_required"))
+    external_zone = ("DMZ" if zone_model in {"dmz_centric", "strict_isolation"} else "EXTERNAL") if wan_required else None
 
         if service_name == "telemetry":
             graph.add_edge("OT", service_node, path_role="source")
-            graph.add_edge(service_node, "DMZ" if zone_model in {"dmz_centric", "strict_isolation"} else "EXTERNAL", path_role="transport")
+            if external_zone:
+                graph.add_edge(service_node, external_zone, path_role="transport")
```

---

## 6. NEXT WAVE RECOMMENDATION

### Негайно (до наступного review)

1. **`validate_stage_confidence`** — validator що виставляє `confidence_level` і попереджає при concept + mixed evidence. Без цього `status: ok` misleading.
2. **`sample_object_02`** — dirty sample з TBDs, conflicting constraints. Pipeline MUST produce non-zero warnings/errors.
3. **Archetype resolution** — додати criticality/redundancy + новий archetype `resilient_telemetry_site`.

### Друга хвиля

4. **Annex activation validator** — warning коли required service active але annex absent.
5. **Cross-graph consistency** — service graph zones ⊆ logical graph zones.
6. **Role assignment validator** — S4 owner≠reviewer conflict check.
7. **Failure domain ↔ physical mapping** — failure domain nodes reference physical equipment.
8. **Мінімальний test suite** — pytest для model_utils, build_requirements_model, compile_graphs.

### Пізніше / Wave 3+

9. Multi-object program view.
10. Annex field consumption у pipeline.
11. As-built drift detection.
12. RACI generator від role_views + role_assignments.
13. Видалити `site_specific` catch-all values.

---

## ВЕРДИКТ

**Залишити:** v2 field contract, controlled vocabulary, methodology docs, stage-gate model, implementation mapping, handoff matrix generator, graph seed logic, validator cross-field rules.

**Переробити:** archetype resolution (додати criticality dimension), validation summary (додати confidence_level), sample object (додати dirty test case), service graph zone coupling.

**Не роздувати далі:** Не додавати нові annex types, нові ролі, нові methodology docs поки runtime не має stage-confidence validator, annex consumption і хоча б один stress-test sample. Methodology вже випереджає runtime — зупинити docs, піднімати code.
