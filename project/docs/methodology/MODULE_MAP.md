# MODULE_MAP

## Призначення

Цей файл фіксує boundaries між methodology, declarative specs і Python tooling.

## Layer Mapping

| Layer | Purpose | Current Location |
| --- | --- | --- |
| Human Interaction Model | Role-based intake, ownership, review flow | `docs/methodology/HUMAN_INTERACTION_MODEL.md` + `docs/methodology/ROLE_MAP.md` + `docs/methodology/QUESTIONNAIRE_WORKFLOW.md` |
| Operator Runtime | Day-to-day command surface, generated reports, gate semantics | `docs/methodology/INTAKE_OPERATOR_GUIDE.md` + `project/intake` |
| Planning & Rehearsal | Post-baseline verification and next-phase planning | `docs/methodology/INTAKE_MASTER_NOTE.md` |
| Core Questionnaire | Збір первинних вимог | `specs/questionnaire/` |
| Role Views | Людські представлення canonical questionnaire | `specs/questionnaire/role_views.yaml` |
| Field & Value Dictionary | Controlled vocabulary і трактування | `specs/dictionary/` |
| Implementation Mapping | Traceability field -> pack -> consumer | `docs/methodology/IMPLEMENTATION_MAPPING.md` + `specs/mappings/` |
| Requirements Model | Нормалізований machine-readable layer | `specs/requirements/` + `src/compiler/build_requirements_model.py` |
| Network Volume | Синтез базового інфраструктурного тому | `docs/methodology/NETWORK_VOLUME_STRUCTURE.md` + `src/reports/` |
| Graph Compilation | Побудова graph artifacts | `src/compiler/compile_graphs.py` |
| Validation | Connectivity / zoning / resilience / fit checks | `src/validators/` |
| Downstream Packs | Handoff outputs і summaries | `src/reports/` |
| Example Object | End-to-end sample | `examples/sample_object_01/` |

## Boundary Rules

- `docs/` не є source of truth для machine inputs;
- role views не є окремим source of truth, а лише human-facing views;
- `specs/` не містить final configs;
- implementation mapping визначає, які артефакти народжуються з requirements, але не зберігає final CLI / runtime configs;
- `src/` не хардкодить project-specific facts у валідатори;
- `examples/` демонструють workflow, а не замінюють dictionary / schema;
- core `networkx/` не чіпається без доведеної потреби.

## First Execution Path

1. Заповнити role-based questionnaire views для конкретного об'єкта.
2. Звести відповіді в canonical questionnaire payload.
3. Перетворити його в requirements model.
4. Скомпілювати physical / logical / service / failure-domain / interface graphs.
5. Запустити validators.
6. Згенерувати network volume summary + downstream handoff outputs.
