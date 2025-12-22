from jsonschema import Draft202012Validator

def validate_schema(artifact: dict, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(artifact))
    return ["ERR-SCHEMA-001"] if errors else []
