"""Contract validation report generation."""
from typing import Any, Mapping, Sequence
from datetime import datetime, timezone


def generate_report(
    service_name: str,
    is_valid: bool,
    errors: Sequence[str],
    warnings: Sequence[str],
    validated_environments: Sequence[str]
) -> dict[str, Any]:
    """
    Generate a machine-readable validation report.
    
    Returns a dictionary that can be serialized to JSON containing:
    - service_name: Name of the service
    - validation_status: "pass" or "fail"
    - timestamp: ISO 8601 timestamp
    - errors: List of error messages
    - warnings: List of warning messages
    - compatibility: Validated environments
    """
    return {
        "service_name": service_name,
        "validation_status": "pass" if is_valid else "fail",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "errors": list(errors),
        "warnings": list(warnings),
        "compatibility": {
            "validated_environments": list(validated_environments)
        }
    }
