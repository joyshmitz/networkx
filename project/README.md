# Network Methodology Sandbox

Цей каталог ізолює methodology + tooling шар від core коду `networkx`.

## Призначення

- зафіксувати object-first методологію;
- описати декларативні inputs;
- підготувати compile -> validate -> report loop поверх NetworkX;
- не змішувати requirements model із final configs.

## Canonical Model

- `v2` questionnaire/dictionary/mapping є canonical contract для нового skeleton;
- `v1` файли збережені лише як deprecated migration reference;
- `NetworkX` тут analysis engine, а не source of truth;
- source of truth живе у YAML / Markdown contracts.

## Поточний фокус

Фаза 1:

- зафіксувати markdown-ядро методології;
- закласти YAML dictionary / schema foundation;
- підготувати skeleton Python pipeline;
- дати один sample object для end-to-end проходу.

## Структура

- `docs/methodology/` — правила, boundaries, handoff contracts;
- `docs/decisions/` — decision log;
- `docs/reviews/` — зовнішні architecture reviews і corrective feedback;
- `specs/` — декларативні YAML inputs;
- `src/` — compiler / validators / reports;
- `examples/` — sample objects.

## Нові шари skeleton

- `docs/methodology/HUMAN_INTERACTION_MODEL.md` — як questionnaire живе між ролями;
- `docs/methodology/ROLE_MAP.md` — хто власник яких відповідей і хто що рев'ює;
- `docs/methodology/QUESTIONNAIRE_WORKFLOW.md` — stage-gated workflow від intake до as-built;
- `docs/methodology/IMPLEMENTATION_MAPPING.md` — як поля переходять у downstream packs;
- `specs/questionnaire/core_questionnaire_v2.yaml` — object-first core questionnaire v2;
- `specs/questionnaire/role_views.yaml` — role-based views поверх canonical question bank;
- `specs/questionnaire/role_assignments.template.yaml` — як кілька ролей агрегуються по реальних людях;
- `specs/dictionary/questionnaire_v2_fields.yaml` — v2 field contract;
- `specs/dictionary/questionnaire_v2_values.yaml` — controlled vocabulary для v2;
- `specs/questionnaire/annex_*.yaml` — optional annexes з explicit relaxed contract;
- `specs/mappings/implementation_mapping.yaml` — machine-readable mapping field -> artifact.

## Робочий принцип

NetworkX тут використовується як analysis engine.
Source of truth живе у YAML / Markdown.

## Execution Contract

- working directory: repository root;
- interpreter: `.venv/bin/python`;
- `PYTHONPATH=.` для тестів і CLI.

Bootstrap:

```bash
python3 -m venv .venv
.venv/bin/pip install -r project/requirements.txt jsonschema pytest
```

Verify:

```bash
PYTHONPATH=. .venv/bin/python -m pytest project/tests -q
```

Canonical intake/runtime commands:

```bash
PYTHONPATH=. .venv/bin/python project/src/intake/generate_intake_sheets.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/compile_intake.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/run_pipeline.py project/examples/sample_object_01/questionnaire.yaml
```

## Intake Artifact Policy

Tracked source-of-truth artifacts:

- `role_assignments.yaml`
- filled `*.response.yaml`
- compiled `questionnaire.yaml`
- `reports/intake_status.yaml`
- `reports/intake_status.md`

Demo artifacts:

- `intake/responses/*.xlsx`
- `intake/generated/*.guide.md`

Golden/regression artifacts:

- only stable, machine-comparable outputs used for regenerate-and-compare checks

Deterministic regeneration rule:

- checked-in intake exemplars and golden checks must pass explicit fixed `--date YYYY-MM-DD`;
- date-only drift in tracked exemplars is not allowed;
- regeneration drift is allowed only when source/spec/code changed intentionally.

## Happy-Path Golden Contract

Approved golden target: `project/examples/sample_object_01`

Golden files for regenerate-and-compare:

- `questionnaire.yaml`
- `intake/generated/*.guide.md`
- `intake/responses/*.xlsx`
- `intake/responses/*.response.yaml`
- `reports/intake_status.yaml`
- `reports/intake_status.md`

Regenerate procedure for Gate B:

```bash
PYTHONPATH=. .venv/bin/python project/src/intake/generate_intake_sheets.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/compile_intake.py project/examples/sample_object_01 --date 2026-04-02
```

Golden comparison rules:

- compare the approved golden files byte-for-byte;
- no normalization is applied within the golden set;
- `role_assignments.yaml` is a source input, not a regenerated golden output;
- pipeline reports in `reports/requirements.compiled.yaml`, `graphs.summary.yaml`, `validation.summary.yaml`, `network_volume_summary.md`, `handoff_matrix.md`, and `pipeline.manifest.yaml` are excluded from Gate B and covered by roundtrip/pipeline verification instead.
