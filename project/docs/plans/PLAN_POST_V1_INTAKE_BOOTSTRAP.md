# Post-v1 Intake Workspace Bootstrap

> **ARCHIVAL STATUS:** superseded draft.  
> This bootstrap skeleton is kept only for traceability.  
> It was superseded by [PLAN_CF2_BOOTSTRAP_FINAL.md](PLAN_CF2_BOOTSTRAP_FINAL.md) and is no longer an active planning document.

**Дата:** 2026-04-03  
**Гілка на момент створення:** `research/methodology-foundation-clean`  
**Статус:** superseded historical draft  
**Related baseline:** `project/docs/reviews/V1_CLOSEOUT_2026-04-03.md`  
**Related operator doc:** `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`  
**Related planning context:** `project/docs/methodology/INTAKE_MASTER_NOTE.md`

## Призначення

Цей документ фіксує окрему post-`v1` planning-задачу для bootstrap/init problem у human-facing intake workflow.

Його мета не в тому, щоб "ще трохи доробити `v1`", а в тому, щоб окремо оформити конкретний workflow gap, який проявився під час реального operator сценарію:

- користувач природно очікує, що `project/intake generate <workspace>` є стартовою командою для нового об'єкта;
- поточна реалізація цього не робить;
- без попередньо створеної папки і без `role_assignments.yaml` команда не може почати роботу.

## Problem Statement

На поточному baseline `project/intake generate` працює лише всередині вже існуючого workspace і очікує, що в ньому вже лежить `role_assignments.yaml`.

Це створює розрив між очікуванням користувача і реальною поведінкою системи.

Симптом виглядає так:

- користувач створює нову назву workspace;
- запускає `project/intake generate <workspace> --date ...`;
- отримує `Workspace not found`, хоча з його точки зору це і є старт workflow.

## Чому Це Варто Виносити В Окремий План

Це не дрібна косметика в docs. Це проблема точки входу в workflow.

Поки bootstrap-крок не оформлений явно, маємо три наслідки:

- новий користувач з високою ймовірністю впирається в помилку на першій команді;
- operator guide змушений пояснювати manual workaround там, де природніше було б мати явний productized step;
- реальний початок роботи з новим об'єктом залишається напівручним і залежним від знання exemplar-ів або внутрішніх деталей.

## Поточна Правда

Поточний baseline слід вважати правильним до моменту окремого рішення. На сьогодні правда така:

- `generate` не bootstrap-ить нову папку об'єкта;
- `generate` не створює стартовий `role_assignments.yaml`;
- без існуючого workspace команда не стартує;
- safe workaround: створити папку вручну, додати `role_assignments.yaml`, потім запускати `generate`.

Цей план не повинен переписувати цю правду заднім числом.

## Ціль

Зробити старт нового intake workspace більш природним і менш крихким для користувача, який не живе всередині repo.

У кінці роботи користувач повинен мати очевидний і документований спосіб почати новий об'єкт без читання exemplar-ів і без здогадок, які файли треба створити руками перед першою командою.

## Не-Цілі

Цей план свідомо не включає:

- зміну compile / preview / review / evidence contracts;
- зміну evidence policy;
- зміну routing logic;
- нові external integrations;
- notifications;
- нові intake modes поза bootstrap/start problem;
- redesign усього operator surface.

## Рекомендований Напрямок

Рекомендований напрямок для цього post-`v1` gap:

### окрема команда `project/intake init <workspace>`

Саме цей варіант найкраще відповідає здоровій CLI-практиці й найчіткіше відділяє дві різні дії:

- `init` створює мінімальний skeleton нового workspace;
- `generate` створює або оновлює role-based workbooks усередині вже ініціалізованого workspace.

Чому саме так:

- це відповідає звичній CLI-логіці на кшталт `git init`, `npm init`, `cargo init`;
- це не розмиває поточну семантику `generate`;
- це дає прості overwrite rules: `init` ініціалізує, `generate` регенерує;
- це краще читається mixed audience користувачами, для яких "одноразовий старт" і "повторна генерація" є різними діями.

## Відхилені Альтернативи

### 1. Розширити `project/intake generate`

Цей варіант вважається слабшим, бо:

- `generate` уже має власну чітку роль;
- додавання bootstrap semantics створює overloaded command;
- `--preserve-responses` і bootstrap живуть у різних mental models;
- implicit behavior на кшталт "path не існує -> bootstrap" погіршує ясність contract.

### 2. Окремий generator лише для `role_assignments.yaml`

Цей варіант теж слабший, бо вирішує не весь start problem:

