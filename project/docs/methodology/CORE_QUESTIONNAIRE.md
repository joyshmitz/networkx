# CORE_QUESTIONNAIRE

## Призначення

Core Questionnaire є керованим джерелом вимог для конкретного об'єкта.
Його задача — не описати готову мережу, а зібрати дані, з яких мережевий baseline може бути синтезований і перевірений.

Canonical contract для поточного skeleton:

- `core_questionnaire_v2.yaml`;
- `questionnaire_v2_fields.yaml`;
- `questionnaire_v2_values.yaml`.

`v1` questionnaire лишається лише як deprecated migration reference.

## Boundary

Questionnaire:

- збирає вимоги, обмеження, сценарії та acceptance criteria;
- не містить final configs;
- не містить device CLI як source of truth;
- не підміняє собою том "Мережа".

## Human Interaction Contract

Questionnaire не повинен трактуватися як один монолітний YAML, який заповнює одна людина.
Правильна форма взаємодії:

- є один canonical question bank;
- поверх нього будуються role-based views;
- кожне поле має owner role і reviewer role;
- optional annexes активуються лише коли сервіс реально входить у scope;
- unresolved / unknown значення не ховаються у вільному тексті, а проходять через контрольований policy.

## Обов'язкові секції

1. `metadata`
   Ідентифікація об'єкта, контекст, owner, stage.
2. `object_profile`
   Staffing model, growth horizon, operational frame.
3. `critical_services`
   Telemetry, control, video, IIoT, local archiving та інші критичні сервіси.
4. `external_transport`
   Зовнішні канали, оператори, trust boundaries.
5. `security_access`
   Доступ, зонування, remote access, logging expectations.
6. `time_sync`
   Джерела часу, точність, критичність.
7. `power_environment`
   Живлення, PoE, шафи, температурний режим, EMC / field conditions.
8. `resilience`
   Redundancy targets, MTTR, degraded mode expectations.
9. `operations`
   OOB, support model, maintenance windows, handoff expectations.
10. `acceptance_criteria`
    Що буде вважатися успішним результатом.
11. `governance`
    Evidence maturity, waiver policy, stage-gate discipline.
12. `known_unknowns`
    Реєстр невизначеності ведеться окремо від canonical question bank.

## Field Contract

Кожне поле questionnaire повинно мати:

- стабільний `field_id`;
- однозначний зміст;
- дозволені значення або формат;
- рівень строгості;
- `owner_role`;
- `reviewer_roles`;
- політику unknown;
- ознаку required / optional;
- design impact;
- downstream impact;
- вимогу до evidence.

## Annex Policy

Annexes виносять доменно-специфічні блоки, якщо вони не потрібні всім об'єктам:

- CCTV;
- IIoT / edge;
- PTP / time;
- HA;

Brownfield / migration і expanded remote-ops annexes залишаються наступною хвилею,
не частиною поточного minimal skeleton.

Annex за замовчуванням не зобов'язаний мати повний 15-атрибутний field contract.
Він може працювати у `relaxed contract` режимі, але це має бути явно задекларовано
в самому annex YAML.

## Implementation Boundary

Questionnaire може запускати downstream-артефакти, але не зберігає їхній final content.
Наприклад:

- questionnaire фіксує, що потрібен OOB;
- network volume вирішує рамку OOB;
- downstream pack деталізує addressing / interfaces / policy;
- final конфіги живуть поза questionnaire.

## Output Contract

Результат questionnaire етапу:

- сирий questionnaire payload;
- role assignment map;
- role resolution map;
- normalized requirements model;
- список unknowns / waivers;
- traceability map field -> requirement impact.
