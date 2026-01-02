from typing import Any, Mapping

# pyright: reportMissingModuleSource=false
from jsonschema import Draft202012Validator


def validate_schema(artifact: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(artifact))  # type: ignore[call-overload]
    return ["ERR-SCHEMA-001"] if errors else []
