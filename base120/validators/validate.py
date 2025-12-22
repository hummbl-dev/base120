from base120.validators.schema import validate_schema
from base120.validators.mappings import resolve_failure_modes
from base120.validators.errors import resolve_errors

def validate_artifact(
    artifact: dict,
    schema: dict,
    mappings: dict,
    err_registry: list[dict]
) -> list[str]:

    errs = []

    # 1. Schema validation
    errs.extend(validate_schema(artifact, schema))
    if errs:
        return sorted(set(errs))

    # 2. Subclass → FM
    subclass = artifact.get("class")
    fms = resolve_failure_modes(subclass, mappings)

    # 3. FM → ERR
    errs.extend(resolve_errors(fms, err_registry))

    return sorted(set(errs))
