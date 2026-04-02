# Human-Facing Intake Layer v0

**Дата:** 2026-04-02  
**Гілка:** `research/methodology-foundation-clean`  
**Статус:** v0 formally released; operational current-state contract after Stage 0-8  
**Останній branch verify:** `PYTHONPATH=. .venv/bin/python -m pytest project/tests -q` -> `242 passed`

## Current State

v0 intake layer більше не є design-only plan. На цій гілці він існує як executable workflow з checked-in exemplars, fixed-date regeneration policy, formal branch gates і operator-facing command surface.

Що вже materialized:

- Happy-path exemplar: `project/examples/sample_object_01`
  - fixed date `2026-04-02`
  - `41/41 answered`
  - `_unassigned.xlsx` present for 4 fields without assigned person
  - pipeline green, `resolved_archetype: video_heavy_site`
- Stress-path exemplar: `project/examples/sample_object_02`
  - fixed date `2026-04-02`
  - `29 answered / 7 tbd / 5 unanswered`
  - no `_unassigned.xlsx`
  - pipeline fails only on domain constraints
  - expected error validators: `resilience`, `time`

Actual ownership/person model:

- Field ownership source of truth: `project/specs/questionnaire_v2_fields.yaml`
- Person-to-role assignment input: `role_assignments.yaml`
- Generate emits one workbook per assigned person
- If some owner roles have no assigned person, generate emits `_unassigned.xlsx`
- Coordinator/operator runs generate, compile, verify, and demo commands; respondents edit only `.xlsx`

Actual `_values` policy:

- Every generated workbook contains hidden `_values` and locked `_reference` sheets
- Enum cells in column `E` use descriptive labels in the form `code — label`
- Compile strips everything after ` — ` and writes canonical value codes into `questionnaire.yaml`
- `tbd` / `not_applicable` are controlled through status column `F`, not through free-text comments

Recent v0 commits on this branch:

- `60e881cac` `test(intake): freeze happy-path golden contract`
- `b419d0dee` `test(intake): materialize stress-path exemplar`
- `33207e52d` `test(intake): add formal branch gates`
- `4ee038908` `feat(intake): add operator command surface`

## Execution Contract

Canonical runtime:

- working directory: repository root
- interpreter: `.venv/bin/python`
- `PYTHONPATH=.`

Bootstrap:

```bash
python3 -m venv .venv
.venv/bin/pip install -r project/requirements.txt jsonschema pytest
```

Canonical verify:

```bash
PYTHONPATH=. .venv/bin/python -m pytest project/tests -q
```

Canonical raw CLI:

```bash
PYTHONPATH=. .venv/bin/python project/src/intake/generate_intake_sheets.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/intake/compile_intake.py project/examples/sample_object_01 --date 2026-04-02
PYTHONPATH=. .venv/bin/python project/src/run_pipeline.py project/examples/sample_object_01/questionnaire.yaml
```

Canonical operator-facing surface:

```bash
project/intake generate project/examples/sample_object_01 --date 2026-04-02
project/intake compile project/examples/sample_object_01 --date 2026-04-02
project/intake verify
project/intake demo happy
project/intake demo stress
```

Operator surface rules:

- no canonical command relies on `python` alias
- `project/intake ...` is the short coordinator-facing surface
- raw `PYTHONPATH=. .venv/bin/python ...` commands remain the execution contract underneath
- `demo` replays checked-in exemplars in a temporary copy and must not rewrite tracked files

## Artifact Policy

Tracked source-of-truth artifacts:

- `role_assignments.yaml`
- filled `intake/responses/*.response.yaml`
- compiled `questionnaire.yaml`
- `reports/intake_status.yaml`
- `reports/intake_status.md`

Tracked demo artifacts:

- `intake/responses/*.xlsx`
- `intake/generated/*.guide.md`

Happy-path golden set:

- `questionnaire.yaml`
- `intake/generated/*.guide.md`
- `intake/responses/*.xlsx`
- `intake/responses/*.response.yaml`
- `reports/intake_status.yaml`
- `reports/intake_status.md`

