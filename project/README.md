# Network Methodology Sandbox

Каталог `project/` відокремлює користувацький intake-процес, методологічні правила й допоміжні інструменти аналізу від основного коду `networkx`. Саме тут рольове анкетування по об'єкту перетворюється на зведений профіль, погоджену модель вимог, пакети на перевірку, звіти про підтвердження та інші робочі матеріали для подальшої інженерної роботи.

## Поточний Стан

Користувацький intake-шар `v1` завершений і зафіксований на продуктовій гілці `app-main`.

Поточний базовий набір можливостей включає:

- стабільну командну поверхню через `project/intake`;
- окрему команду `project/intake init` для створення нової робочої папки;
- детерміновану поведінку `generate`, `compile` і `preview` з підтримкою фіксованої дати;
- розкладені пакети на перевірку для координаторів і профільних перевіряльників;
- попереджувальний звіт про підтвердження плюс вузьке блокувальне етапне обмеження;
- YAML-каталог міжпольових правил виведення і окремий шар семантичної узгодженості;
- індекс згенерованих артефактів у `reports/workspace.manifest.yaml`;
- останній підтверджений результат перевірки: `project/intake verify` -> `335 passed`.

Є ще одна неприємна, але важлива правда. Продукт уже живе в `project/`, а не в бібліотечному коді `networkx/`. Тому репозиторій більше не слід читати як "форк бібліотеки з якоюсь додатковою папкою". Поточна стратегія репозиторію описана в [REPO_STRATEGY.md](../REPO_STRATEGY.md), стратегічний план відділення описаний у [PLAN_APP_REPO_EXTRACTION.md](docs/plans/PLAN_APP_REPO_EXTRACTION.md), а [PLAN_APP_DEPENDENCY_DECOUPLING.md](docs/plans/PLAN_APP_DEPENDENCY_DECOUPLING.md) тепер слід читати не як головний фронт роботи, а як майже виконаний execution plan фази розриву залежностей із одним залишковим repo-root боргом навколо `project/intake` і fallback `.venv`.

## З Чого Почати

| Якщо вам потрібно... | Почніть із цього документа |
| --- | --- |
| зрозуміти, які документи зараз активні, а які лише історичні | [docs/README.md](docs/README.md) |
| щоденно вести intake по робочій папці | [INTAKE_OPERATOR_GUIDE.md](docs/methodology/INTAKE_OPERATOR_GUIDE.md) |
| зрозуміти repo-рішення і чому `project/` уже є продуктом | [REPO_STRATEGY.md](../REPO_STRATEGY.md) |
| зрозуміти наступну стратегічну фазу після стабілізації `v1` | [PLAN_APP_REPO_EXTRACTION.md](docs/plans/PLAN_APP_REPO_EXTRACTION.md) |
| перевірити, що вже доставила фаза dependency decoupling і який залишковий борг ще відкритий | [PLAN_APP_DEPENDENCY_DECOUPLING.md](docs/plans/PLAN_APP_DEPENDENCY_DECOUPLING.md) |
| зрозуміти послідовність роботи між ролями та етапами | [QUESTIONNAIRE_WORKFLOW.md](docs/methodology/QUESTIONNAIRE_WORKFLOW.md) |
| зрозуміти зони відповідальності та правила перевірки | [ROLE_MAP.md](docs/methodology/ROLE_MAP.md) |
| зрозуміти межі методології та правила людської взаємодії | [HUMAN_INTERACTION_MODEL.md](docs/methodology/HUMAN_INTERACTION_MODEL.md) |
| подивитися, що саме доставив baseline `v1` і що лишилося поза межами того етапу | [V1_CLOSEOUT_2026-04-03.md](docs/reviews/V1_CLOSEOUT_2026-04-03.md) |
| переглянути історичні плани й попередні підсумки перевірок | `docs/plans/` і `docs/reviews/` |

## Що Є В Каталозі

| Розділ | Призначення |
| --- | --- |
| `docs/decisions/` | журнал рішень та архітектурні пояснення |
| `docs/README.md` | карта активних і історичних документів |
| `docs/methodology/` | опис робочого процесу, ролей, меж модулів і користувацьких правил |
| `docs/plans/` | поточний стратегічний план відділення, execution-план вже майже закритої фази decoupling і історичні плани |
| `docs/reviews/` | підсумки релізів, матеріали перевірок і коригувальні нотатки |
| `specs/` | декларативні контракти анкети, словника, підтверджень, перевірки та вимог |
| `src/` | компілятори, перевірки, генератори звітів, intake-команди та спільні шари даних |
| `examples/` | приклади робочих папок для звичайного й напруженого сценаріїв |

