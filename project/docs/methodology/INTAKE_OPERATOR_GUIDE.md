# INTAKE_OPERATOR_GUIDE

## Для Кого Цей Гайд

Цей гайд написаний для людини, яка працює з даними по конкретному об'єкту, а не з внутрішньою технічною будовою системи.

Найчастіше це одна з таких ролей:

- координатор intake-процесу;
- спеціаліст, який знає об'єкт, вузол обліку, шафу, канал зв'язку або суміжну частину системи;
- інженер або архітектор, який перевіряє зібраний стан перед подальшою роботою;
- керівник або reviewer, якому треба зрозуміти, що вже зібрано, а що ще ні.

Вам не потрібно наперед знати внутрішні технічні деталі. Для повсякденної роботи достатньо розуміти три речі:

- які файли ви редагуєте руками;
- які команди збирають і перевіряють стан workspace;
- які звіти показують, що ще потрібно доробити.

Якщо вам потрібна історія виконання `v1`, дивіться `docs/reviews/V1_CLOSEOUT_2026-04-03.md`. Якщо вам потрібен внутрішній planning/rehearsal контекст, дивіться `INTAKE_MASTER_NOTE.md`. Якщо вам потрібна загальна картина workflow і розподіл ролей, дивіться `QUESTIONNAIRE_WORKFLOW.md` і `ROLE_MAP.md`. Якщо ж вам треба просто пройти робочий процес по об'єкту, залишайтеся в цьому guide.

## З Чого Почати

Думайте про workspace як про робочу папку одного об'єкта. У ній є те, що люди вносять руками, і те, що система збирає та перевіряє автоматично.

У звичайному сценарії робота виглядає так:

1. Ви або координатор готуєте таблиці для заповнення.
2. Предметні спеціалісти вносять відповіді по своїх ролях.
3. Система збирає ці відповіді у єдиний узгоджений стан.
4. Після цього видно, що ще не заповнено, кому що потрібно перевірити і де бракує підтверджень.

Якщо ви працюєте з енергетичним об'єктом і добре знаєте комерційний облік, але не хочете занурюватися в мережеву реалізацію, цього достатньо як стартової моделі:

- ви редагуєте робочі таблиці, а не службові звіти;
- система збирає з них загальний стан об'єкта;
- звіти після compile показують, що ще не готово;
- окремий звіт про підтвердження показує, чи є достатня підстава для речей на кшталт FAT/SAT, схем, специфікацій, актів, погоджених документів або інших файлів-підстав.

Практичне правило дуже просте:

- `intake/responses/*.xlsx` редагуються вручну;
- `reports/*` руками не редагуються;
- `compile` збирає єдиний стан;
- `review` показує, кому належить наступна дія;
- `evidence` показує, чи достатньо підтверджень для пізньої стадії.

Є ще одна важлива практична деталь на старті. Поточний `v1` не вміє створювати новий workspace "з нуля" лише за назвою папки. Команда `generate` працює всередині вже існуючої робочої папки й очікує, що в ній уже є щонайменше `role_assignments.yaml`.

Якщо ви починаєте новий об'єкт, спочатку потрібно:

- створити папку workspace;
- покласти туди `role_assignments.yaml`;
- тільки після цього запускати `project/intake generate ...`.

Якщо цього файлу або самої папки немає, команда не зможе почати генерацію workbook-ів.

## Що Зазвичай Вважається Підтвердженням

У цьому workflow підтвердженням може бути не лише текстове пояснення, а й конкретний файл або документ, який лежить у workspace чи на який є структуроване посилання.

Для користувача з енергетичної предметної області типовими прикладами будуть:

- схема або однолінійне рішення;
- специфікація, опитувальний лист або документ виробника;
- FAT protocol;
- SAT protocol;
- акт, фото, лист погодження або інший файл, який реально підтверджує заявлене рішення;
- службова або технічна записка, якщо вона збережена у робочій папці об'єкта.

Чим ближче `source_ref` веде до реального файлу всередині workspace, тим сильнішим вважається підтвердження.

## Як Влаштована Робота З Даними

Одна робоча папка об'єкта проходить через три прості кроки:

1. люди дають відповіді у таблицях по ролях;
2. система збирає ці відповіді в єдиний узгоджений опитувальник і технічні звіти;
3. поверх цього з'являються зручні звіти для готовності, перевірки і підтверджень.

Важлива межа така:

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
| `project/intake generate <workspace> [--date ...] [--preserve-responses]` | коли workspace уже існує і треба згенерувати або перебудувати role-based workbooks | генерує role-based workbooks і guide files | `intake/generated/*.guide.md`, `intake/responses/*.xlsx` |
| `project/intake compile <workspace> [--date ...]` | коли відповіді вже внесені і треба отримати canonical payload | компілює workbook answers у canonical questionnaire і compile status | `questionnaire.yaml`, `intake/responses/*.response.yaml`, `reports/intake_status.*`, manifest |
| `project/intake preview <workspace> [--date ...]` | коли треба зрозуміти, чи workspace baseline-ready | перевиконує compile + pipeline через shared snapshot і дає короткий readiness summary | pipeline reports, `reports/preview_status.*`, manifest |
| `project/intake review <workspace> [--date ...]` | коли треба роздати unresolved fields, validator findings і evidence gaps по ролях і людях | будує reviewer registry та routed review packets | `reports/reviewer_registry.*`, `reports/review_packet.*`, manifest |
| `project/intake evidence <workspace> [--date ...]` | коли треба оцінити якість evidence і, за потреби, пройти stage gate | будує evidence status, а в narrow scope ще й blocking gate | `reports/evidence_status.*`, manifest |
| `project/intake verify [pytest args...]` | коли змінюється код, specs або exemplar behavior | запускає regression suite | нічого у workspace не пише |
| `project/intake demo happy|stress [--date ...]` | коли треба показати expected behavior на exemplar workspaces | відтворює happy/stress сценарій у temporary copy | нічого в tracked workspace не пише |

## Рекомендована Послідовність Роботи

### 1. Підготуйте або оновіть workbooks

Перед першим запуском `generate` переконайтеся, що робоча папка об'єкта вже створена і в ній є `role_assignments.yaml`.

Поточний `v1` не bootstrap-ить порожній workspace автоматично. Тобто `generate` не створює нову папку об'єкта сам і не вигадує початковий `role_assignments.yaml` без вашої участі.

Якщо workspace новий:

```bash
project/intake generate project/examples/my_object --date 2026-04-02
```

На практиці для нового workspace послідовність зараз така:

1. створити папку об'єкта;
2. покласти в неї `role_assignments.yaml`;
3. після цього запускати `generate`.

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
