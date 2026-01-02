from base120.validators.schema import validate_schema
from base120.validators.mappings import resolve_failure_modes
from base120.validators.errors import resolve_errors

def validate_artifact(
    artifact: dict,
    schema: dict,
    mappings: dict,
    err_registry: list[dict],
    event_sink=None
) -> list[str]:

    errs = []
    fms = []

    # 1. Schema validation
    errs.extend(validate_schema(artifact, schema))
    if errs:
        # Schema failure implies FM15 (Schema Non-Compliance)
        fms = ["FM15"]
        _emit_event(artifact, errs, fms, event_sink)
        return sorted(set(errs))

    # 2. Subclass → FM
    subclass = artifact.get("class")
    fms = resolve_failure_modes(subclass, mappings)

    # 3. FM → ERR
    errs.extend(resolve_errors(fms, err_registry))

    # 4. Emit observability event
    _emit_event(artifact, errs, fms, event_sink)

    return sorted(set(errs))


def _emit_event(artifact, error_codes, failure_mode_ids, event_sink):
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
            failure_mode_ids=failure_mode_ids
        )
        
        event_sink(event)
    except Exception:
        # Never propagate observability failures
        # This preserves validation semantics
        pass
