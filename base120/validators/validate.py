from typing import Any, Callable, Mapping, MutableSequence, Optional, Sequence

from base120.validators.schema import validate_schema
from base120.validators.mappings import resolve_failure_modes
from base120.validators.errors import resolve_errors

def validate_artifact(
    artifact: Mapping[str, Any],
    schema: Mapping[str, Any],
    mappings: Mapping[str, Any],
    err_registry: Sequence[Mapping[str, Any]],
    event_sink: Optional[Callable[[Mapping[str, Any]], None]] = None,
) -> list[str]:

    errs: MutableSequence[str] = []
    fms: list[str] = []

    # 1. Schema validation
    errs.extend(validate_schema(artifact, schema))
    if errs:
        # Schema failure implies FM15 (Schema Non-Compliance)
        fms = ["FM15"]
        _emit_event(artifact, errs, fms, event_sink)
        return sorted(set(errs))

    # 2. Subclass → FM
    subclass = str(artifact.get("class", ""))
    fms = resolve_failure_modes(subclass, mappings)

    # 3. FM → ERR
    errs.extend(resolve_errors(fms, err_registry))

    # 4. Emit observability event
    _emit_event(artifact, errs, fms, event_sink)

    return sorted(set(errs))


def _emit_event(
    artifact: Mapping[str, Any],
    error_codes: Sequence[str],
    failure_mode_ids: Sequence[str],
    event_sink: Optional[Callable[[Mapping[str, Any]], None]],
) -> None:
    """
    Emit validator_result event if event_sink is provided.
    
    Event emission errors are caught and never propagate.
    """
    if event_sink is None:
        return
    
    try:
        from base120.observability import create_validator_event
        
        artifact_id = artifact.get("id", "unknown")
        result = "success" if not error_codes else "failure"
        
        event = create_validator_event(
            artifact_id=artifact_id,
            schema_version="v1.0.0",
            result=result,
            error_codes=sorted(set(error_codes)),
            failure_mode_ids=list(failure_mode_ids),
        )
        
        event_sink(event)
    except Exception:
        # Never propagate observability failures
        # This preserves validation semantics
        pass
