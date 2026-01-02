"""
Tests for Base120 observability layer.

Verifies event emission contract for validator runs.
"""

import json
from pathlib import Path
from io import StringIO
from typing import Any, Mapping

from base120.validators.validate import validate_artifact
from base120.observability import create_event_sink, create_validator_event


ROOT = Path(__file__).parent.parent

with open(ROOT / "schemas" / "v1.0.0" / "artifact.schema.json") as f:
    SCHEMA = json.load(f)

with open(ROOT / "registries" / "mappings.json") as f:
    MAPPINGS = json.load(f)

with open(ROOT / "registries" / "err.json") as f:
    ERR_REGISTRY = json.load(f)["registry"]


def test_success_validation_emits_event():
    """Successful validation emits event with result='success'."""
    output = StringIO()
    event_sink = create_event_sink(output)
    
    artifact = {
        "id": "test-success-001",
        "domain": "core",
        "class": "example",
        "instance": "test",
        "models": ["FM1"]
    }
    
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=event_sink)
    
    assert errors == [], "Valid artifact should produce no errors"
    
    # Parse emitted event
    output.seek(0)
    event = json.loads(output.read().strip())
    
    assert event["event_type"] == "validator_result"
    assert event["artifact_id"] == "test-success-001"
    assert event["schema_version"] == "v1.0.0"
    assert event["result"] == "success"
    assert event["error_codes"] == []
    assert event["failure_mode_ids"] == []
    assert "timestamp" in event


def test_schema_failure_emits_event_with_fm15():
    """Schema validation failure emits event with FM15."""
    output = StringIO()
    event_sink = create_event_sink(output)
    
    artifact = {
        "id": "test-schema-fail-001",
        "domain": "core",
        "class": "example"
        # Missing required 'instance' field
    }
    
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=event_sink)
    
    assert errors == ["ERR-SCHEMA-001"], "Schema failure should produce ERR-SCHEMA-001"
    
    # Parse emitted event
    output.seek(0)
    event = json.loads(output.read().strip())
    
    assert event["event_type"] == "validator_result"
    assert event["artifact_id"] == "test-schema-fail-001"
    assert event["result"] == "failure"
    assert event["error_codes"] == ["ERR-SCHEMA-001"]
    assert "FM15" in event["failure_mode_ids"], "Schema failure should include FM15"


def test_failure_with_multiple_fms():
    """Validation failure with multiple FMs includes all in event."""
    output = StringIO()
    event_sink = create_event_sink(output)
    
    # Use subclass "22" which maps to FM29 and FM30
    artifact = {
        "id": "test-multi-fm-001",
        "domain": "core",
        "class": "22",
        "instance": "test",
        "models": ["FM1"]
    }
    
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=event_sink)
    
    # FM30 dominance: only ERR-GOV-004 should be returned
    assert errors == ["ERR-GOV-004"], "FM30 dominance should return only ERR-GOV-004"
    
    # Parse emitted event
    output.seek(0)
    event = json.loads(output.read().strip())
    
    assert event["result"] == "failure"
    assert event["error_codes"] == ["ERR-GOV-004"]
    # Should contain both FM29 and FM30 from the mapping
    assert "FM29" in event["failure_mode_ids"]
    assert "FM30" in event["failure_mode_ids"]


def test_backward_compatibility_without_event_sink():
    """Without event_sink parameter, validation behaves identically."""
    artifact = {
        "id": "test-compat-001",
        "domain": "core",
        "class": "example",
        "instance": "test",
        "models": ["FM1"]
    }
    
    # Call without event_sink (backward compatible)
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY)
    
    assert errors == [], "Valid artifact should produce no errors"
    # No event should be emitted, but validation succeeds


def test_event_emission_failure_does_not_propagate():
    """Errors during event emission do not affect validation."""
    def failing_sink(event: Mapping[str, Any]) -> None:
        raise Exception("Event emission failed!")
    
    artifact = {
        "id": "test-fail-safe-001",
        "domain": "core",
        "class": "example",
        "instance": "test",
        "models": ["FM1"]
    }
    
    # Should not raise exception despite failing sink
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=failing_sink)
    
    assert errors == [], "Valid artifact should produce no errors"


def test_unknown_artifact_id():
    """Missing artifact ID results in 'unknown' in event."""
    output = StringIO()
    event_sink = create_event_sink(output)
    
    artifact = {
        # No 'id' field
        "domain": "core",
        "class": "example",
        "instance": "test",
        "models": ["FM1"]
    }

    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=event_sink)
    assert errors == ["ERR-SCHEMA-001"], "Missing id should fail schema validation"

    output.seek(0)
    event = json.loads(output.read().strip())
    
    assert event["artifact_id"] == "unknown"
    assert event["result"] == "failure"
    assert "ERR-SCHEMA-001" in event["error_codes"]


def test_create_validator_event_with_correlation_id():
    """create_validator_event includes correlation_id when provided."""
    event = create_validator_event(
        artifact_id="test-001",
        schema_version="v1.0.0",
        result="success",
        error_codes=[],
        failure_mode_ids=[],
        correlation_id="req-12345"
    )
    
    assert event["correlation_id"] == "req-12345"
    assert event["event_type"] == "validator_result"


def test_create_validator_event_without_correlation_id():
    """create_validator_event omits correlation_id when not provided."""
    event = create_validator_event(
        artifact_id="test-001",
        schema_version="v1.0.0",
        result="success",
        error_codes=[],
        failure_mode_ids=[]
    )
    
    assert "correlation_id" not in event


def test_failure_mode_ids_are_sorted():
    """Failure mode IDs in events are sorted lexicographically."""
    event = create_validator_event(
        artifact_id="test-001",
        schema_version="v1.0.0",
        result="failure",
        error_codes=["ERR-001"],
        failure_mode_ids=["FM30", "FM15", "FM1"]
    )
    
    # Should be sorted
    assert event["failure_mode_ids"] == ["FM1", "FM15", "FM30"]


def test_corpus_valid_basic_with_observability():
    """Corpus test: valid-basic.json emits success event."""
    output = StringIO()
    event_sink = create_event_sink(output)
    
    artifact = {
        "id": "artifact-valid-001",
        "domain": "core",
        "class": "example",
        "instance": "happy-path",
        "models": ["FM1"]
    }
    
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=event_sink)
    
    assert errors == []
    
    output.seek(0)
    event = json.loads(output.read().strip())
    
    assert event["result"] == "success"
    assert event["artifact_id"] == "artifact-valid-001"


def test_corpus_invalid_schema_with_observability():
    """Corpus test: invalid schema emits failure event."""
    output = StringIO()
    event_sink = create_event_sink(output)
    
    artifact = {
        "id": "artifact-invalid-001",
        "domain": "core",
        "class": "example",
        "models": ["FM1"]
        # Missing 'instance' field
    }
    
    errors = validate_artifact(artifact, SCHEMA, MAPPINGS, ERR_REGISTRY, event_sink=event_sink)
    
    assert errors == ["ERR-SCHEMA-001"]
    
    output.seek(0)
    event = json.loads(output.read().strip())
    
    assert event["result"] == "failure"
    assert event["error_codes"] == ["ERR-SCHEMA-001"]
    assert "FM15" in event["failure_mode_ids"]
