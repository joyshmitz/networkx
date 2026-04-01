# Network Methodology Sandbox

Цей каталог ізолює methodology + tooling шар від core коду `networkx`.

## Призначення

- зафіксувати object-first методологію;
- описати декларативні inputs;
- підготувати compile -> validate -> report loop поверх NetworkX;
- не змішувати requirements model із final configs.

## Canonical Model

- `v2` questionnaire/dictionary/mapping є canonical contract для нового skeleton;
- `v1` файли збережені лише як deprecated migration reference;
- `NetworkX` тут analysis engine, а не source of truth;
- source of truth живе у YAML / Markdown contracts.

## Поточний фокус

Фаза 1:

- зафіксувати markdown-ядро методології;
- закласти YAML dictionary / schema foundation;
- підготувати skeleton Python pipeline;
- дати один sample object для end-to-end проходу.

## Структура

- `docs/methodology/` — правила, boundaries, handoff contracts;
- `docs/decisions/` — decision log;
- `docs/reviews/` — зовнішні architecture reviews і corrective feedback;
- `specs/` — декларативні YAML inputs;
- `src/` — compiler / validators / reports;
- `examples/` — sample objects.

## Нові шари skeleton

- `docs/methodology/HUMAN_INTERACTION_MODEL.md` — як questionnaire живе між ролями;
- `docs/methodology/ROLE_MAP.md` — хто власник яких відповідей і хто що рев'ює;
- `docs/methodology/QUESTIONNAIRE_WORKFLOW.md` — stage-gated workflow від intake до as-built;
- `docs/methodology/IMPLEMENTATION_MAPPING.md` — як поля переходять у downstream packs;
- `specs/questionnaire/core_questionnaire_v2.yaml` — object-first core questionnaire v2;
- `specs/questionnaire/role_views.yaml` — role-based views поверх canonical question bank;
- `specs/questionnaire/role_assignments.template.yaml` — як кілька ролей агрегуються по реальних людях;
- `specs/dictionary/questionnaire_v2_fields.yaml` — v2 field contract;
- `specs/dictionary/questionnaire_v2_values.yaml` — controlled vocabulary для v2;
- `specs/questionnaire/annex_*.yaml` — optional annexes з explicit relaxed contract;
- `specs/mappings/implementation_mapping.yaml` — machine-readable mapping field -> artifact.

## Робочий принцип

NetworkX тут використовується як analysis engine.
Source of truth живе у YAML / Markdown.
