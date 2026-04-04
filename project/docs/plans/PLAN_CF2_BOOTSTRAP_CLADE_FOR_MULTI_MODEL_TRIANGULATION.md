# Plan: Close Remaining Critical/High Architecture Findings

> **ARCHIVAL STATUS:** superseded triangulation draft.  
> Active execution plan now lives in `project/docs/plans/PLAN_CF2_BOOTSTRAP_FINAL.md`.  
> This document remains in the repo as model-specific review/input traceability.

**Дата:** 2026-04-04
**Гілка:** `research/methodology-foundation-clean`
**Статус:** archived; superseded by `project/docs/plans/PLAN_CF2_BOOTSTRAP_FINAL.md`
**Related baseline:** `project/docs/reviews/V1_CLOSEOUT_2026-04-03.md`
**Related review:** `project/docs/reviews/ARCHITECTURE_REVIEW_2026-04-01.md`

## Призначення

Architecture review (2026-04-01) identified 10 findings (CF-1 through CF-10). After v1 closeout, 8 of 10 resolved. Two remain:

| Finding | Severity | Current State |
|---|---|---|
| CF-2: Compiler lacks cross-field semantic inference | CRITICAL → PARTIAL | Archetype defaults + bool normalization done, but no cross-field business rules |
| Bootstrap/init gap | HIGH | Plan exists (`PLAN_POST_V1_INTAKE_BOOTSTRAP.md`), not implemented |

All 284 tests pass. Parts 1 and 2 have zero file overlap — can be implemented in parallel.

---

## Part 1: Cross-Field Inference Rules (CF-2)

### Чому

Compiler заповнює missing поля з archetype defaults, але зберігає `tbd` values. Коли cross-field evidence робить `tbd` відповідь детермінованою (наприклад, `staffing_model=remote_ops` implies `oob_required=yes`), compiler повинен інферити значення і записати його як assumption. Validators вже попереджають про деякі з цих випадків, але не можуть заповнювати gaps — тільки compiler може.

### Архітектура

Insertion point в `build_requirements_model()`: ПІСЛЯ `apply_archetype_defaults()` (line 207), ПЕРЕД `normalize_boolish_enums()` (line 208).

```
detect_version → load_archetypes → resolve_archetype → apply_archetype_defaults
    → apply_cross_field_inferences (NEW) → normalize_boolish_enums → schema_validate → return
```

Wiring:

```python
inference_assumptions = apply_cross_field_inferences(normalized)
assumptions.extend(inference_assumptions)
```

### Rules (8 rules, data-driven list, 2-pass)

| # | Condition | Target section.field (only if tbd) | Inferred | Rationale |
|---|---|---|---|---|
| 1 | `metadata.criticality_class in {high, mission_critical}` | `resilience.redundancy_target` | `n_plus_1` | High-crit objects need HW redundancy |
| 2 | `object_profile.staffing_model == "remote_ops"` | `security_access.oob_required` | `yes` | Remote sites need OOB for recovery |
| 3 | `is_yes(critical_services.video_required)` | `power_environment.poe_required` | `yes` | IP cameras universally need PoE |
| 4 | `is_yes(critical_services.iiot_required) AND is_yes(critical_services.video_required)` | `power_environment.poe_budget_class` | `heavy` | Combined IIoT + video = high port count |
| 5a | `is_yes(time_sync.timing_required) AND time_sync.timing_accuracy_class in {tens_of_us, sub_us}` | `time_sync.sync_protocol` | `ptp` | High-accuracy demands PTP; NTP cannot achieve sub-ms |
| 5b | `is_yes(time_sync.timing_required) AND timing_accuracy_class NOT in {tens_of_us, sub_us}` (incl. tbd) | `time_sync.sync_protocol` | `ntp` | NTP is safest default when accuracy unknown or ms-level |
| 6 | `security_access.security_zone_model in {strict_isolation, dmz_centric}` | `security_access.audit_logging_required` | `yes` | Security-focused zones require audit trail |
| 7 | `is_yes(critical_services.control_required)` | `time_sync.timing_required` | `yes` | SCADA control loops need time sync |

### Data structure

