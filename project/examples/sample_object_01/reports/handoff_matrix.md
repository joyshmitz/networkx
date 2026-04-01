# Handoff Matrix

| Field | Value | Activation | Artifacts | Consumers |
| --- | --- | --- | --- | --- |
| object_id | sample_object_01 | baseline | network_volume, commissioning_pack, operations_handoff_pack, asbuilt_closure_pack | project_manager, ot_architect |
| object_name | Sample Industrial Site | baseline | network_volume, commissioning_pack, operations_handoff_pack | project_manager, ot_architect |
| object_type | generation | baseline | network_volume, addressing_framework_pack, telemetry_transport_pack, video_transport_pack, iiot_integration_pack | ot_architect, network_engineer, telemetry_engineer, video_engineer, iiot_engineer |
| project_stage | concept | baseline | network_volume, commissioning_pack, asbuilt_closure_pack | project_manager, commissioning_engineer |
| criticality_class | high | baseline | network_volume, firewall_policy_intent_pack, telemetry_transport_pack, operations_handoff_pack, commissioning_pack | object_owner, ot_architect, operations_engineer |
| staffing_model | remote_ops | baseline | network_volume, operations_handoff_pack, addressing_framework_pack | operations_engineer, network_engineer |
| growth_horizon_months | 36 | baseline | network_volume, cabinet_build_pack, addressing_framework_pack, operations_handoff_pack | ot_architect, operations_engineer |
| telemetry_required | yes | required | network_volume, telemetry_transport_pack, commissioning_pack | telemetry_engineer, commissioning_engineer |
| control_required | yes | required | network_volume, telemetry_transport_pack, firewall_policy_intent_pack, commissioning_pack | telemetry_engineer, cybersecurity_engineer, operations_engineer |
| video_required | yes | required | network_volume, video_transport_pack, cabinet_build_pack, commissioning_pack | video_engineer, cabinet_power_engineer |
| iiot_required | no | inactive | network_volume, iiot_integration_pack, firewall_policy_intent_pack | iiot_engineer, cybersecurity_engineer |
| local_archiving_required | yes | required | network_volume, video_transport_pack, telemetry_transport_pack, operations_handoff_pack | video_engineer, telemetry_engineer, operations_engineer |
| wan_required | yes | required | network_volume, telemetry_transport_pack, iiot_integration_pack, firewall_policy_intent_pack | network_engineer, telemetry_engineer, iiot_engineer |
| carrier_diversity_target | dual_carrier_required | baseline | network_volume, firewall_policy_intent_pack, commissioning_pack, operations_handoff_pack | network_engineer, cybersecurity_engineer, commissioning_engineer |
| transport_separation_policy | logical_separation | baseline | network_volume, telemetry_transport_pack, video_transport_pack, iiot_integration_pack | network_engineer, telemetry_engineer, video_engineer, iiot_engineer |
| security_zone_model | dmz_centric | baseline | network_volume, firewall_policy_intent_pack, telemetry_transport_pack, video_transport_pack, iiot_integration_pack | cybersecurity_engineer, network_engineer, telemetry_engineer, video_engineer, iiot_engineer |
| remote_access_profile | controlled_vpn | baseline | network_volume, firewall_policy_intent_pack, operations_handoff_pack | cybersecurity_engineer, operations_engineer |
| contractor_access_policy | time_bounded_remote | baseline | network_volume, firewall_policy_intent_pack, operations_handoff_pack, commissioning_pack | cybersecurity_engineer, operations_engineer, project_manager |
| audit_logging_required | yes | required | network_volume, firewall_policy_intent_pack, operations_handoff_pack, commissioning_pack | cybersecurity_engineer, operations_engineer, commissioning_engineer |
| oob_required | yes | required | network_volume, addressing_framework_pack, operations_handoff_pack, commissioning_pack | network_engineer, operations_engineer, commissioning_engineer |
| timing_required | yes | required | network_volume, telemetry_transport_pack, commissioning_pack, operations_handoff_pack | telemetry_engineer, network_engineer, operations_engineer |
| sync_protocol | ntp | baseline | network_volume, telemetry_transport_pack, commissioning_pack, operations_handoff_pack | network_engineer, telemetry_engineer, operations_engineer |
| timing_accuracy_class | relaxed_ms | baseline | network_volume, telemetry_transport_pack, commissioning_pack | network_engineer, telemetry_engineer, commissioning_engineer |
| power_source_model | ac_dc_hybrid | baseline | network_volume, cabinet_build_pack, operations_handoff_pack | cabinet_power_engineer, operations_engineer |
| cabinet_constraint_class | new_standard | baseline | network_volume, cabinet_build_pack | cabinet_power_engineer, network_engineer |
| environmental_constraint_class | industrial_indoor | baseline | network_volume, cabinet_build_pack, commissioning_pack, operations_handoff_pack | cabinet_power_engineer, commissioning_engineer, operations_engineer |
| poe_required | yes | required | network_volume, cabinet_build_pack, video_transport_pack | cabinet_power_engineer, video_engineer |
| poe_budget_class | medium | baseline | network_volume, cabinet_build_pack, video_transport_pack | cabinet_power_engineer, video_engineer |
| redundancy_target | n_plus_1 | baseline | network_volume, commissioning_pack, operations_handoff_pack, asbuilt_closure_pack | network_engineer, operations_engineer, commissioning_engineer |
| degraded_mode_profile | telemetry_survives | baseline | network_volume, operations_handoff_pack, commissioning_pack | operations_engineer, telemetry_engineer, video_engineer |
| mttr_target_class | four_hours | baseline | network_volume, operations_handoff_pack, asbuilt_closure_pack | operations_engineer, project_manager |
| common_cause_separation_required | yes | required | network_volume, commissioning_pack, asbuilt_closure_pack | ot_architect, network_engineer, commissioning_engineer |
| support_model | hybrid | baseline | network_volume, operations_handoff_pack, asbuilt_closure_pack | operations_engineer, project_manager |
| maintenance_window_model | planned_only | baseline | network_volume, operations_handoff_pack, commissioning_pack | operations_engineer, commissioning_engineer |
| operations_handoff_required | yes | required | network_volume, operations_handoff_pack | operations_engineer, project_manager |
| asbuilt_package_required | yes | required | network_volume, asbuilt_closure_pack | project_manager, commissioning_engineer, operations_engineer |
| fat_required | yes | required | network_volume, commissioning_pack | commissioning_engineer, project_manager |
| sat_required | yes | required | network_volume, commissioning_pack, asbuilt_closure_pack | commissioning_engineer, operations_engineer |
| acceptance_evidence_class | test_records | baseline | network_volume, commissioning_pack, asbuilt_closure_pack | commissioning_engineer, object_owner |
| evidence_maturity_class | mixed | baseline | network_volume, commissioning_pack | project_manager, ot_architect |
| waiver_policy_class | controlled | baseline | network_volume, asbuilt_closure_pack, operations_handoff_pack | project_manager, object_owner |
