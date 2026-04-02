# Intake Status — sample_object_02

Compiled at: 2026-04-02

Answered: 29/41 (70%) | TBD: 7 | Unanswered: 5 | N/A: 0

## Scope Summary
- Object type: utility_process
- Criticality: high
- Services: telemetry

## Per Person
| Person | Roles | Owned | Answered | TBD | Unanswered |
|--------|-------|-------|----------|-----|------------|
| sample2_arch | network_engineer, ot_architect | 5 | 4 | 1 | 0 |
| sample2_iiot_commissioning | commissioning_engineer, iiot_engineer | 3 | 1 | 0 | 2 |
| sample2_ops_sec | cybersecurity_engineer, operations_engineer | 11 | 6 | 3 | 2 |
| sample2_pm_owner | object_owner, project_manager | 10 | 9 | 0 | 1 |
| sample2_power_video | cabinet_power_engineer, video_engineer | 6 | 5 | 1 | 0 |
| sample2_process_telemetry | process_engineer, telemetry_engineer | 6 | 4 | 2 | 0 |

## Phase Readiness
- Phase 1 (Identity): partial — 2 tbd
- Phase 2 (Constraints): partial — 5 tbd
- Phase 3 (Operations): incomplete — 5 unanswered

## Field Ownership Table
| Field | Section | Owner Person | Status | Value |
|-------|---------|-------------|--------|-------|
| acceptance_evidence_class | acceptance_criteria | sample2_pm_owner | answered | basic_checklists |
| fat_required | acceptance_criteria | sample2_iiot_commissioning | unanswered |  |
| sat_required | acceptance_criteria | sample2_iiot_commissioning | unanswered |  |
| control_required | critical_services | sample2_process_telemetry | tbd |  |
| iiot_required | critical_services | sample2_iiot_commissioning | answered | no |
| local_archiving_required | critical_services | sample2_process_telemetry | tbd |  |
| telemetry_required | critical_services | sample2_process_telemetry | answered | yes |
| video_required | critical_services | sample2_power_video | answered | no |
| carrier_diversity_target | external_transport | sample2_arch | answered | single_path_allowed |
| transport_separation_policy | external_transport | sample2_arch | answered | shared_ok |
| wan_required | external_transport | sample2_arch | answered | yes |
| evidence_maturity_class | governance | sample2_pm_owner | answered | assumption_heavy |
| waiver_policy_class | governance | sample2_pm_owner | answered | provisional |
| criticality_class | metadata | sample2_pm_owner | answered | high |
| object_id | metadata | sample2_pm_owner | answered | sample_object_02 |
| object_name | metadata | sample2_pm_owner | answered | Remote Metering Point Alpha |
| object_type | metadata | sample2_pm_owner | answered | utility_process |
| project_stage | metadata | sample2_pm_owner | answered | concept |
| growth_horizon_months | object_profile | sample2_pm_owner | answered | 60 |
| staffing_model | object_profile | sample2_ops_sec | answered | remote_ops |
| asbuilt_package_required | operations | sample2_pm_owner | unanswered |  |
| maintenance_window_model | operations | sample2_ops_sec | unanswered |  |
| operations_handoff_required | operations | sample2_ops_sec | answered | yes |
| support_model | operations | sample2_ops_sec | unanswered |  |
| cabinet_constraint_class | power_environment | sample2_power_video | answered | existing_tight |
| environmental_constraint_class | power_environment | sample2_power_video | answered | outdoor_shelter |
| poe_budget_class | power_environment | sample2_power_video | tbd |  |
| poe_required | power_environment | sample2_power_video | answered | yes |
| power_source_model | power_environment | sample2_power_video | answered | dc_24_only |
| common_cause_separation_required | resilience | sample2_arch | tbd |  |
| degraded_mode_profile | resilience | sample2_ops_sec | answered | best_effort |
| mttr_target_class | resilience | sample2_ops_sec | answered | same_day |
| redundancy_target | resilience | sample2_arch | answered | none |
| audit_logging_required | security_access | sample2_ops_sec | tbd |  |
| contractor_access_policy | security_access | sample2_ops_sec | tbd |  |
| oob_required | security_access | sample2_ops_sec | tbd |  |
| remote_access_profile | security_access | sample2_ops_sec | answered | oob_only |
| security_zone_model | security_access | sample2_ops_sec | answered | segmented |
| sync_protocol | time_sync | sample2_process_telemetry | answered | ntp |
| timing_accuracy_class | time_sync | sample2_process_telemetry | answered | tens_of_us |
| timing_required | time_sync | sample2_process_telemetry | answered | yes |