```python
INFERENCE_RULES = [
    {
        "id": "high_crit_implies_redundancy",
        "target_section": "resilience",
        "target_field": "redundancy_target",
        "inferred_value": "n_plus_1",
        "condition": lambda n: n["metadata"].get("criticality_class") in {"high", "mission_critical"},
        "reason": "High/mission-critical objects need hardware redundancy",
    },
    # ...
]
```

### Key invariants

- Boolean-ish conditions MUST use `is_yes()`/`is_no()` from `model_utils.py` — at inference time, `normalize_boolish_enums()` has not yet run, so values may be Python `True`/`False` not `"yes"`/`"no"`. Enum fields (criticality_class, staffing_model, security_zone_model) are always strings — direct comparison safe.
- Rules only fire on tbd/missing values — never override explicit answers.
- Each inference recorded as assumption with `source: "inference:<rule_id>"`.
- Two-pass execution — second pass handles the one known cascade (rule 7 → rule 5). Comment documents WHY two passes. If rules grow beyond ~15 or cascade depth > 1, migrate to `while changed` with max_iterations.
- Archetype defaults run BEFORE inference. If an archetype fills a field with a concrete value, inference will NOT override it. This is intentional: archetype defaults represent the design basis for that archetype class. The validator (not inference) catches inconsistencies. Required regression test: verify archetype default blocks inference even when condition is met.
- All 12 EXPECTED_V2_SECTIONS guaranteed to exist in `normalized` after `apply_archetype_defaults()` (lines 91-100).

### Inference → graph → validator cascade

Inference affects validators through TWO paths:

1. **Direct:** inferred values change validator input (e.g., `oob_required=yes` → no OOB warning).
2. **Mediated:** inferred values change graph topology — `compile_graphs.py` reads `redundancy_target` (lines 105, 174, 317) and `sync_protocol` (line 187). Rule 1 → secondary firewall + WAN backup in physical graph. Rule 5a → PTP grandmaster node.

This is correct behavior: graphs should reflect requirements, including inferred ones.

### Inference + review = self-confirming loop

Inference and review are complementary, not contradictory:

1. Questionnaire: `oob_required = tbd`
2. Pipeline inference: `oob_required → yes` (assumption recorded)
3. Preview: shows "oob_required unresolved S4" (from raw questionnaire)
4. Review: routes oob_required to operations_engineer
5. Human confirms: sets `oob_required = yes` explicitly
6. Next run: inference is a no-op

No `auto_resolvable` annotation needed in preview — preview showing "unresolved" is accurate (questionnaire still has tbd) and actionable (human should confirm).

### Fix stage_confidence messages

`validate_stage_confidence.py:113` says "filled from archetype defaults" for ALL assumptions — becomes inaccurate when inference assumptions are in the list. Fix:

```python
archetype_count = sum(1 for a in assumptions if a.get("source", "").startswith("archetype:"))
inference_count = sum(1 for a in assumptions if a.get("source", "").startswith("inference:"))
parts = []
if archetype_count:
    parts.append(f"{archetype_count} from archetype defaults")
if inference_count:
    parts.append(f"{inference_count} from cross-field inference")
source_detail = ", ".join(parts)
```

Apply to warning (line 113) and error (line 123) messages.

### Test impact (sample_object_02)

Only Rule 2 fires: `staffing_model=remote_ops` + `oob_required=tbd` → infer `yes`.

sample_object_01: all fields explicit, zero rules fire.

Warning count drops by 2: OOB warning gone + tbd-count warning gone (4→3 tbd fields, threshold `> 3` = False).

**Tests that need updating:**

| Test | Change |
|---|---|
| `test_pipeline_e2e.py:113` `test_remaining_tbd_fields_preserved` | Remove `oob_required == "tbd"` assertion |
| `test_pipeline_e2e.py:103` `test_expected_assumptions_from_unanswered_fields` | Add `"oob_required"` to expected set |
| `test_pipeline_e2e.py:143` `test_oob_warning_visible` | Invert: assert OOB warning ABSENT (inference resolved it) |
| `test_pipeline_e2e.py:100` `test_has_warnings` | Change `>= 5` to `>= 3` |

**Tests NOT affected (regression guards):**