## Командна Поверхня

Основний користувацький вхід проходить через shell-обгортку `project/intake`.

| Команда | Коли зазвичай використовується | Основні результати |
| --- | --- | --- |
| `project/intake init <workspace> [--object-id ...]` | почати новий об'єкт і створити стартову робочу папку | `role_assignments.yaml` |
| `project/intake generate <workspace> [--date ...] [--preserve-responses]` | підготувати або оновити рольові таблиці та пояснювальні файли | `intake/generated/*.guide.md`, `intake/responses/*.xlsx` |
| `project/intake compile <workspace> [--date ...]` | звести відповіді з таблиць у погоджені артефакти | `questionnaire.yaml`, `intake/responses/*.response.yaml`, `reports/intake_status.*`, `reports/workspace.manifest.yaml` |
| `project/intake preview <workspace> [--date ...]` | вирішити, чи робоча папка вже придатна як базовий стан | технічні звіти під `reports/`, `reports/preview_status.*`, `reports/workspace.manifest.yaml` |
| `project/intake review <workspace> [--date ...]` | розкласти незакриті питання та зауваження по ролях і людях | `reports/reviewer_registry.*`, `reports/review_packet.*`, `reports/workspace.manifest.yaml` |
| `project/intake evidence <workspace> [--date ...]` | оцінити силу підтверджень і, де це дозволяє правило, застосувати вузьке етапне обмеження | `reports/evidence_status.*`, `reports/workspace.manifest.yaml` |
| `project/intake verify [pytest args...]` | прогнати регресійну перевірку | лише вивід тестів |
| `project/intake demo happy|stress [--date ...]` | відтворити приклади у тимчасовій копії | лише тимчасова робоча папка |

На практиці важливі два правила:

- `preview` відповідає за коротке зведення готовності й перезаписує власні згенеровані звіти, але не застосовує блокувальне правило за підтвердженнями.
- `evidence` є єдиною командою для користувача, яка може завершитися з ненульовим кодом через брак підтверджень, і навіть це відбувається лише у вузькому перевіреному обсязі, описаному в operator guide.

## Модель Робочої Папки

Одна робоча папка містить три типи артефактів.

### 1. Людські вхідні артефакти

- `role_assignments.yaml`
- `intake/responses/*.xlsx`

Це матеріали, які люди справді заповнюють і підтримують під час intake.

### 2. Зібрані погоджені артефакти

- `questionnaire.yaml`
- `intake/responses/*.response.yaml`
- `reports/intake_status.yaml`
- `reports/intake_status.md`

Ці файли фіксують нормалізований, машинозчитуваний стан зібраних відповідей.

### 3. Похідні звіти

- звіти технічного конвеєра, зокрема `requirements.compiled.yaml`, `graphs.summary.yaml` і `validation.summary.yaml`
- `reports/preview_status.yaml` та `reports/preview_status.md`
- `reports/reviewer_registry.yaml`, `reports/reviewer_registry.md` та `reports/review_packet.*.md`
- `reports/evidence_status.yaml` та `reports/evidence_status.md`
- `reports/workspace.manifest.yaml`

Ці звіти потрібні для перевірки, координації та подальшої роботи. Це згенеровані артефакти, а не ще одне місце, де руками підтримується джерело істини.

## Виконання Команд

Продукт усе ще не відв'язано від бібліотечного checkout повністю, але канонічний запуск уже більше не повинен спиратися на `PYTHONPATH=.` або на прямий виклик `project/src/...`. Поточний контракт такий: wrapper [project/intake](intake) спочатку шукає `PROJECT_INTAKE_PYTHON`, потім активний `VIRTUAL_ENV/bin/python`, потім product-local `.venv/bin/python`, а поки продукт ще живе всередині цього monorepo, зберігає parent-repo `.venv/bin/python` як сумісний fallback. Канонічний Python-namespace для продукту тепер `network_methodology_sandbox`, і саме він є встановлюваною поверхнею пакета. Старі top-level модулі `intake`, `compiler`, `validators`, `reports`, `model_utils` і `run_pipeline` більше не входять до продуктового install contract і мають вважатися видаленими з підтримуваного API. Залежність від repo-bundled fallback `.venv` лишається відкритим технічним боргом і прямо зафіксована у [PLAN_APP_DEPENDENCY_DECOUPLING.md](docs/plans/PLAN_APP_DEPENDENCY_DECOUPLING.md).

