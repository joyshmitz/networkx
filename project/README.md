# Network Methodology Sandbox

`project/` ізолює human-facing intake workflow, methodology contracts і NetworkX-backed analysis tooling від upstream коду `networkx`. Саме тут role-based questionnaire intake перетворюється на compiled object profile, normalized requirements model, routed review packets, evidence status і derived reports для handoff.

## Поточний Стан

Human-facing intake layer `v1` завершений на гілці `research/methodology-foundation-clean`.

Поточний baseline включає:

- стабільну operator surface через `project/intake`;
- детерміновану поведінку `generate`, `compile` і `preview` з fixed-date support;
- routed review packets для координаторів і specialist reviewers;
- advisory evidence status плюс narrow blocking evidence gate;
- generated artifact index у `reports/workspace.manifest.yaml`;
- останній verification baseline: `project/intake verify` -> `284 passed`.

## З Чого Почати

| Якщо вам потрібно... | Почніть із цього документа |
| --- | --- |
| щоденно вести intake workspace | `docs/methodology/INTAKE_OPERATOR_GUIDE.md` |
| зрозуміти workflow між ролями та stages | `docs/methodology/QUESTIONNAIRE_WORKFLOW.md` |
| зрозуміти ownership і review responsibilities | `docs/methodology/ROLE_MAP.md` |
| зрозуміти methodology boundaries і human interaction rules | `docs/methodology/HUMAN_INTERACTION_MODEL.md` |
| подивитися, що саме доставив `v1` і що лишилося поза scope | `docs/reviews/V1_CLOSEOUT_2026-04-03.md` |
| переглянути historical plans і review history | `docs/plans/` і `docs/reviews/` |

## Що Є В Каталозі

| Розділ | Призначення |
| --- | --- |
| `docs/decisions/` | decision log і architectural rationale |
| `docs/methodology/` | human workflow, role model, module boundaries, operator guidance |
| `docs/plans/` | historical execution plans і planning records |
| `docs/reviews/` | historical release notes, review briefs, corrective follow-ups, close-out records |
| `specs/` | declarative questionnaire, dictionary, evidence, review і requirements contracts |
| `src/` | compilers, validators, report generators, intake commands і shared data layers |
| `examples/` | checked-in example workspaces для happy-path і stress-path verification |

## Операторська Поверхня

Канонічна operator-facing поверхня проходить через shell wrapper `project/intake`.

| Команда | Коли зазвичай використовується | Основні outputs |
| --- | --- | --- |
| `project/intake generate <workspace> [--date ...] [--preserve-responses]` | підготувати або оновити role-based workbooks і guides | `intake/generated/*.guide.md`, `intake/responses/*.xlsx` |
| `project/intake compile <workspace> [--date ...]` | скомпілювати workbook answers у canonical artifacts | `questionnaire.yaml`, `intake/responses/*.response.yaml`, `reports/intake_status.*`, `reports/workspace.manifest.yaml` |
| `project/intake preview <workspace> [--date ...]` | вирішити, чи workspace уже baseline-ready | pipeline reports під `reports/`, `reports/preview_status.*`, `reports/workspace.manifest.yaml` |
| `project/intake review <workspace> [--date ...]` | розкласти unresolved items і findings по ролях та людях | `reports/reviewer_registry.*`, `reports/review_packet.*`, `reports/workspace.manifest.yaml` |
| `project/intake evidence <workspace> [--date ...]` | оцінити evidence strength і, де це дозволено policy, застосувати narrow stage gate | `reports/evidence_status.*`, `reports/workspace.manifest.yaml` |
| `project/intake verify [pytest args...]` | прогнати regression suite | лише test output |
| `project/intake demo happy|stress [--date ...]` | відтворити checked-in exemplars у temporary copy | лише temporary workspace |

На практиці важливі два правила:

- `preview` відповідає за readiness summary і перезаписує generated reports, але не застосовує blocking evidence gate.
- `evidence` є єдиною operator command, яка може завершитися non-zero через missing evidence, і навіть це відбувається лише в narrow, tested blocking scope, описаному в operator guide.

## Модель Workspace

Один workspace містить три типи артефактів.

### 1. Людські input-артефакти

- `role_assignments.yaml`
- `intake/responses/*.xlsx`

Це матеріали, які люди справді заповнюють і підтримують під час intake.

### 2. Compiled canonical artifacts

- `questionnaire.yaml`
- `intake/responses/*.response.yaml`
- `reports/intake_status.yaml`
- `reports/intake_status.md`

Ці файли фіксують normalized, machine-readable стан зібраних відповідей.

### 3. Derived reports

- pipeline reports such as `requirements.compiled.yaml`, `graphs.summary.yaml`, and `validation.summary.yaml`
- `reports/preview_status.yaml` and `reports/preview_status.md`
- `reports/reviewer_registry.yaml`, `reports/reviewer_registry.md`, and `reports/review_packet.*.md`
- `reports/evidence_status.yaml` and `reports/evidence_status.md`
- `reports/workspace.manifest.yaml`

Derived reports потрібні для review, coordination і downstream work. Це generated artifacts, а не ще один editable source of truth.

## Execution Contract

Команди слід запускати з кореня репозиторію.

- interpreter: `.venv/bin/python`
- test/runtime import contract: `PYTHONPATH=.`
- coordinator-facing surface: `project/intake ...`
- raw Python commands лишаються underlying execution contract для maintainers і debugging

Bootstrap:

```bash
python3 -m venv .venv
.venv/bin/pip install -r project/requirements.txt jsonschema pytest
```

Canonical verify:

```bash
project/intake verify
```

Raw command examples:

```bash
PYTHONPATH=. .venv/bin/python project/src/intake/generate_intake_sheets.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/compile_intake.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/preview_status.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/review_packets.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/evidence_status.py project/examples/sample_object_01 --date 2026-04-02
```

## Правила Регенерації Та Overwrite

- використовуйте explicit `--date YYYY-MM-DD`, коли потрібна deterministic exemplar regeneration;
- `generate --preserve-responses` оновлює workbook structure без втрати вже заповнених `E/F/G/H` cells;
- `preview`, `review` і `evidence` можуть безпечно overwrite-ити власні generated outputs під `reports/`;
- `demo happy` і `demo stress` працюють у temporary copy й не повинні переписувати tracked example workspaces.

## Історичний Контекст

`v0` і `v1` plans лишаються в repository для traceability. Їх тепер слід читати як historical execution records, а не як active implementation backlog. Поточний operator-facing reference: `docs/methodology/INTAKE_OPERATOR_GUIDE.md`. Поточний milestone summary: `docs/reviews/V1_CLOSEOUT_2026-04-03.md`.
