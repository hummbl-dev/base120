"""Tests for Base120 contract unit validation."""
import json
from pathlib import Path

from base120.contract.validate import (
    validate_contract_schema,
    validate_failure_graph,
    validate_metadata_consistency,
    validate_contract
)

ROOT = Path(__file__).parent.parent
SCHEMA_PATH = ROOT / "schemas" / "v1.0.0" / "contract.schema.json"
EXAMPLES_PATH = ROOT / "examples" / "contracts"

with open(SCHEMA_PATH) as f:
    CONTRACT_SCHEMA = json.load(f)


def test_valid_contract_passes():
    """Test that a valid contract passes all validations."""
    with open(EXAMPLES_PATH / "valid-basic-contract.json") as f:
        contract = json.load(f)
    
    is_valid, errors, warnings = validate_contract(contract, CONTRACT_SCHEMA)
    
    assert is_valid, f"Expected valid contract but got errors: {errors}"
    assert len(errors) == 0
    # Warnings are allowed for valid contracts


def test_invalid_missing_metadata_fails():
    """Test that a contract missing metadata fails schema validation."""
    with open(EXAMPLES_PATH / "invalid-missing-metadata.json") as f:
        contract = json.load(f)
    
    is_valid, errors, warnings = validate_contract(contract, CONTRACT_SCHEMA)
    
    assert not is_valid
    assert len(errors) > 0
    assert any("metadata" in err.lower() for err in errors)


def test_invalid_termination_edge_fails():
    """Test that termination nodes with outgoing edges fail validation."""
    with open(EXAMPLES_PATH / "invalid-termination-edge.json") as f:
        contract = json.load(f)
    
    is_valid, errors, warnings = validate_contract(contract, CONTRACT_SCHEMA)
    
    assert not is_valid
    assert len(errors) > 0
    assert any("termination" in err.lower() for err in errors)


def test_failure_graph_duplicate_nodes():
    """Test that duplicate node IDs are detected."""
    failure_graph = {
        "nodes": [
            {"id": "FM1", "name": "Test", "max_retries": 0, "action": "terminate"},
            {"id": "FM1", "name": "Duplicate", "max_retries": 0, "action": "terminate"}
        ],
        "edges": []
    }
    
    errors = validate_failure_graph(failure_graph)
    
    assert len(errors) > 0
    assert any("duplicate" in err.lower() for err in errors)


def test_failure_graph_invalid_edge_reference():
    """Test that edges referencing non-existent nodes are detected."""
    failure_graph = {
        "nodes": [
            {"id": "FM1", "name": "Test", "max_retries": 0, "action": "terminate"}
        ],
        "edges": [
            {"from": "FM1", "to": "FM99", "condition": "test"}
        ]
    }
    
    errors = validate_failure_graph(failure_graph)
    
    assert len(errors) > 0
    assert any("fm99" in err.lower() for err in errors)


def test_failure_graph_no_termination_node():
    """Test that failure graphs must have at least one termination node."""
    failure_graph = {
        "nodes": [
            {"id": "FM1", "name": "Test", "max_retries": 3, "action": "retry"},
            {"id": "FM2", "name": "Test2", "max_retries": 2, "action": "escalate"}
        ],
        "edges": []
    }
    
    errors = validate_failure_graph(failure_graph)
    
    assert len(errors) > 0
    assert any("termination" in err.lower() for err in errors)


def test_metadata_created_after_updated():
    """Test that created date must be before or equal to updated date."""
    metadata = {
        "created": "2026-01-03T18:00:00Z",
        "updated": "2026-01-03T17:00:00Z",
        "compatibility": {
            "environments": ["production"]
        }
    }
    
    errors = validate_metadata_consistency(metadata, "v1.0.0")
    
    assert len(errors) > 0
    assert any("created" in err.lower() and "after" in err.lower() for err in errors)


def test_metadata_empty_environments():
    """Test that environments list cannot be empty."""
    metadata = {
        "created": "2026-01-03T17:00:00Z",
        "updated": "2026-01-03T17:00:00Z",
        "compatibility": {
            "environments": []
        }
    }
    
    errors = validate_metadata_consistency(metadata, "v1.0.0")
    
    assert len(errors) > 0
    assert any("environments" in err.lower() for err in errors)


def test_metadata_version_compatibility():
    """Test that contract version must be >= minimum version."""
    metadata = {
        "created": "2026-01-03T17:00:00Z",
        "updated": "2026-01-03T17:00:00Z",
        "compatibility": {
            "environments": ["production"],
            "minimum_version": "v2.0.0"
        }
    }
    
    errors = validate_metadata_consistency(metadata, "v1.0.0")
    
    assert len(errors) > 0
    assert any("minimum_version" in err.lower() for err in errors)


def test_contract_schema_validation():
    """Test basic schema validation catches missing required fields."""
    contract = {
        "contract_version": "v1.0.0",
        "service_name": "test"
        # Missing required fields: artifact_schema, failure_graph, metadata
    }
    
    errors = validate_contract_schema(contract, CONTRACT_SCHEMA)
    
    assert len(errors) > 0
    # Should have errors for each missing required field


def test_retry_limits_bounds():
    """Test that retry limits are enforced within bounds."""
    failure_graph = {
        "nodes": [
            {"id": "FM1", "name": "Test", "max_retries": -1, "action": "terminate"},
            {"id": "FM2", "name": "Test2", "max_retries": 15, "action": "terminate"}
        ],
        "edges": []
    }
    
    errors = validate_failure_graph(failure_graph)
    
    assert len(errors) >= 2
    assert any("fm1" in err.lower() and ">= 0" in err.lower() for err in errors)
    assert any("fm2" in err.lower() and "<= 10" in err.lower() for err in errors)