- interpreter for direct commands: активне `python` з встановленим продуктом
- wrapper interpreter resolution: `PROJECT_INTAKE_PYTHON` -> `VIRTUAL_ENV/bin/python` -> product-local `.venv/bin/python` -> parent-repo `.venv/bin/python` as monorepo compatibility fallback
- правило для прямих Python-команд: `python -m network_methodology_sandbox...`, а не `project/src/...`
- правило для нових Python-імпортів: тільки `network_methodology_sandbox...`
- основна командна поверхня для координатора: `project/intake ...`
- прямі Python-команди лишаються службовим інтерфейсом для супроводу та налагодження

Початкове налаштування:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e './project[dev]'
```

Якщо з якоїсь причини потрібен лише прямий список runtime-залежностей без editable install, можна використати `project/requirements.txt`. Але це fallback-шлях, який вимагає `git` і мережевий доступ через VCS-залежність `networkx`. Канонічний шлях для розробки і перевірки тепер саме `pip install -e './project[dev]'`.

Увага: цей спосіб все ще не означає повне відділення від repo root. Продукт уже має явний dependency contract, canonical namespace і чесний installed surface, а shell wrapper тепер достатньо product-root aware, щоб чесно репетирувати extracted layout без hardcode на `project/tests` і `project/examples`. Але командна поверхня все ще живе як shell wrapper у цьому репозиторії та, поки триває monorepo-stage, зберігає parent-repo `.venv` compatibility fallback. Це не дрібниця і не "так і задумано", але це вже не головний фронт переписування Python-межі. Поточна нагальність тепер змістилася в extraction rehearsal, а цей борг лишається як хвіст фази decoupling у [PLAN_APP_DEPENDENCY_DECOUPLING.md](docs/plans/PLAN_APP_DEPENDENCY_DECOUPLING.md).

Канонічна перевірка:

```bash
project/intake verify
```

Приклади прямих команд:

Наведені нижче прямі приклади використовують відносні шляхи `project/...`, тому їх слід запускати з кореня репозиторію. Це службовий шлях для супроводу та налагодження. Канонічний користувацький шлях лишається через `project/intake`, який уже може працювати і з іншого `cwd`.

```bash
python -m network_methodology_sandbox.intake.init_workspace project/examples/my_object
python -m network_methodology_sandbox.intake.generate_intake_sheets project/examples/sample_object_01 --date 2026-04-02
python -m network_methodology_sandbox.intake.compile_intake project/examples/sample_object_01 --date 2026-04-02
python -m network_methodology_sandbox.intake.preview_status project/examples/sample_object_01 --date 2026-04-02
python -m network_methodology_sandbox.intake.review_packets project/examples/sample_object_01 --date 2026-04-02
python -m network_methodology_sandbox.intake.evidence_status project/examples/sample_object_01 --date 2026-04-02
```

## Правила Перегенерації Та Перезапису

- використовуйте явний `--date YYYY-MM-DD`, коли потрібне відтворюване оновлення прикладів;
- `generate --preserve-responses` оновлює структуру робочих таблиць без втрати вже заповнених клітинок `E/F/G/H`;
- `preview`, `review` і `evidence` можуть безпечно перезаписувати власні згенеровані результати під `reports/`;
- `demo happy` і `demo stress` працюють у тимчасовій копії й не повинні переписувати приклади, що зберігаються в репозиторії.

## Історичний Контекст

Плани `v0`, `v1`, bootstrap-етап і review briefs лишаються в репозиторії для простежуваності. Їх слід читати як історичні записи виконання, а не як поточний робочий перелік. Основний користувацький довідник зараз: [INTAKE_OPERATOR_GUIDE.md](docs/methodology/INTAKE_OPERATOR_GUIDE.md). Підсумок зафіксованого baseline `v1`: [V1_CLOSEOUT_2026-04-03.md](docs/reviews/V1_CLOSEOUT_2026-04-03.md). Поточний стратегічний рух уперед: [PLAN_APP_REPO_EXTRACTION.md](docs/plans/PLAN_APP_REPO_EXTRACTION.md). [PLAN_APP_DEPENDENCY_DECOUPLING.md](docs/plans/PLAN_APP_DEPENDENCY_DECOUPLING.md) тепер описує щойно виконану хвилю decoupling і залишковий repo-root debt, а не нову нагальну фазу переписування імпортів.