| Test | Why safe |
|---|---|
| `test_pipeline_e2e.py:65` `test_zero_assumptions` | sample_01 all explicit — primary guard against rules firing on non-tbd |
| `test_pipeline_e2e.py:159` `test_schema_valid_with_tbd` | Schema validation of post-inference model |
| `test_intake_preview.py:76` unresolved_s4_ids | Preview reads raw questionnaire, not post-inference |
| `test_intake_review.py:53` oob_required review item | Review routes from questionnaire, not post-inference |
| Golden byte-for-byte test (sample_01) | Zero rules fire, output unchanged |

**New tests** (`project/tests/test_inference_rules.py`, ~100 LOC):

- Each rule fires when condition met + target is tbd
- Each rule does NOT fire when target has explicit value
- Rules don't fire when condition not met
- Cascade integration test: `control_required=yes` + `timing_required=tbd` + `sync_protocol=tbd` through `build_requirements_model()`. Verify: timing inferred to yes (rule 7), sync_protocol inferred to ntp (rule 5b), both assumptions recorded, order reflects causal chain
- Idempotency: call `build_requirements_model()` twice on same questionnaire, assert identical output
- Archetype default blocks inference: archetype sets field to concrete value, inference does not override even when condition met
- Assumption records have `source: "inference:..."` prefix

### Documentation (Part 1)

Add section "Automatic inference" to `INTAKE_OPERATOR_GUIDE.md`:
- Compiler fills certain tbd values when cross-field evidence is unambiguous
- These appear as assumptions in pipeline output with `source: "inference:..."` prefix
- Review workflow is the mechanism for confirming inferred values

### Files to modify (Part 1)

- `project/src/compiler/build_requirements_model.py` — add `apply_cross_field_inferences()` + wiring
- `project/src/validators/validate_stage_confidence.py` — fix assumption source messages (lines 113, 123)
- `project/tests/test_pipeline_e2e.py` — update 4 assertions
- `project/tests/test_inference_rules.py` — new file
- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md` — add inference section

---

## Part 2: Bootstrap/Init Command

### Чому

Новий користувач запускає `project/intake generate <workspace>` як першу команду, отримує `Workspace not found`. Потрібна окрема команда `project/intake init <workspace>`.

### Що змінюється

**New file: `project/src/intake/init_workspace.py` (~70 LOC)**

```
init_workspace(workspace_path, template_path=None)
  1. Derive object_id = basename(workspace_path)
  2. Validate object_id: ^[a-z][a-z0-9_-]{1,63}$ (ASCII, no spaces)
     - If invalid: fail with clear message suggesting a valid name
  3. Check workspace doesn't already have role_assignments.yaml
     - If exists: "Workspace already initialized. To regenerate workbooks:
       project/intake generate <workspace>. To re-initialize: delete
       role_assignments.yaml first."
  4. Create workspace directory
  5. Copy role_assignments.template.yaml → workspace/role_assignments.yaml
  6. Substitute object_id into template
  7. Print: "Workspace initialized. Edit role_assignments.yaml, then run:
     project/intake generate <workspace>"
