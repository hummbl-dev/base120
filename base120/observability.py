"""
Base120 Observability Layer

Provides structured event emission for validator runs.
Uses standard library only - no runtime dependencies.
"""

import json
import sys
from datetime import datetime, timezone


def create_event_sink(output=None):
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
        
    def sink(event):
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
    artifact_id,
    schema_version,
    result,
    error_codes,
    failure_mode_ids,
    correlation_id=None
):
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
    event = {
        "event_type": "validator_result",
        "artifact_id": artifact_id,
        "schema_version": schema_version,
        "result": result,
        "error_codes": error_codes,
        "failure_mode_ids": sorted(failure_mode_ids),  # Ensure sorted for consistency
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if correlation_id is not None:
        event["correlation_id"] = correlation_id
    
    return event
