from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from network_methodology_sandbox.model_utils import enabled_services


def generate_network_volume_summary(requirements: dict[str, Any]) -> str:
    metadata = requirements.get("metadata", {})
    resilience = requirements.get("resilience", {})
    security = requirements.get("security_access", {})
    time_sync = requirements.get("time_sync", {})
    operations = requirements.get("operations", {})
    power = requirements.get("power_environment", {})
    services = ", ".join(enabled_services(requirements)) or "none"

    lines = [
        "# Network Volume Summary",
        "",
        f"- Object ID: {metadata.get('object_id', 'TBD')}",
        f"- Object Name: {metadata.get('object_name', 'TBD')}",
        f"- Object Type: {metadata.get('object_type', 'TBD')}",
        f"- Stage: {metadata.get('project_stage', 'TBD')}",
        f"- Resolved Archetype: {metadata.get('resolved_archetype', 'TBD')}",
        f"- Enabled Services: {services}",
        f"- Security Zone Model: {security.get('security_zone_model', 'TBD')}",
        f"- Remote Access Profile: {security.get('remote_access_profile', 'TBD')}",
        f"- Redundancy Target: {resilience.get('redundancy_target', 'TBD')}",
        f"- Degraded Mode: {resilience.get('degraded_mode_profile', 'TBD')}",
        f"- Sync Protocol: {time_sync.get('sync_protocol', 'TBD')}",
        f"- Timing Accuracy Class: {time_sync.get('timing_accuracy_class', 'TBD')}",
        f"- Power Source Model: {power.get('power_source_model', 'TBD')}",
        f"- Cabinet Constraint Class: {power.get('cabinet_constraint_class', 'TBD')}",
        f"- Support Model: {operations.get('support_model', 'TBD')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    requirements_path = Path("project/examples/sample_object_01/requirements.yaml")
    requirements = yaml.safe_load(requirements_path.read_text(encoding="utf-8"))
    print(generate_network_volume_summary(requirements))


if __name__ == "__main__":
    main()
