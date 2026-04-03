# Claude Follow-Up Delta Review — Slice 3 Blocking Gate Hardening

> **ARCHIVAL STATUS:** historical review output.  
> This document captures the follow-up delta review after the Slice 3 hardening commit.

**Дата:** 2026-04-03  
**Гілка:** `research/methodology-foundation-clean`  
**Рев'юер:** Claude (за запитом)  
**Delta:** `12930c251..364c9d812`  
**Scope:** fixes for Slice 3 review findings and test gaps

---

## 1. Finding 1.1 — Policy Validation (`advisory >= blocking threshold`)

**Status:** closed correctly.

[evidence_status.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/evidence_status.py) now validates policy load by:

- rejecting `blocking_enforced` in `defaults`;
- checking `advisory_minimum_strength >= blocking_minimum_strength` for each field with `blocking_enforced: true`;
- falling back `blocking_minimum_strength` to `advisory_minimum_strength` when the blocking minimum is omitted.

This closes the latent contract hole from the prior review at policy-load time instead of leaving it as a runtime blind spot.

---

## 2. Finding 1.2 — Item Override Whitelist

**Status:** closed correctly.

[review_packets.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/review_packets.py) now:

- defines `ALLOWED_ITEM_OVERRIDE_KEYS` explicitly for evidence-related fields only;
- raises `KeyError` on unexpected override keys;
- replaces raw `.update()` with explicit key assignment.

This removes the maintenance foot-gun where future callers could silently overwrite computed routing or priority fields.

---

## 3. Risk 2.3 — Unknown or Missing Stage

**Status:** closed with correct scope.

The follow-up tests validate conservative gate behavior for:

- `basic_design`
- `unexpected_stage`
- `None`

The test intentionally uses `build_evidence_status_from_snapshot(...)` over a mutated snapshot instead of `evidence_workspace(...)`, because upstream compile/schema validation rejects malformed or missing `project_stage` values before they reach the evidence layer.

This is the correct boundary.

---

## 4. Test Gap Closure

The follow-up review confirmed that the previously missing coverage is now present:

- missing stage coverage: closed
- CLI exit code after report write: closed
- gate-pass case with both blocking artifacts present: closed
- policy rejection for `blocking_enforced` in defaults: closed
- policy rejection for weaker advisory threshold than blocking threshold: closed

The CLI test specifically verifies that:

- `SystemExit(1)` is raised for a failed blocking gate;
- reports are written before exit;
- stdout still contains `gate_status: failed`.

---

## 5. Remaining Observations

### 5.1 Private helper imported by tests

`_load_evidence_policy` is still private by naming convention while being tested directly.

This is acceptable for now because the validation is internal infrastructure hardening, but if policy validation becomes a stable public contract later, renaming it without a leading underscore may be cleaner.

### 5.2 No dedicated whitelist-violation test

There is not yet a direct unit test that intentionally passes a bad key into `_make_review_item(...)` to assert the whitelist guard.

This is low priority because the current call site is narrow and the guard will fail loudly if someone violates it later.

### 5.3 Sorted iteration on override application

The sorted key iteration is deterministic but not semantically important here. It is harmless and does not justify further change.

---

## 6. Verdict

**accept as-is**

The follow-up review concludes that:

- all four findings from the previous Slice 3 review are closed correctly;
- the policy validation is now machine-enforced;
- the item override surface is hardened;
- the missing test coverage has been added in the right places;
- the implementation remains narrow and does not introduce scope creep.
