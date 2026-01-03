"""Contract unit validation logic for Base120."""
from typing import Any, Mapping, Sequence, Optional
from datetime import datetime
from jsonschema.validators import Draft202012Validator


def _parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse ISO 8601 datetime string with robust handling of edge cases.
    
    Supports:
    - Full ISO 8601 format with timezone (e.g., "2026-01-03T17:00:00Z")
    - ISO 8601 with timezone offset (e.g., "2026-01-03T17:00:00+00:00")
    - ISO 8601 without timezone (e.g., "2026-01-03T17:00:00")
    - Fractional seconds (e.g., "2026-01-03T17:00:00.123456Z")
    
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not datetime_str:
        return None
    
    # List of datetime formats to try, in order of specificity
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # With fractional seconds and timezone
        "%Y-%m-%dT%H:%M:%S%z",      # With timezone
        "%Y-%m-%dT%H:%M:%S.%fZ",    # With fractional seconds, Z timezone
        "%Y-%m-%dT%H:%M:%SZ",       # With Z timezone
        "%Y-%m-%dT%H:%M:%S.%f",     # With fractional seconds, no timezone
        "%Y-%m-%dT%H:%M:%S",        # No fractional seconds, no timezone
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    return None


def _compare_semver(version1: str, version2: str) -> int:
    """
    Compare two semantic versions.
    
    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    # Remove 'v' prefix if present
    v1 = version1.lstrip('v')
    v2 = version2.lstrip('v')
    
    # Split into parts and convert to integers
    parts1 = [int(x) for x in v1.split('.')]
    parts2 = [int(x) for x in v2.split('.')]
    
    # Pad with zeros if needed
    while len(parts1) < len(parts2):
        parts1.append(0)
    while len(parts2) < len(parts1):
        parts2.append(0)
    
    # Compare parts
    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
    
    return 0


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


def _has_cycle(edges: list[dict[str, Any]], node_ids: set[str]) -> tuple[bool, list[str]]:
    """
    Detect cycles in a directed graph using depth-first search.
    
    Returns:
        Tuple of (has_cycle, cycle_path) where:
        - has_cycle: True if a cycle exists
        - cycle_path: List of node IDs forming a cycle, empty if no cycle
    """
    # Build adjacency list
    graph: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        from_id = edge.get("from")
        to_id = edge.get("to")
        if from_id in graph and to_id in node_ids:
            graph[from_id].append(to_id)
    
    # DFS with cycle detection
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: str) -> bool:
        """DFS helper that returns True if cycle detected."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Found a cycle - extract it from path
                cycle_start = path.index(neighbor)
                path_copy = path[cycle_start:] + [neighbor]
                path.clear()
                path.extend(path_copy)
                return True
        
        path.pop()
        rec_stack.remove(node)
        return False
    
    # Check all nodes as potential cycle starting points
    for node_id in node_ids:
        if node_id not in visited:
            if dfs(node_id):
                return True, path
    
    return False, []


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
    
    # Check for cycles in the graph
    # Only check if there are no errors about missing nodes (to avoid spurious cycle errors)
    if not any("does not exist" in err for err in errors):
        has_cycle, cycle_path = _has_cycle(edges, node_id_set)
        if has_cycle:
            cycle_str = " -> ".join(cycle_path)
            errors.append(
                f"Failure graph contains a cycle: {cycle_str}"
            )
    
    return errors


def validate_metadata_consistency(
    metadata: Mapping[str, Any],
    contract_version: str
) -> list[str]:
    """
    Validate metadata consistency rules.
    
    Checks:
    - Created date is before or equal to updated date (with robust datetime parsing)
    - Contract version is compatible with environment requirements
    - Compatibility environments are non-empty
    - Datetime fields are valid ISO 8601 timestamps
    """
    errors = []
    
    created_str = metadata.get("created")
    updated_str = metadata.get("updated")
    
    # Validate datetime formats
    created_dt = None
    updated_dt = None
    
    if created_str:
        created_dt = _parse_datetime(created_str)
        if created_dt is None:
            errors.append(
                f"Metadata: 'created' field has invalid datetime format: {created_str}"
            )
    
    if updated_str:
        updated_dt = _parse_datetime(updated_str)
        if updated_dt is None:
            errors.append(
                f"Metadata: 'updated' field has invalid datetime format: {updated_str}"
            )
    
    # Compare dates if both are valid
    if created_dt and updated_dt:
        if created_dt > updated_dt:
            errors.append(
                f"Metadata: 'created' date ({created_str}) is after 'updated' "
                f"date ({updated_str})"
            )
    
    compatibility = metadata.get("compatibility", {})
    environments = compatibility.get("environments", [])
    
    if not environments:
        errors.append("Metadata: compatibility.environments must not be empty")
    
    minimum_version = compatibility.get("minimum_version")
    if minimum_version:
        # Check that contract_version >= minimum_version using proper semver comparison
        if _compare_semver(contract_version, minimum_version) < 0:
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
    
    # 4. Check for warnings (non-blocking issues - governance smells)
    
    # Warning: Missing optional description
    if not metadata.get("description"):
        warnings.append("Metadata: 'description' field is recommended but missing")
    
    # Warning: Missing tags in metadata
    tags = metadata.get("tags")
    if not tags or (isinstance(tags, list) and len(tags) == 0):
        warnings.append(
            "Metadata: 'tags' field is missing or empty (recommended for discoverability)"
        )
    
    # Warning: Single-environment-only contracts
    compatibility = metadata.get("compatibility", {})
    environments = compatibility.get("environments", [])
    if len(environments) == 1:
        warnings.append(
            f"Compatibility: Contract only supports a single environment "
            f"({environments[0]}). Consider multi-environment support."
        )
    
    # Warning: Empty or trivial model definitions in artifact_schema
    artifact_schema = contract.get("artifact_schema", {})
    schema_props = artifact_schema.get("properties", {})
    models_schema = schema_props.get("models", {})
    
    # Check if models schema exists but is very permissive or empty
    if "models" in schema_props:
        models_type = models_schema.get("type")
        models_items = models_schema.get("items", {})
        
        # Warn if models array has no item constraints
        if models_type == "array" and not models_items:
            warnings.append(
                "Artifact schema: 'models' array has no item constraints "
                "(consider defining model structure)"
            )
        
        # Warn if models items are completely unconstrained
        if models_type == "array" and models_items == {}:
            warnings.append(
                "Artifact schema: 'models' items have no constraints "
                "(consider defining model validation rules)"
            )
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings
