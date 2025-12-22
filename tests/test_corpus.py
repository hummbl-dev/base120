import json
from pathlib import Path

from base120.validators.validate import validate_artifact

ROOT = Path(__file__).parent.parent
CORPUS = ROOT / "tests" / "corpus"

with open(ROOT / "schemas" / "v1.0.0" / "artifact.schema.json") as f:
    SCHEMA = json.load(f)

with open(ROOT / "registries" / "mappings.json") as f:
    MAPPINGS = json.load(f)

with open(ROOT / "registries" / "err.json") as f:
    ERR_REGISTRY = json.load(f)["registry"]

def load_json(path):
    with open(path) as f:
        return json.load(f)

def test_valid_corpus():
    for path in (CORPUS / "valid").glob("*.json"):
        artifact = load_json(path)
        errs = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY)
        assert errs == [], f"{path.name} produced {errs}"

def test_invalid_corpus():
    for path in (CORPUS / "invalid").glob("*.json"):
        artifact = load_json(path)
        expected = load_json(
            CORPUS / "expected" / f"{path.stem}.errs.json"
        )
        errs = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY)
        assert errs == expected, f"{path.name} expected {expected}, got {errs}"
