"""
Base120 Observability Layer

Provides structured event emission for validator runs.
Uses standard library only - no runtime dependencies.
"""

from typing import Any, Callable, Iterable, Mapping, Optional, TextIO, cast

import json
import sys
from datetime import datetime, timezone


def create_event_sink(output: Optional[TextIO] = None) -> Callable[[Mapping[str, Any]], None]:
    """
    Create a standard event sink that logs structured JSON events.
    
    Args:
        output: File-like object for output (default: sys.stdout)
        
    Returns:
        Callable that accepts event dict and writes JSON to output
        
    Example:
        >>> sink = create_event_sink()
        >>> sink({"event_type": "validator_result", "result": "success"})
    """
    if output is None:
        output = sys.stdout
    output = cast(TextIO, output)
        
    def sink(event: Mapping[str, Any]) -> None:
        try:
            json.dump(event, output)
            output.write('\n')
            output.flush()
        except Exception:
            # Never propagate event emission errors
            # Observability failures must not affect validation semantics
            pass
    
    return sink


def create_validator_event(
    artifact_id: str,
    schema_version: str,
    result: str,
    error_codes: Iterable[str],
    failure_mode_ids: Iterable[str],
    correlation_id: Optional[str] = None,
) -> Mapping[str, Any]:
    """
    Create a validator_result event conforming to the observability schema.
    
    Args:
        artifact_id: ID from artifact or "unknown" if missing
        schema_version: Schema version string (e.g., "v1.0.0")
        result: "success" or "failure"
        error_codes: List of error code strings
        failure_mode_ids: List of failure mode ID strings
        correlation_id: Optional correlation ID for request tracing
        
    Returns:
        Dict conforming to validator_result event schema
    """
    event: dict[str, Any] = {
        "event_type": "validator_result",
        "artifact_id": artifact_id,
        "schema_version": schema_version,
        "result": result,
        "error_codes": list(error_codes),
        "failure_mode_ids": sorted(failure_mode_ids),  # Ensure sorted for consistency
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if correlation_id is not None:
        event["correlation_id"] = correlation_id
    
    return event