```

Template source: `project/specs/questionnaire/role_assignments.template.yaml`.

**Overwrite rules:**

- Path doesn't exist → create + materialize
- Path exists but empty → materialize
- Path exists + has `role_assignments.yaml` → error with actionable message
- Subdirectories (`intake/`, `reports/`) NOT created — runtime commands materialize them

**File: `project/intake` (shell script)**

Add `init` command:

```sh
run_init() {
    [ $# -ge 1 ] || fail "init requires <workspace>"
    workspace=$(resolve_path "$1")
    shift
    cd "$ROOT_DIR"
    PYTHONPATH=. "$PYTHON" project/src/intake/init_workspace.py "$workspace" "$@"
}
```

Add to case statement and usage text.

**Improve generate error (Part 2 scope only — init must exist first):**

In `generate_intake_sheets.py`, at workspace existence check:

```python
if not workspace_path.exists():
    raise FileNotFoundError(
        f"Workspace not found: {workspace_path}\n"
        f"To create a new workspace: project/intake init {workspace_path.name}"
    )
```

### Explicit non-goals

- `--force` flag for re-initialization — user can delete `role_assignments.yaml` manually
- `--archetype` or `--template` presets — future work if needed
- Creating `intake/` or `reports/` subdirectories — runtime commands handle this
- Interactive prompts or wizards — CLI stays non-interactive

### Tests (`project/tests/test_init_workspace.py`, ~70 LOC)

- Happy path: workspace created, `role_assignments.yaml` materialized, object_id correct
- Already initialized → error with actionable message
- Empty directory → success
- Invalid object_id (spaces, Cyrillic, uppercase) → clear error

### Docs

- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md` — add init as step 0 before generate
- `project/README.md` — add init to command table

### Files to modify (Part 2)

- `project/src/intake/init_workspace.py` — new
- `project/intake` — add init command + usage
- `project/src/intake/generate_intake_sheets.py` — improve error message
- `project/tests/test_init_workspace.py` — new
- `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md` — add init step
- `project/README.md` — add init to command list

---

## Execution

Parts 1 and 2 have zero file overlap — can be implemented in parallel.

### Verification

```bash
# Part 1
project/intake verify                              # All tests pass
project/intake demo happy --date 2026-04-02        # Must print "completed successfully"
project/intake demo stress --date 2026-04-02       # Must print "expected domain validation failure"
# Verify: stress demo shows fewer warnings (OOB + tbd-count gone)

# Part 2
project/intake verify                              # All tests including new init tests pass
# Full init→generate smoke test:
tmpdir=$(mktemp -d)
project/intake init "$tmpdir/test_site"             # Must succeed, print next step
cat "$tmpdir/test_site/role_assignments.yaml"       # Must have object_id: test_site
project/intake generate "$tmpdir/test_site" --date 2026-04-02  # Must generate workbooks
ls "$tmpdir/test_site/intake/generated/"            # Must list guide files
```

### Post-implementation housekeeping

- Update `INTAKE_MASTER_NOTE.md` with CF-2 and bootstrap closure
- Update `PLAN_POST_V1_INTAKE_BOOTSTRAP.md` status from "draft skeleton" to "completed"

---

## Test coverage map

| Interaction path | Covered by | Status |
|---|---|---|
| Rule fires on tbd field | test_inference_rules.py | NEW |
| Rule doesn't fire on explicit value | test_inference_rules.py | NEW |
| Rule doesn't fire when condition unmet | test_inference_rules.py | NEW |
| Cascade rule 7→5 | test_inference_rules.py | NEW |
| Idempotency (2x identical run) | test_inference_rules.py | NEW |
| Archetype default blocks inference | test_inference_rules.py | NEW |
| sample_object_01: zero rules fire | test_pipeline_e2e.py:65 (existing) | GUARD |
| sample_object_02: Rule 2 fires | test_pipeline_e2e.py (updated) | UPDATED |
| OOB warning absent after inference | test_pipeline_e2e.py:143 (updated) | UPDATED |
| warning_count threshold | test_pipeline_e2e.py:100 (updated) | UPDATED |
| Schema validation post-inference | test_pipeline_e2e.py:159 (existing) | GUARD |
| Preview unresolved_s4_fields unchanged | test_intake_preview.py:76 (existing) | GUARD |
| Review oob_required still routed | test_intake_review.py:53 (existing) | GUARD |
| Graph topology from Rule 1 | NOT COVERED | ACCEPTED RISK |
| Graph topology from Rule 5a (PTP) | NOT COVERED | ACCEPTED RISK |
| Init happy path | test_init_workspace.py | NEW |
| Init on existing workspace | test_init_workspace.py | NEW |
| Init object_id sanitization | test_init_workspace.py | NEW |

---

## Architectural note: YAML-first tension

The project follows YAML-first specs for all domain knowledge (questionnaire, fields, archetypes, constraints, evidence policy). Inference rules in Python break this pattern. `constraints_hard.yaml` and `constraints_soft.yaml` have `expression: TBD` — the original design anticipated YAML-driven rules.

Current decision: keep in Python for 8 rules. If rules grow beyond ~15, migrate to YAML rule spec consumed by a generic inference engine, unifying with the planned constraint expression system.
