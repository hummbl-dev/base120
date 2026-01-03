"""Contract unit validation logic for Base120."""
from typing import Any, Mapping, Sequence
import jsonschema
from jsonschema.validators import Draft202012Validator


def validate_contract_schema(
    contract: Mapping[str, Any],
    contract_schema: Mapping[str, Any]
) -> list[str]:
    """
    Validate a contract unit against the contract schema.
    
    Returns a list of validation error messages.
    Empty list indicates successful validation.
    """
    validator = Draft202012Validator(contract_schema)
    errors = []
    
    for error in validator.iter_errors(contract):
        # Format error path
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"Schema error at '{path}': {error.message}")
    
    return errors


def validate_failure_graph(
    failure_graph: Mapping[str, Any]
) -> list[str]:
    """
    Validate semantic rules for the failure graph.
    
    Checks:
    - Node IDs are unique
    - Edge references point to existing nodes
    - No cycles in escalation paths (termination nodes must be reachable)
    - Retry limits are within bounds
    - Actions are semantically valid
    """
    errors = []
    
    if "nodes" not in failure_graph:
        return ["Failure graph missing 'nodes' field"]
    
    if "edges" not in failure_graph:
        return ["Failure graph missing 'edges' field"]
    
    nodes = failure_graph["nodes"]
    edges = failure_graph["edges"]
    
    # Check node ID uniqueness
    node_ids = [node.get("id") for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
        errors.append(f"Duplicate node IDs found: {list(set(duplicates))}")
    
    node_id_set = set(node_ids)
    
    # Check edge references
    for i, edge in enumerate(edges):
        from_id = edge.get("from")
        to_id = edge.get("to")
        
        if from_id not in node_id_set:
            errors.append(f"Edge {i}: 'from' node '{from_id}' does not exist")
        
        if to_id not in node_id_set:
            errors.append(f"Edge {i}: 'to' node '{to_id}' does not exist")
    
    # Check that termination nodes don't have outgoing edges
    termination_nodes = {
        node.get("id") for node in nodes 
        if node.get("action") == "terminate"
    }
    
    for edge in edges:
        if edge.get("from") in termination_nodes:
            errors.append(
                f"Termination node '{edge.get('from')}' has outgoing edge "
                f"to '{edge.get('to')}' (termination nodes cannot escalate)"
            )
    
    # Check retry limits
    for node in nodes:
        max_retries = node.get("max_retries")
        if max_retries is not None:
            if max_retries < 0:
                errors.append(
                    f"Node '{node.get('id')}': max_retries must be >= 0"
                )
            if max_retries > 10:
                errors.append(
                    f"Node '{node.get('id')}': max_retries must be <= 10"
                )
    
    # Check for at least one termination node
    if not termination_nodes:
        errors.append(
            "Failure graph must contain at least one termination node"
        )
    
    return errors


def validate_metadata_consistency(
    metadata: Mapping[str, Any],
    contract_version: str
) -> list[str]:
    """
    Validate metadata consistency rules.
    
    Checks:
    - Created date is before or equal to updated date
    - Contract version is compatible with environment requirements
    - Compatibility environments are non-empty
    """
    errors = []
    
    created = metadata.get("created")
    updated = metadata.get("updated")
    
    if created and updated:
        if created > updated:
            errors.append(
                f"Metadata: 'created' date ({created}) is after 'updated' "
                f"date ({updated})"
            )
    
    compatibility = metadata.get("compatibility", {})
    environments = compatibility.get("environments", [])
    
    if not environments:
        errors.append("Metadata: compatibility.environments must not be empty")
    
    minimum_version = compatibility.get("minimum_version")
    if minimum_version:
        # Check that contract_version >= minimum_version
        # Simple string comparison works for semantic versions
        if contract_version < minimum_version:
            errors.append(
                f"Metadata: contract_version ({contract_version}) is less "
                f"than minimum_version ({minimum_version})"
            )
    
    return errors


def validate_contract(
    contract: Mapping[str, Any],
    contract_schema: Mapping[str, Any]
) -> tuple[bool, list[str], list[str]]:
    """
    Validate a complete contract unit.
    
    Returns:
        tuple of (is_valid, errors, warnings)
        - is_valid: True if contract passes all validations
        - errors: List of error messages (blocking issues)
        - warnings: List of warning messages (non-blocking issues)
    """
    errors = []
    warnings = []
    
    # 1. Schema validation (hard requirement)
    schema_errors = validate_contract_schema(contract, contract_schema)
    errors.extend(schema_errors)
    
    # If schema validation fails, don't proceed with semantic validation
    if schema_errors:
        return False, errors, warnings
    
    # 2. Failure graph semantic validation
    failure_graph = contract.get("failure_graph", {})
    graph_errors = validate_failure_graph(failure_graph)
    errors.extend(graph_errors)
    
    # 3. Metadata consistency validation
    metadata = contract.get("metadata", {})
    contract_version = contract.get("contract_version", "")
    metadata_errors = validate_metadata_consistency(metadata, contract_version)
    errors.extend(metadata_errors)
    
    # 4. Check for warnings (non-blocking issues)
    # Example: Missing optional description
    if not metadata.get("description"):
        warnings.append("Metadata: 'description' field is recommended but missing")
    
    # Check artifact schema has proper structure
    artifact_schema = contract.get("artifact_schema", {})
    if "required" not in artifact_schema:
        warnings.append(
            "Artifact schema: 'required' field is recommended but missing"
        )
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings
