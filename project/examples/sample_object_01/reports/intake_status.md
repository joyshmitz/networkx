# Intake Status — sample_object_01

Compiled at: 2026-04-02

Answered: 41/41 (100%) | TBD: 0 | Unanswered: 0 | N/A: 0

## Scope Summary
- Object type: generation
- Criticality: high
- Services: telemetry, control, video, local_archiving

## Per Person
| Person | Roles | Owned | Answered | TBD | Unanswered |
|--------|-------|-------|----------|-----|------------|
| sample_arch | network_engineer, ot_architect | 5 | 5 | 0 | 0 |
| sample_field | commissioning_engineer, telemetry_engineer | 5 | 5 | 0 | 0 |
| sample_ops_sec | cybersecurity_engineer, operations_engineer | 11 | 11 | 0 | 0 |
| sample_pm_owner | object_owner, project_manager | 10 | 10 | 0 | 0 |
| sample_power_video | cabinet_power_engineer, video_engineer | 6 | 6 | 0 | 0 |

## Phase Readiness
- Phase 1 (Identity): complete
- Phase 2 (Constraints): complete
- Phase 3 (Operations): complete

## Unassigned Fields
- telemetry_required (owner_role: process_engineer)
- control_required (owner_role: process_engineer)
- iiot_required (owner_role: iiot_engineer)
- local_archiving_required (owner_role: process_engineer)

## Field Ownership Table
| Field | Section | Owner Person | Status | Value |
|-------|---------|-------------|--------|-------|
| acceptance_evidence_class | acceptance_criteria | sample_pm_owner | answered | test_records |
| fat_required | acceptance_criteria | sample_field | answered | yes |
| sat_required | acceptance_criteria | sample_field | answered | yes |
| control_required | critical_services | _unassigned | answered | yes |
| iiot_required | critical_services | _unassigned | answered | no |
| local_archiving_required | critical_services | _unassigned | answered | yes |
| telemetry_required | critical_services | _unassigned | answered | yes |
| video_required | critical_services | sample_power_video | answered | yes |
| carrier_diversity_target | external_transport | sample_arch | answered | dual_carrier_required |
| transport_separation_policy | external_transport | sample_arch | answered | logical_separation |
| wan_required | external_transport | sample_arch | answered | yes |
| evidence_maturity_class | governance | sample_pm_owner | answered | mixed |
| waiver_policy_class | governance | sample_pm_owner | answered | controlled |
| criticality_class | metadata | sample_pm_owner | answered | high |
| object_id | metadata | sample_pm_owner | answered | sample_object_01 |
| object_name | metadata | sample_pm_owner | answered | Sample Industrial Site |
| object_type | metadata | sample_pm_owner | answered | generation |
| project_stage | metadata | sample_pm_owner | answered | concept |
| growth_horizon_months | object_profile | sample_pm_owner | answered | 36 |
| staffing_model | object_profile | sample_ops_sec | answered | remote_ops |
| asbuilt_package_required | operations | sample_pm_owner | answered | yes |
| maintenance_window_model | operations | sample_ops_sec | answered | planned_only |
| operations_handoff_required | operations | sample_ops_sec | answered | yes |
| support_model | operations | sample_ops_sec | answered | hybrid |
| cabinet_constraint_class | power_environment | sample_power_video | answered | new_standard |
| environmental_constraint_class | power_environment | sample_power_video | answered | industrial_indoor |
| poe_budget_class | power_environment | sample_power_video | answered | medium |
| poe_required | power_environment | sample_power_video | answered | yes |
| power_source_model | power_environment | sample_power_video | answered | ac_dc_hybrid |
| common_cause_separation_required | resilience | sample_arch | answered | yes |
| degraded_mode_profile | resilience | sample_ops_sec | answered | telemetry_survives |
| mttr_target_class | resilience | sample_ops_sec | answered | four_hours |
| redundancy_target | resilience | sample_arch | answered | n_plus_1 |
| audit_logging_required | security_access | sample_ops_sec | answered | yes |
| contractor_access_policy | security_access | sample_ops_sec | answered | time_bounded_remote |
| oob_required | security_access | sample_ops_sec | answered | yes |
| remote_access_profile | security_access | sample_ops_sec | answered | controlled_vpn |
| security_zone_model | security_access | sample_ops_sec | answered | dmz_centric |
| sync_protocol | time_sync | sample_field | answered | ntp |
| timing_accuracy_class | time_sync | sample_field | answered | relaxed_ms |
| timing_required | time_sync | sample_field | answered | yes |
