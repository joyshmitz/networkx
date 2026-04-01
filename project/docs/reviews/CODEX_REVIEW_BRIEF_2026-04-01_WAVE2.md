# Codex Review Brief — Wave 2 (test suite + corrective pass)

**Branch:** `research/methodology-foundation`
**Commits:** `4639832de` (foundation + corrective pass), `86a4e2cbb` (test suite)
**Run tests:** `source .venv/bin/activate && python -m pytest project/tests/ -v`
**Run pipeline:** `source .venv/bin/activate && python project/src/run_pipeline.py project/examples/sample_object_01/questionnaire.yaml`

---

## What to review

### Priority 1: Runtime code (src/)

These files contain the actual pipeline logic. Focus on correctness, edge cases, and whether the code does what the tests claim.

- `project/src/model_utils.py` — shared helpers: `is_yes`, `is_tbd`, `merge_missing_values_tracked`
- `project/src/compiler/build_requirements_model.py` — questionnaire → requirements compiler with archetype resolution, TBD preservation, malformed section rejection
- `project/src/compiler/compile_graphs.py` — 5 NetworkX graph builders (physical, logical, service, failure_domain, interface)
- `project/src/validators/validate_connectivity.py` — physical graph connectivity checks
- `project/src/validators/validate_segmentation.py` — zone model consistency + criticality tension
- `project/src/validators/validate_resilience.py` — redundancy, carrier diversity, MTTR, degraded mode cross-checks
- `project/src/validators/validate_power_ports.py` — PoE/power model consistency
- `project/src/validators/validate_time.py` — timing protocol vs accuracy consistency
- `project/src/validators/validate_stage_confidence.py` — stage × evidence maturity → confidence level, TBD counting
- `project/src/run_pipeline.py` — orchestrator: compile → validate → report
- `project/src/reports/generate_handoff_matrix.py` — handoff matrix from implementation mapping
- `project/src/reports/generate_network_volume_summary.py` — network volume summary report

### Priority 2: Tests (tests/)

90 tests across 4 files. Check whether tests actually verify meaningful behavior or just confirm current output.

- `project/tests/test_review_fixes.py` — 13 tests for corrective pass findings (malformed sections, TBD preservation, missing vs null, archetype consistency)
- `project/tests/test_compile_graphs.py` — 23 tests for graph compilation (physical, logical, service, failure_domain, interface)
- `project/tests/test_validators.py` — 35 tests for all 6 validators
- `project/tests/test_pipeline_e2e.py` — 19 end-to-end tests using real sample questionnaires

### Priority 3: Specs (only if relevant to runtime bugs)

- `project/specs/archetypes/station_archetypes.yaml` — 4 archetypes with defaults and topology seeds
- `project/specs/requirements/object_requirements_v2.schema.yaml` — JSON schema (tbd added to all enums)
- `project/specs/archetypes/equipment_catalog.yaml` — equipment definitions used by graph compiler

### Do not review

- Methodology docs (`project/docs/methodology/`) — already reviewed, not changed
- Review docs (`project/docs/reviews/`) — meta-documents, not runtime
- v1 deprecated files (`fields.yaml`, `values.yaml`, `core_questionnaire.yaml`, `object_requirements.schema.yaml`)

---

## Context for reviewer

### Architecture

```
questionnaire.yaml
  → build_requirements_model (archetype resolution, TBD preservation, normalization)
  → validate_requirements_model (JSON schema)
  → compile_all_graphs (5 NetworkX graphs from requirements)
  → run_validators (6 validators against graphs + requirements)
  → generate reports (validation summary, network volume, handoff matrix)
```

### Key design decisions

1. **TBD is a valid answer** — `tbd` is preserved through compilation, not replaced by archetype defaults. Only truly missing fields (absent from YAML) get defaults.
2. **Assumed fields are tracked** — `_assumptions` section in compiled output shows what was filled from archetype defaults, with original_value and source.
3. **Stage-confidence validator** — cross-checks project_stage × evidence_maturity_class → confidence_level (indicative/provisional/binding).
4. **Malformed sections rejected** — non-dict section values cause hard ValueError, not silent coercion.
5. **Schema allows tbd** — all enum fields in v2 schema accept `tbd` as valid value.

### What the previous Codex review found (all addressed)

- P1: Malformed sections were silently coerced to {} → now hard error
- P1: TBD was overwritten by archetype defaults → now preserved
- P2: Resilient archetype defaulted local_archiving=yes without topology support → fixed to no
- P3: Missing vs null indistinguishable in assumptions → fixed with present flag before insert

### Sample pipeline outputs

- `sample_object_01`: status ok, 0 errors, 1 warning (stage confidence), 0 assumed, 0 tbd
- `sample_object_02`: status failed, 2 errors, 7 warnings, 0 assumed, 12 tbd fields preserved
