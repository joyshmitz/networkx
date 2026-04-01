# NETWORK_VOLUME_STRUCTURE

## Призначення

Том "Мережа" є базовим інфраструктурним томом для суміжних систем.
Він синтезується з normalized requirements model і фіксує затверджене мережеве середовище.

## Що входить

- інфраструктурна концепція;
- physical topology;
- logical / zone topology;
- addressing framework;
- naming framework;
- WAN / external transport baseline;
- management / OOB baseline;
- security zoning model;
- time sync baseline;
- resilience and degraded mode model;
- equipment compatibility baseline;
- interface baseline for adjacent volumes;
- data handoff matrix;
- FAT / SAT network criteria;
- as-built reconciliation rules.

## Що не входить як основний зміст

- прикладна логіка SCADA / АСКОЕ / VMS;
- прикладні policy configs;
- повний CLI пристроїв;
- vendor-specific implementation details без затвердженої потреби.

## Вхідні артефакти

- questionnaire payload;
- field & value dictionary;
- requirements model;
- hard / soft constraints;
- waivers;
- archetype catalog;
- compatibility matrix.

## Вихідні артефакти

- network volume summary;
- graph validation report;
- interface baseline;
- downstream handoff matrix;
- list of unresolved assumptions / waivers.

## Internal Sections

1. Scope and assumptions
2. Physical topology
3. Logical topology and zoning
4. Addressing and naming
5. External transport
6. Management / OOB
7. Time sync
8. Resilience and degraded modes
9. Equipment compatibility
10. Adjacent-volume interfaces
11. FAT / SAT criteria
12. As-built closure rules

