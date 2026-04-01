# HUMAN_INTERACTION_MODEL

## Призначення

Цей файл фіксує людський шар questionnaire-процесу.
Мета проста: questionnaire має бути придатним для різних ролей і при цьому лишатися machine-readable source for synthesis.

## Базовий принцип

Questionnaire не є формою "для однієї людини".
Правильна модель така:

- є canonical question bank;
- є role-based views поверх нього;
- кожне поле має owner і reviewers;
- відповідь існує разом із evidence, статусом і unknown policy;
- зведений questionnaire payload компілюється в requirements model.

## Role Aggregation

Кількість roles не дорівнює кількості людей.
Одна людина може закривати кілька roles, але:

- ownership залишається role-based, не person-based;
- якщо одна людина закриває і owner role, і reviewer role для `S4` поля, потрібен second reviewer;
- downstream packs посилаються на `role_id`, а не на ім'я конкретної людини;
- mapping people -> roles фіксується окремо від canonical question bank.

Шаблон такого mapping винесений у
[role_assignments.template.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/role_assignments.template.yaml).

## Що вважається human-facing view

Людська форма може бути:

- workbook / spreadsheet;
- structured form у внутрішній системі;
- YAML/Markdown-шаблон для відповідної ролі.

У всіх випадках canonical field IDs та controlled values залишаються спільними.

## Чого цей шар не робить

Human interaction layer:

- не визначає final topology сам по собі;
- не зберігає final device configs;
- не підміняє change control;
- не дублює downstream packs.

## Принципи

- `object-first` — спочатку вимоги конкретного об'єкта, потім archetype.
- `one field, one meaning, one owner` — одне поле не несе кілька різних смислів.
- `core + annexes` — базовий intake для всіх, спеціалізовані annexes лише за потребою.
- `role views, not role silos` — ролі бачать свою view, але працюють над спільним canonical model.
- `unknowns are managed` — невідоме значення не ховається у тексті, а керується через policy.
- `role aggregation is explicit` — люди агрегують ролі явно, а не неформально.

## Статуси відповіді

Рекомендовані стани:

- `draft`
- `answered`
- `reviewed`
- `approved`
- `waived`
- `unresolved`

## Stage Gates

1. `intake_open`
   Core questionnaire відкритий, annexes ще не зафіксовані.
2. `intake_complete`
   Core questionnaire заповнений, відомі owners і open questions.
3. `baseline_ready`
   Requirements model і network volume можуть бути зібрані.
4. `handoff_ready`
   Downstream packs сформовані й погоджені.
5. `asbuilt_closed`
   Intended vs as-built closure завершена.

## Мінімальні ролі

- `object_owner`
- `project_manager`
- `process_engineer`
- `ot_architect`
- `network_engineer`
- `cybersecurity_engineer`
- `cabinet_power_engineer`
- `telemetry_engineer`
- `video_engineer`
- `iiot_engineer`
- `operations_engineer`
- `commissioning_engineer`

Детальна карта ролей винесена у [ROLE_MAP.md](/Users/sd/projects/networkx-3.6.1/project/docs/methodology/ROLE_MAP.md).
