# IMPLEMENTATION_MAPPING

## Призначення

Implementation mapping фіксує, як поля questionnaire і requirements model переходять у downstream-артефакти.

## Базовий принцип

Логіка така:

`questionnaire field -> normalized requirement -> network volume section -> downstream artifact`

Це дає дві речі:

- questionnaire не перетворюється на смітник конфігів;
- downstream packs мають трасоване походження.

## Що не є implementation mapping

Цей шар:

- не містить final CLI;
- не зберігає повний IP-by-device план;
- не підміняє firewall config repository;
- не підміняє ПНР чеклісти.

Він лише каже, які поля мають породжувати які артефакти і хто їх споживає.

## Downstream Pack Classes

| Pack ID | Призначення | Основні споживачі |
| --- | --- | --- |
| `cabinet_build_pack` | Шафи, power fit, PoE, media, монтажні обмеження | cabinet/power engineer, монтаж |
| `addressing_framework_pack` | Addressing principles, naming, segment classes | network engineer, telemetry, video, IIoT |
| `firewall_policy_intent_pack` | Zones, allowed flows, remote access, logging | cybersecurity, network engineer |
| `telemetry_transport_pack` | Transport constraints для АСКОЕ/телеметрії | telemetry engineer |
| `video_transport_pack` | CCTV transport, PoE, retention constraints | video engineer |
| `iiot_integration_pack` | Isolation, cloud path, management/logging constraints | iiot engineer |
| `commissioning_pack` | FAT/SAT dependencies, test obligations | commissioning engineer |
| `operations_handoff_pack` | OOB, MTTR, degraded mode, support model | operations |
| `asbuilt_closure_pack` | Closure rules for intended vs as-built | project manager, commissioning |

## Mapping Rules

- Поле може мати кілька downstream artifacts.
- Downstream artifact може збирати дані з кількох field IDs.
- Core v2 поле без mapping вважається незавершеним contract і має бути або змеплене, або видалене.
- Якщо зміна поля впливає на artifact class, це має бути відображено у change note.
- Реципієнт артефакта може деталізувати його content, але не змінювати baseline без change control.

## Machine-readable Form

Machine-readable skeleton винесений у [implementation_mapping.yaml](/Users/sd/projects/networkx-3.6.1/project/specs/mappings/implementation_mapping.yaml).
