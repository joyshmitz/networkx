# Codex Review Brief — Wave 2 Final

> **ARCHIVAL STATUS:** historical review brief.  
> This document remains as review context, not as an active execution plan.

**Branch:** `research/methodology-foundation`
**Commits under review:** `70e4c6b5e` → `1b171bee6` (4 commits)
**Run tests:** `source .venv/bin/activate && python -m pytest project/tests/ -v`
**Run pipeline:** `source .venv/bin/activate && python project/src/run_pipeline.py project/examples/sample_object_01/questionnaire.yaml`

---

## Commits

1. `70e4c6b5e` — fix: WAN gating, tbd zone model, sparse v2 detection (previous review fixes)
2. `3fc8d2542` — fix: failure-domain carrier nodes gated on wan_required
3. `a2a0296e8` — feat: annex activation + cross-graph consistency validators
4. `1b171bee6` — feat: role assignment validator with S4 conflict detection

---

## What to review

### New validators (3 files)

- **`project/src/validators/validate_annex_activation.py`** — reads annex spec files (`specs/questionnaire/annex_*.yaml`), evaluates `applies_when` conditions against requirements, warns when annex should be active but data absent. Supports both `{field_id, equals}` and `{any_of}` activation rules.

- **`project/src/validators/validate_cross_graph.py`** — checks that service graph zone nodes exist in logical graph (error if phantom zone), and that interface graph consumers match enabled services (warning if orphan consumer). Exempts `LOCAL_ARCHIVE` and `askoe`.

- **`project/src/validators/validate_role_assignments.py`** — reads `role_assignments.yaml` (auto-discovered next to questionnaire or via `--role-assignments` CLI arg), loads field specs from `questionnaire_v2_fields.yaml`. Checks: (1) all owner_roles assigned to at least one person, (2) S4 fields where owner and all reviewers collapse to same person → error requiring second reviewer.

### Modified files

- **`project/src/compiler/compile_graphs.py`** — WAN seed node gating (skip `wan_edge` role nodes when `wan_required != yes`), WAN enrichment gating, failure-domain carrier domain gating, `tbd` zone model → OT-only logical graph, service graph zone routing through OT when zone_model is tbd/flat.

- **`project/src/compiler/build_requirements_model.py`** — sparse v2 detection via version prefix or marker sections, defensive `_section()` helper for archetype resolution.

- **`project/src/run_pipeline.py`** — wires all 3 new validators, adds `--role-assignments` CLI arg with auto-discovery fallback.

### New tests (3 files, 29 tests)

- **`project/tests/test_annex_activation.py`** — 12 tests: activation logic, all 4 annexes, tbd non-activation
- **`project/tests/test_cross_graph.py`** — 5 tests: consistent zones, phantom zone, LOCAL_ARCHIVE exemption, orphan consumer, askoe exemption
- **`project/tests/test_role_assignments.py`** — 9 tests: person-role mapping, S4 conflict detection, partial overlap, full coverage
- Plus 3 tests added to existing files for WAN/carrier gating edge cases

### Modified tests

- **`project/tests/test_compile_graphs.py`** — added: wan_no skips WAN seed nodes, wan_no skips carrier domains, tbd zone model OT-only, tbd zone routes through OT, no-wan no transport edges
- **`project/tests/test_review_fixes.py`** — added: sparse v2 detection (version prefix, marker section, sparse compile, v1 still detected, unknown raises)

---

## Key design decisions

1. **Annex activation is warning-only** — annexes are not consumed by pipeline yet, validator only signals that annex data should exist. Blocking would be premature.

2. **Role assignments auto-discovered** — pipeline looks for `role_assignments.yaml` in same directory as questionnaire. Falls back to `None` (warning, not error) if absent.

3. **S4 conflict = owner persons ∩ reviewer persons with no independent reviewer** — if at least one reviewer person is different from all owner persons, no conflict. Partial overlap (same person holds both roles but another person also reviews) is safe.

4. **WAN gating is comprehensive** — physical seed nodes, physical enrichment, failure-domain carrier nodes all gated on `wan_required`. Service graph transport edges also gated.

5. **tbd zone_model = unresolved** — logical graph gets only OT node with no edges. Service graph routes everything through OT. Previously fell through to DMZ-style topology.

---

## Pipeline outputs after all changes

### sample_object_01 (happy path)
```
status: ok, error_count: 0, warning_count: 8, assumed_count: 0
```
Warnings: stage_confidence (concept+mixed), 3 annex activations (cctv, ha, time), 4 unassigned roles (process_engineer ×3, iiot_engineer ×1)

### sample_object_02 (stress test)
```
status: failed, error_count: 2, warning_count: 9, assumed_count: 0
```
Errors: high criticality + redundancy=none, tens_of_us + NTP
Warnings: stage_confidence, 12 tbd fields, shared_ok transport, single_path carrier, best_effort degraded, same_day MTTR, time annex activation, no role_assignments

---

## Total test suite

129 tests, 7 test files, ~1 second runtime. Covers:
- 9 validators (connectivity, segmentation, resilience, power, time, stage_confidence, annex_activation, cross_graph, role_assignments)
- Graph compilation (physical, logical, service, failure_domain, interface)
- End-to-end pipeline (both samples)
- Review fixes from previous rounds
