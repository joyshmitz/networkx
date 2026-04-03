# INTAKE_OPERATOR_GUIDE

## Призначення

Цей документ пояснює, як практично працювати з intake workspace після завершення `v1`. Він написаний для змішаної аудиторії:

- координатора або керівника проєкту, який веде intake-процес;
- предметних спеціалістів, які відповідають за окремі поля та review;
- архітекторів і інженерів, яким потрібна точна поведінка CLI та generated reports;
- неінженерних учасників, яким потрібно зрозуміти, який статус має workspace і що саме ще не закрито.

Якщо потрібна історія виконання `v1`, дивіться `project/docs/reviews/V1_CLOSEOUT_2026-04-03.md`. Якщо потрібна методологічна картина в цілому, дивіться `QUESTIONNAIRE_WORKFLOW.md` і `ROLE_MAP.md`.

## Основна Ідея

Один workspace проходить через три шари:

1. люди дають відповіді у role-based workbooks;
2. система компілює ці відповіді у canonical questionnaire і pipeline reports;
3. поверх compiled state генеруються operator-facing reports для readiness, review і evidence gate.

Важлива межа проста:

- editable source of truth не множиться;
- `review` і `evidence` не створюють нових ручних input-файлів;
- generated files під `reports/` можна безпечно перегенеровувати.

## Що Є В Workspace

| Клас артефактів | Типові файли | Хто цим користується | Чи редагується вручну |
| --- | --- | --- | --- |
| Role and human inputs | `role_assignments.yaml`, `intake/responses/*.xlsx` | координатор, domain specialists | так |
| Compiled canonical state | `questionnaire.yaml`, `intake/responses/*.response.yaml`, `reports/intake_status.*` | координатор, інженери, аудит | ні, це compile outputs |
| Derived operational reports | `reports/preview_status.*`, `reports/reviewer_registry.*`, `reports/review_packet.*`, `reports/evidence_status.*`, `reports/workspace.manifest.yaml` | координатор, reviewers, PM, аудит | ні, це generated artifacts |
| Pipeline reports | `reports/requirements.compiled.yaml`, `reports/graphs.summary.yaml`, `reports/validation.summary.yaml`, `reports/network_volume_summary.md`, `reports/handoff_matrix.md`, `reports/pipeline.manifest.yaml` | інженери, архітектори, handoff consumers | ні, це generated artifacts |

`reports/workspace.manifest.yaml` є індексом generated outputs усередині workspace. Це не ручний input і не окремий source of truth.

## Командна Поверхня

Канонічна operator-facing поверхня проходить через `project/intake`.

| Команда | Коли запускати | Що вона робить | Що записує |
| --- | --- | --- | --- |
| `project/intake generate <workspace> [--date ...] [--preserve-responses]` | коли створюєте workspace або перебудовуєте workbook layout | генерує role-based workbooks і guide files | `intake/generated/*.guide.md`, `intake/responses/*.xlsx` |
| `project/intake compile <workspace> [--date ...]` | коли відповіді вже внесені і треба отримати canonical payload | компілює workbook answers у canonical questionnaire і compile status | `questionnaire.yaml`, `intake/responses/*.response.yaml`, `reports/intake_status.*`, manifest |
| `project/intake preview <workspace> [--date ...]` | коли треба зрозуміти, чи workspace baseline-ready | перевиконує compile + pipeline через shared snapshot і дає короткий readiness summary | pipeline reports, `reports/preview_status.*`, manifest |
| `project/intake review <workspace> [--date ...]` | коли треба роздати unresolved fields, validator findings і evidence gaps по ролях і людях | будує reviewer registry та routed review packets | `reports/reviewer_registry.*`, `reports/review_packet.*`, manifest |
| `project/intake evidence <workspace> [--date ...]` | коли треба оцінити якість evidence і, за потреби, пройти stage gate | будує evidence status, а в narrow scope ще й blocking gate | `reports/evidence_status.*`, manifest |
| `project/intake verify [pytest args...]` | коли змінюється код, specs або exemplar behavior | запускає regression suite | нічого у workspace не пише |
| `project/intake demo happy|stress [--date ...]` | коли треба показати expected behavior на exemplar workspaces | відтворює happy/stress сценарій у temporary copy | нічого в tracked workspace не пише |

## Рекомендована Послідовність Роботи

