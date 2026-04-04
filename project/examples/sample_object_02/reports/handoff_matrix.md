# Handoff Matrix

| Field | Value | Activation | Artifacts | Consumers |
| --- | --- | --- | --- | --- |
| object_id | sample_object_02 | baseline | network_volume, commissioning_pack, operations_handoff_pack, asbuilt_closure_pack | project_manager, ot_architect |
| object_name | Remote Metering Point Alpha | baseline | network_volume, commissioning_pack, operations_handoff_pack | project_manager, ot_architect |
| object_type | utility_process | baseline | network_volume, addressing_framework_pack, telemetry_transport_pack, video_transport_pack, iiot_integration_pack | ot_architect, network_engineer, telemetry_engineer, video_engineer, iiot_engineer |
| project_stage | concept | baseline | network_volume, commissioning_pack, asbuilt_closure_pack | project_manager, commissioning_engineer |
| criticality_class | high | baseline | network_volume, firewall_policy_intent_pack, telemetry_transport_pack, operations_handoff_pack, commissioning_pack | object_owner, ot_architect, operations_engineer |
| staffing_model | remote_ops | baseline | network_volume, operations_handoff_pack, addressing_framework_pack | operations_engineer, network_engineer |
| growth_horizon_months | 60 | baseline | network_volume, cabinet_build_pack, addressing_framework_pack, operations_handoff_pack | ot_architect, operations_engineer |
| telemetry_required | yes | required | network_volume, telemetry_transport_pack, commissioning_pack | telemetry_engineer, commissioning_engineer |
| control_required | tbd | unresolved | network_volume, telemetry_transport_pack, firewall_policy_intent_pack, commissioning_pack | telemetry_engineer, cybersecurity_engineer, operations_engineer |
| video_required | no | inactive | network_volume, video_transport_pack, cabinet_build_pack, commissioning_pack | video_engineer, cabinet_power_engineer |
| iiot_required | no | inactive | network_volume, iiot_integration_pack, firewall_policy_intent_pack | iiot_engineer, cybersecurity_engineer |
| local_archiving_required | tbd | unresolved | network_volume, video_transport_pack, telemetry_transport_pack, operations_handoff_pack | video_engineer, telemetry_engineer, operations_engineer |
| wan_required | yes | required | network_volume, telemetry_transport_pack, iiot_integration_pack, firewall_policy_intent_pack | network_engineer, telemetry_engineer, iiot_engineer |
| carrier_diversity_target | single_path_allowed | baseline | network_volume, firewall_policy_intent_pack, commissioning_pack, operations_handoff_pack | network_engineer, cybersecurity_engineer, commissioning_engineer |
| transport_separation_policy | shared_ok | baseline | network_volume, telemetry_transport_pack, video_transport_pack, iiot_integration_pack | network_engineer, telemetry_engineer, video_engineer, iiot_engineer |
| security_zone_model | segmented | baseline | network_volume, firewall_policy_intent_pack, telemetry_transport_pack, video_transport_pack, iiot_integration_pack | cybersecurity_engineer, network_engineer, telemetry_engineer, video_engineer, iiot_engineer |
| remote_access_profile | oob_only | baseline | network_volume, firewall_policy_intent_pack, operations_handoff_pack | cybersecurity_engineer, operations_engineer |
| contractor_access_policy | tbd | unresolved | network_volume, firewall_policy_intent_pack, operations_handoff_pack, commissioning_pack | cybersecurity_engineer, operations_engineer, project_manager |
| audit_logging_required | tbd | unresolved | network_volume, firewall_policy_intent_pack, operations_handoff_pack, commissioning_pack | cybersecurity_engineer, operations_engineer, commissioning_engineer |
| oob_required | yes | required | network_volume, addressing_framework_pack, operations_handoff_pack, commissioning_pack | network_engineer, operations_engineer, commissioning_engineer |
| timing_required | yes | required | network_volume, telemetry_transport_pack, commissioning_pack, operations_handoff_pack | telemetry_engineer, network_engineer, operations_engineer |
| sync_protocol | ntp | baseline | network_volume, telemetry_transport_pack, commissioning_pack, operations_handoff_pack | network_engineer, telemetry_engineer, operations_engineer |
| timing_accuracy_class | tens_of_us | baseline | network_volume, telemetry_transport_pack, commissioning_pack | network_engineer, telemetry_engineer, commissioning_engineer |
| power_source_model | dc_24_only | baseline | network_volume, cabinet_build_pack, operations_handoff_pack | cabinet_power_engineer, operations_engineer |
| cabinet_constraint_class | existing_tight | baseline | network_volume, cabinet_build_pack | cabinet_power_engineer, network_engineer |
| environmental_constraint_class | outdoor_shelter | baseline | network_volume, cabinet_build_pack, commissioning_pack, operations_handoff_pack | cabinet_power_engineer, commissioning_engineer, operations_engineer |
| poe_required | yes | required | network_volume, cabinet_build_pack, video_transport_pack | cabinet_power_engineer, video_engineer |
| poe_budget_class | tbd | unresolved | network_volume, cabinet_build_pack, video_transport_pack | cabinet_power_engineer, video_engineer |
| redundancy_target | none | baseline | network_volume, commissioning_pack, operations_handoff_pack, asbuilt_closure_pack | network_engineer, operations_engineer, commissioning_engineer |
| degraded_mode_profile | best_effort | baseline | network_volume, operations_handoff_pack, commissioning_pack | operations_engineer, telemetry_engineer, video_engineer |
| mttr_target_class | same_day | baseline | network_volume, operations_handoff_pack, asbuilt_closure_pack | operations_engineer, project_manager |
| common_cause_separation_required | tbd | unresolved | network_volume, commissioning_pack, asbuilt_closure_pack | ot_architect, network_engineer, commissioning_engineer |
| support_model | hybrid | baseline | network_volume, operations_handoff_pack, asbuilt_closure_pack | operations_engineer, project_manager |
| maintenance_window_model | planned_only | baseline | network_volume, operations_handoff_pack, commissioning_pack | operations_engineer, commissioning_engineer |
| operations_handoff_required | yes | required | network_volume, operations_handoff_pack | operations_engineer, project_manager |
| asbuilt_package_required | yes | required | network_volume, asbuilt_closure_pack | project_manager, commissioning_engineer, operations_engineer |
| fat_required | yes | required | network_volume, commissioning_pack | commissioning_engineer, project_manager |
| sat_required | yes | required | network_volume, commissioning_pack, asbuilt_closure_pack | commissioning_engineer, operations_engineer |
| acceptance_evidence_class | basic_checklists | baseline | network_volume, commissioning_pack, asbuilt_closure_pack | commissioning_engineer, object_owner |
| evidence_maturity_class | assumption_heavy | baseline | network_volume, commissioning_pack | project_manager, ot_architect |
| waiver_policy_class | provisional | baseline | network_volume, asbuilt_closure_pack, operations_handoff_pack | project_manager, object_owner |
