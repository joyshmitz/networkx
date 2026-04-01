# ROLE_MAP

## Призначення

Цей файл фіксує, хто є owner різних частин questionnaire і хто споживає downstream outputs.
Canonical source of ownership є
[questionnaire_v2_fields.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/dictionary/questionnaire_v2_fields.yaml).
Role views повинні бути похідними від нього, а не окремим джерелом істини.

## Базові ролі

| Role ID | Назва | Основна відповідальність | Типові секції | Основні downstream outputs |
| --- | --- | --- | --- | --- |
| `object_owner` | Власник об'єкта / замовник | Бізнес-критичність, acceptance, рамка об'єкта | `metadata`, `object_profile`, `acceptance_criteria` | network volume baseline, acceptance pack |
| `project_manager` | Керівник проєкту | Stage gates, unresolved items, waivers | cross-section review | change log, closure tracking |
| `process_engineer` | Технолог / виробництво | Критичні режими, деградовані сценарії | `object_profile`, `critical_services`, `resilience` | degraded mode matrix |
| `ot_architect` | OT / ICS архітектор | Загальна object-first рамка, архітектурні компроміси | all core sections | network volume, archetype selection |
| `network_engineer` | Мережевий інженер | Transport, zoning, management, addressing framework | `external_transport`, `security_access`, `operations` | logical baseline, addressing pack |
| `cybersecurity_engineer` | Кібербезпека | Zones, remote access, logging, trust boundaries | `security_access`, `operations` | firewall intent pack, access matrix |
| `cabinet_power_engineer` | Шафи / живлення / монтаж | Cabinet fit, power, PoE, environment | `power_environment` | cabinet build pack, power budget |
| `telemetry_engineer` | Телеметрія / АСКОЕ / SCADA transport | Telemetry/control transport і timing dependencies | `critical_services`, `time_sync`, telemetry-related annexes | telemetry transport pack |
| `video_engineer` | Відеоспостереження | Camera profile, retention, transport pressure, PoE | CCTV annex | video transport pack |
| `iiot_engineer` | IIoT / edge / analytics | Isolation, cloud policy, edge workloads | IIoT annex | iiot integration pack |
| `operations_engineer` | Експлуатація | OOB, MTTR, support model, break-glass expectations | `operations`, `resilience` | operations handoff pack |
| `commissioning_engineer` | ПНР / FAT / SAT | Verification obligations, closure evidence | `acceptance_criteria`, `resilience` | commissioning pack, as-built closure |

## Ownership Rules

- Кожне поле повинно мати `owner_role`.
- Критичні поля повинні мати щонайменше одного reviewer.
- Reviewer не змінює зміст поля без повернення його owner.
- Downstream-роль не може непомітно перевизначити поле у своєму пакеті.

## Role Aggregation Rules

- Одна людина може виконувати кілька roles.
- Це не змінює `owner_role` поля і не зливає role-level accountability.
- Якщо одна людина закриває owner і reviewer для `S4` поля, потрібен second reviewer.
- Person-to-role assignments фіксуються окремим artifact, а не в самому field dictionary.

Шаблон для цього artifact:
[role_assignments.template.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/questionnaire/role_assignments.template.yaml)

### Приклад role aggregation

```yaml
assignments:
  - person_id: arch_01
    roles: [ot_architect, network_engineer]
  - person_id: ops_01
    roles: [operations_engineer, cybersecurity_engineer]
```

## Approval Heuristic

- `S4` поля: owner + reviewer + stage-gate підтвердження.
- `S3` поля: owner + evidence.
- `S2` поля: owner + controlled value.
- `S1` поля: owner, можна як estimate.