- користувачеві все одно потрібно окремо створювати папку;
- старт workflow розпадається на надто технічні дрібні кроки;
- проблема користувача полягає не в одному файлі, а в неочевидному entry point для нового об'єкта.

## Proposed Work Breakdown

### Milestone 0 — Contract Decision

Потрібно вирішити:

- остаточний CLI contract для `project/intake init <workspace>`;
- який мінімальний набір артефактів створює `init`;
- як саме використовується існуючий template `project/specs/questionnaire/role_assignments.template.yaml`;
- як `init` поводиться на вже існуючому або частково ініціалізованому workspace.

### Milestone 1 — Minimal Bootstrap Artifact Set

Потрібно визначити мінімальний skeleton для нового workspace:

- каталог workspace;
- `role_assignments.yaml`, materialized з `project/specs/questionnaire/role_assignments.template.yaml` з підстановкою `object_id = basename(workspace path)`;
- зрозумілий operator message про наступний крок.

Принципово не потрібно створювати порожні `intake/` і `reports/` каталоги на цьому кроці.
Їх already-existing runtime commands і так materialize-ять тоді, коли це справді потрібно.

### Milestone 2 — Operator Surface

Потрібно materialize user-facing contract:

- нова команда `project/intake init <workspace>`;
- help text;
- safe overwrite rules для нового й уже існуючого workspace;
- короткий post-init message з наступною дією;
- deterministic behavior на вже існуючому workspace.

### Milestone 3 — Docs and Verification

Потрібно оновити:

- `INTAKE_OPERATOR_GUIDE.md`;
- `README.md`, якщо зміниться recommended entry point;
- tests на bootstrap flow;
- demo або exemplar smoke path, якщо це доречно.

## Acceptance Criteria

План вважатиметься успішно виконаним, якщо:

- існує один явний, документований спосіб почати новий workspace;
- новий користувач не впирається в `Workspace not found` на першій команді без зрозумілого альтернативного шляху;
- стартовий `role_assignments.yaml` з'являється через підтримуваний contract на базі існуючого template, а не через ручне копіювання exemplar-а;
- `generate` і bootstrap semantics не конфліктують між собою;
- docs описують новий стартовий шлях простою мовою;
- regression tests покривають happy-path bootstrap contract.

## Основні Ризики

- розмити межу між bootstrap command і generate command;
- додати занадто "розумний" automation step, який важко пояснити користувачу;
- створити порожній workspace skeleton, який виглядає валідним, але ще не придатний до реальної роботи;
- випадково ввести destructive overwrite semantics для вже існуючих workspace-ів.

## Known Inputs And Open Questions

Що вже відомо і не є open question:

- template already exists: `project/specs/questionnaire/role_assignments.template.yaml`;
- bootstrap не повинен створювати порожні `intake/` і `reports/` каталоги;
- recommended entry point: окрема команда `project/intake init <workspace>`.

Що ще лишається open:

- чи `init` повинен працювати лише на неіснуючому/порожньому шляху, чи й на partially initialized workspace;
- який саме текст post-init message найкраще замикає user flow;
- чи потрібні майбутні presets або `--template` options, чи це слід свідомо відкласти;
- як найкраще поєднати цей flow з майбутнім реальним object onboarding, а не лише з exemplars.

## Existing Template Reality

Bootstrap plan повинен спиратися на вже наявний template:

- `project/specs/questionnaire/role_assignments.template.yaml`

Цей template already contains:

- `version`
- `questionnaire_id`
- `template_id`
- `description_uk`
- `rules`
- generic example assignments

Bootstrap contract не повинен ігнорувати цей файл і не повинен змушувати користувача копіювати exemplar `role_assignments.yaml` вручну.

## Verification Strategy

Мінімальна перевірка майбутнього рішення повинна включати:

- створення нового workspace у temporary path;
- успішний materialization стартового skeleton;
- перевірку, що `object_id` коректно підставляється з імені workspace;
- наступний успішний запуск `generate`;
- перевірку, що вже існуючий workspace не ламається від нового bootstrap contract;
- чіткі помилки для небезпечних або неоднозначних сценаріїв.

## Expected Post-Init UX

Після успішного `init` оператор повинен одразу побачити наступний крок, без потреби вгадувати його з docs.

Мінімальне очікування:

```text
Workspace initialized. Edit role_assignments.yaml, then run:
project/intake generate <workspace>
```

## Closing Note

Цей документ поки що є skeleton, а не затвердженим execution plan. Його задача проста: не дати реальній workflow problem загубитися в `Master Note` або в усній домовленості, і підготувати чисту основу для окремого post-`v1` рішення.