Excluded from Gate B by design:

- `reports/requirements.compiled.yaml`
- `reports/graphs.summary.yaml`
- `reports/validation.summary.yaml`
- `reports/network_volume_summary.md`
- `reports/handoff_matrix.md`
- `reports/pipeline.manifest.yaml`

Compile normalization contract:

- `answered` -> write canonical value
- `tbd` -> emit string `tbd`
- `not_applicable` -> emit `tbd` in `questionnaire.yaml`, preserve actual status in `intake_status`
- `unanswered` -> omit field from `questionnaire.yaml`, making it eligible for archetype defaults

Fixed-date regenerate contract:

- Approved exemplar date for v0: `2026-04-02`
- Checked-in exemplar updates must use explicit `--date 2026-04-02`
- Authoritative happy-path drift check is Gate B:

```bash
PYTHONPATH=. .venv/bin/python -m pytest project/tests/test_intake_happy_path_golden.py -q
```

What Gate B actually proves:

- regenerate happy-path workspace with fixed date
- hydrate generated `.xlsx` from approved exemplar content
- compile back to `questionnaire.yaml`
- compare the approved golden files byte-for-byte

Drift policy:

- allowed drift: intentional source/spec/code changes with explicit exemplar refresh
- disallowed drift: date-only churn, workbook metadata noise, unexplained exemplar deltas

## Verified Gates

Gate A: happy-path roundtrip

- test: `project/tests/test_intake_branch_gates.py::test_gate_a_happy_path_roundtrip`
- proves: `generate -> fill -> compile -> pipeline` for `sample_object_01`
- expected result: `41/41 answered`, pipeline `status: ok`, `0 errors`, `0 assumptions`

Gate B: happy-path drift

- test: `project/tests/test_intake_happy_path_golden.py::test_happy_path_regeneration_matches_checked_in_golden`
- proves: fixed-date regeneration matches approved happy-path golden artifacts byte-for-byte

Gate C: stress-path partial roundtrip

- test: `project/tests/test_intake_branch_gates.py::test_gate_c_stress_path_partial_roundtrip`
- proves: `generate -> partial fill -> compile -> pipeline` for `sample_object_02`
- expected result: `29 answered / 7 tbd / 5 unanswered`, pipeline `status: failed`, `error_count: 2`

Gate D: stress expected-failure contract

- test: `project/tests/test_intake_branch_gates.py::test_gate_d_stress_expected_failure_contract`
- proves:
  - exact failing validators are `resilience` and `time`
  - failure messages still mention `redundancy_target` and `PTP`
  - no `role_assignments` / workflow glue failure is present

Gate E: full branch verify

- command: `PYTHONPATH=. .venv/bin/python -m pytest project/tests -q`
- current result: `242 passed`

Operational evidence behind those gates:

- Happy-path pipeline smoke: `project/intake demo happy` -> green
- Stress-path smoke: `project/intake demo stress` -> expected domain failure with exit 1 from pipeline and success from wrapper

## Open Gaps

No open v0 execution blockers remain inside Stage 0-7 scope.

Remaining non-blocking items:

- `project/intake demo` keeps default date `2026-04-02` in shell script and must stay manually aligned with the approved golden date
- Gate B intentionally excludes pipeline reports; those artifacts are covered by roundtrip and pipeline gates instead of byte-for-byte golden comparison
- Secondary cleanup track is still deferred:
  - shared `PHASE_MAP`
  - shared YAML helper reuse
  - explicit `not_applicable -> tbd` coverage expansion if needed beyond current tests

## Deferred v1 Backlog

These items remain explicitly out of scope until the formal v0 release gate is acknowledged:

- reviewer sheets
- preview / `baseline_ready`
- `--preserve-responses`
- evidence enforcement
- validator-to-person automation
- any new intake mode
- methodology expansion not required to preserve current v0 behavior

Release discipline:

- no v1 work before formal v0 release gate
- no exemplar drift without explicit source/spec/code change
- no relaxation of Stage A-E gates to “make progress”
