# DATA_HANDOFF_MATRIX

## Призначення

Матриця передачі даних визначає, що саме том "Мережа" передає суміжним томам і операційним процесам.

## Принцип

Суміжні томи не перевизначають мережевий baseline локально.
Вони використовують затверджені outputs network volume як вхідні інфраструктурні обмеження.

## Мінімальна матриця

| Receiver | Mandatory Inputs From Network Volume |
| --- | --- |
| `askoe` | points of connection, addressing framework, segmentation constraints, transport baseline, timing baseline, resilience assumptions |
| `telemetry` | transport baseline, zoning, OOB baseline, timing baseline, degraded mode rules, integration point register |
| `video` | transport policy, separate/shared transport rules, PoE constraints, uplink constraints, security boundaries, resilience baseline |
| `iiot_edge` | zone of deployment, isolation policy, external connectivity policy, logging baseline, timing baseline, environment and power constraints |
| `operations` | OOB baseline, degraded mode matrix, acceptance criteria, FAT/SAT checklist, as-built closure rules |

## Exchange Contract

Кожен handoff item повинен мати:

- `handoff_id`;
- `producer`;
- `consumer`;
- `payload_name`;
- `format`;
- `required`;
- `version_rule`;
- `trace_to_requirements`;
- `trace_to_validators`.

## TODO

- додати machine-readable handoff registry;
- визначити mandatory vs optional payloads per stage gate;
- додати owner and acceptance rule для кожного handoff item.