### 1. Підготуйте або оновіть workbooks

Якщо workspace новий:

```bash
project/intake generate project/examples/my_object --date 2026-04-02
```

Якщо структура questionnaire змінилася, але вже є заповнені таблиці:

```bash
project/intake generate project/examples/my_object --date 2026-04-02 --preserve-responses
```

`--preserve-responses` переносить існуючі значення з колонок `E/F/G/H` за `field_id`. Це корисно, коли field переставляється між workbook tabs або між людьми.

### 2. Скомпілюйте answers у canonical state

```bash
project/intake compile project/examples/my_object --date 2026-04-02
```

Після цього ви отримуєте:

- `questionnaire.yaml` як compiled canonical questionnaire;
- `reports/intake_status.yaml` і `reports/intake_status.md` як короткий compile summary;
- `intake/responses/*.response.yaml` як machine-readable capture того, що було у workbook.

На цьому кроці ще немає operator routing і ще немає evidence gate.

### 3. Перевірте baseline readiness

```bash
project/intake preview project/examples/my_object --date 2026-04-02
```

`preview` відповідає на питання: чи достатньо поточного workspace state, щоб вважати baseline придатним до подальшої інженерної роботи.

Практично це означає:

- compile state валідний;
- pipeline відпрацював і дав зрозумілий validation summary;
- немає unresolved `S4` fields;
- generated summary зібраний у `reports/preview_status.yaml` і `reports/preview_status.md`.

`preview` не застосовує blocking evidence gate. Він може бути зеленим у тих випадках, коли evidence ще лише advisory.

### 4. Згенеруйте review packets

```bash
project/intake review project/examples/my_object --date 2026-04-02
```

Цей крок потрібен тоді, коли треба перетворити technical findings у конкретну людську роботу:

- хто має відповісти на unresolved field;
- хто є primary reviewer;
- чи потрібен second reviewer;
- які items повинен забрати координатор.

Після команди з'являються:

- `reports/reviewer_registry.yaml`
- `reports/reviewer_registry.md`
- `reports/review_packet._coordinator.md`
- `reports/review_packet.<person_id>.md` для тих людей, у яких є routed items

### 5. Перевірте evidence status і, якщо треба, stage gate

```bash
project/intake evidence project/examples/my_object --date 2026-04-02
```

Ця команда робить дві речі:

1. показує evidence status для selected fields;
2. у вузько визначеному scope застосовує blocking gate.

Для більшості ранніх workspace станів це advisory report. Blocking semantics з'являються лише там, де policy явно це дозволяє.

## Як Читати Основні Outputs

### `preview_status`

Файли:

- `reports/preview_status.yaml`
- `reports/preview_status.md`

Що вони відповідають:

- чи workspace baseline-ready;
- скільки є pipeline errors і warnings;
- які `S4` fields лишилися unresolved;
- які blockers зараз важливі для координатора.

Що `baseline_ready` означає:

- compile + pipeline contract не зламаний;
- unresolved `S4` fields не блокують baseline;
- поточний workspace можна обговорювати як baseline candidate.

Що `baseline_ready` не означає:

- що review already complete;
- що evidence already sufficient for later-stage sign-off;
- що downstream packs already agreed.

### `review_packet`

Ключові файли:

- `reports/review_packet._coordinator.md`
- `reports/review_packet.<person_id>.md`

Кожен routed item має stable identity, source kind, routing state, primary role, primary person, secondary reviewers і next action.

Найважливіші routing states:

| Routing state | Як це читати |
| --- | --- |
| `assigned` | item вже має зрозумілого owner/reviewer |
| `unassigned_owner` | роль існує в contract, але людина не призначена |
| `second_reviewer_required` | одна людина закриває owner і reviewer для критичного item, тому потрібна незалежна друга перевірка |
| `coordinator_escalation` | автоматичної безпечної маршрутизації недостатньо, координатор повинен вирішити item вручну |

Для неінженерних учасників найважливіший файл зазвичай `review_packet._coordinator.md`, бо саме він показує items, які не можна безпечно закрити просто технічним rerun команди.

### `evidence_status`

Файли:

- `reports/evidence_status.yaml`
- `reports/evidence_status.md`

Evidence status дивиться не на “чи є якийсь коментар”, а на силу evidence signal.

Поточна шкала evidence strength:

| Evidence strength | Що це означає |
| --- | --- |
| `none` | evidence відсутній |
| `reference_only` | є згадка або текстове посилання, але немає structured link |
| `structured_ref` | є structured reference у `source_ref`, але без підтвердженого workspace artifact |
| `workspace_artifact` | structured reference веде на реальний файл усередині workspace |

Поточний blocking contract:

| Field | Blocking allowlisted | Minimum blocking strength |
| --- | --- | --- |
| `fat_required` | так | `workspace_artifact` |
| `sat_required` | так | `workspace_artifact` |

Поточна stage matrix:

| Project stage | Evidence behavior |
| --- | --- |
| `concept` | advisory only |
| `basic_design` | advisory only |
| `detailed_design` | blocking allowed for allowlisted fields |
| `build_commission` | blocking allowed for allowlisted fields |

Практичне правило таке:

- `preview` ніколи не блокує stage gate через evidence;
- `evidence` може завершитися non-zero тільки тоді, коли stage дозволяє blocking, field allowlisted, а observed evidence слабший за мінімум.

### `workspace.manifest`

Файл `reports/workspace.manifest.yaml` потрібен для discoverability generated outputs.

Він:

- індексує generated artifacts по producer;
- зберігає детермінований порядок;
- допомагає tooling і reviewers побачити, які outputs зараз materialized;
- не є ручним input-файлом.

## Що Потрібно Знати Різним Учасникам

### Координатор або PM

Вам найчастіше потрібні:

- `preview_status.md`, щоб зрозуміти поточний readiness;
- `review_packet._coordinator.md`, щоб побачити routing gaps;
- `evidence_status.md`, щоб зрозуміти, чи evidence вже достатній для later-stage gate.

### Domain specialist

Вам найчастіше потрібні:

- ваш `review_packet.<person_id>.md`;
- відповідні workbook sheets;
- за потреби, workspace artifact files, на які посилається `source_ref`.

### Архітектор або інженер

Вам найчастіше потрібні:

- `questionnaire.yaml`;
- `requirements.compiled.yaml`;
- `graphs.summary.yaml`;
- `validation.summary.yaml`;
- `reviewer_registry.yaml` і `evidence_status.yaml`, якщо треба машинна обробка routed findings.

### Неінженерний sponsor або reviewer

Вам зазвичай достатньо:

- `preview_status.md` для питання “чи ми готові до baseline discussion?”;
- `review_packet._coordinator.md` для питання “що ще не розкладено по відповідальних?”;
- `evidence_status.md` для питання “чи є підтвердження FAT/SAT obligations там, де це вже повинно бути?”.

## Safe Overwrite Rules

- `generate` може перебудовувати workbook structure; з `--preserve-responses` він не повинен стирати вже внесені значення.
- `compile` оновлює compiled canonical artifacts.
- `preview`, `review` і `evidence` перегенеровують свої derived outputs під `reports/`.
- `review` і `evidence` не створюють нового editable source of truth.
- `demo happy` і `demo stress` працюють у temporary copy, тому їх безпечно використовувати як smoke-check.

## Типові Питання

### Чому `preview` зелений, а `evidence` усе ще показує gaps?

Тому що це різні питання. `preview` говорить про baseline readiness і pipeline health. `evidence` говорить про якість підтвердження для selected fields. На ранніх stages це може бути advisory warning, а не blocker.

### Чому `project/intake evidence` завершився non-zero?

Тому що blocking gate failed у narrow tested scope. Перевіряйте `reports/evidence_status.md` і `reports/review_packet._coordinator.md`. У поточному `v1` це стосується лише allowlisted fields і лише на blocking-allowed stages.

### Чому деякий item пішов у coordinator packet, а не до конкретної людини?

Тому що automatic routing не зміг довести безпечного single-owner outcome. Типові причини: відсутнє person assignment, потрібен second reviewer, або item має неоднозначне routing target.

### Чи можна редагувати `review_packet.*` або `evidence_status.*` вручну?

Ні. Це generated reports. Виправляти треба вихідні answers, role assignments або evidence references, після чого слід перегенерувати reports.

### Чому manifest важливий, якщо люди його майже не читають?

Він важливий для traceability і tooling. Це короткий індекс generated outputs у workspace, який дає стабільну картину того, які derived artifacts зараз існують і ким вони були згенеровані.
