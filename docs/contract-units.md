# Base120 Contract Units

## Overview

Contract units are the core governance artifacts in Base120. They encapsulate:
- **Schemas**: JSON Schema definitions for artifacts
- **Failure Graphs**: Failure mode nodes with retry, escalation, and termination rules
- **Metadata**: Version information and environment compatibility

Contract units provide design-time decision surfaces and enable validation in CI/CD pipelines.

---

## CLI Usage

### Installation

Install Base120 with pip:

```bash
pip install base120
```

### Validating a Contract Unit

Use the `base120 validate-contract` command to validate a contract unit:

```bash
base120 validate-contract <path-to-contract.json>
```

**Options:**
- `-o, --output PATH`: Specify output path for validation report (default: `contract_report.json`)

**Exit Codes:**
- `0`: Validation succeeded
- `1`: Validation failed (errors detected)
- `2`: File not found
- `3`: Invalid JSON syntax
- `4`: File read error
- `5`: Report write error

**Example:**

```bash
base120 validate-contract examples/contracts/valid-basic-contract.json -o report.json
```

---

## Contract Unit Structure

### Required Fields

All contract units must include:

1. **`contract_version`** (string): Version of the contract unit specification (e.g., `"v1.0.0"`)

2. **`service_name`** (string): Name of the service this contract governs

3. **`artifact_schema`** (object): JSON Schema for artifacts validated by this contract
   - Must include `$schema` and `type` fields
   - Defines the structure of artifacts this contract validates

4. **`failure_graph`** (object): Failure mode graph with retry, escalation, and termination rules
   - **`nodes`** (array): Failure mode nodes in the graph
   - **`edges`** (array): Edges between nodes (escalation paths)

5. **`metadata`** (object): Contract metadata
   - **`created`** (string): ISO 8601 timestamp
   - **`updated`** (string): ISO 8601 timestamp
   - **`compatibility`** (object): Environment compatibility information
     - **`environments`** (array): List of validated environments (non-empty)
     - **`minimum_version`** (string, optional): Minimum contract version required

---

## Failure Graph Specification

### Node Structure

Each node in the failure graph represents a failure mode:

```json
{
  "id": "FM15",
  "name": "Schema Non-Compliance",
  "max_retries": 0,
  "action": "terminate"
}
```

**Fields:**
- **`id`**: Failure mode identifier (format: `FM` followed by digits)
- **`name`**: Human-readable name
- **`max_retries`**: Maximum retry attempts (0-10)
- **`action`**: Action to take (`"retry"`, `"escalate"`, or `"terminate"`)

### Edge Structure

Edges define escalation paths between failure modes:

```json
{
  "from": "FM17",
  "to": "FM30",
  "condition": "max_retries_exceeded"
}
```

**Fields:**
- **`from`**: Source failure mode ID
- **`to`**: Target failure mode ID
- **`condition`**: Condition that triggers the escalation

### Semantic Rules

The validator enforces these semantic rules:

1. **Node Uniqueness**: All node IDs must be unique
2. **Valid References**: Edge `from` and `to` fields must reference existing nodes
3. **Termination Constraint**: Nodes with `action: "terminate"` cannot have outgoing edges
4. **Retry Limits**: `max_retries` must be between 0 and 10
5. **Termination Requirement**: At least one node must have `action: "terminate"`

---

## Validation Report

The CLI generates a machine-readable JSON report:

```json
{
  "service_name": "user-authentication-service",
  "validation_status": "pass",
  "timestamp": "2026-01-03T17:30:00.123456+00:00",
  "errors": [],
  "warnings": [
    "Metadata: 'description' field is recommended but missing"
  ],
  "compatibility": {
    "validated_environments": ["production", "staging", "development"]
  }
}
```

**Fields:**
- **`service_name`**: Service name from the contract
- **`validation_status`**: `"pass"` or `"fail"`
- **`timestamp`**: ISO 8601 timestamp of validation
- **`errors`**: List of blocking errors (empty if validation passes)
- **`warnings`**: List of non-blocking warnings
- **`compatibility`**: Validated environments from contract metadata

---

## Examples

### Valid Basic Contract

```json
{
  "contract_version": "v1.0.0",
  "service_name": "user-authentication-service",
  "artifact_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["id", "domain", "class", "instance", "models"],
    "properties": {
      "id": { "type": "string" },
      "domain": { "type": "string" },
      "class": { "type": "string" },
      "instance": { "type": "string" },
      "models": {
        "type": "array",
        "items": { "type": "string" }
      }
    }
  },
  "failure_graph": {
    "nodes": [
      {
        "id": "FM15",
        "name": "Schema Non-Compliance",
        "max_retries": 0,
        "action": "terminate"
      },
      {
        "id": "FM17",
        "name": "Authorization Failure",
        "max_retries": 3,
        "action": "escalate"
      },
      {
        "id": "FM30",
        "name": "Unrecoverable System State",
        "max_retries": 0,
        "action": "terminate"
      }
    ],
    "edges": [
      {
        "from": "FM17",
        "to": "FM30",
        "condition": "max_retries_exceeded"
      }
    ]
  },
  "metadata": {
    "created": "2026-01-03T17:00:00Z",
    "updated": "2026-01-03T17:00:00Z",
    "description": "Contract unit for user authentication service",
    "compatibility": {
      "environments": ["production", "staging", "development"],
      "minimum_version": "v1.0.0"
    },
    "tags": ["authentication", "user-management"]
  }
}
```

### Common Validation Errors

**Error: Missing Required Field**
```
Schema error at 'root': 'metadata' is a required property
```

**Error: Termination Node with Outgoing Edge**
```
Termination node 'FM30' has outgoing edge to 'FM15' (termination nodes cannot escalate)
```

**Error: Invalid Node Reference**
```
Edge 0: 'to' node 'FM99' does not exist
```

**Error: No Termination Node**
```
Failure graph must contain at least one termination node
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Validate Contract Units

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install Base120
        run: pip install base120
      - name: Validate Contract
        run: base120 validate-contract contracts/service-contract.json
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

for contract in contracts/*.json; do
  echo "Validating $contract..."
  base120 validate-contract "$contract" || exit 1
done
```

---

## Extensibility

The contract unit specification is designed for extensibility. Future versions may add:

- Custom validation rules
- Additional failure graph semantics
- Extended metadata fields
- Artifact provenance tracking
- Cryptographic signatures

All extensions will maintain backward compatibility within the v1.x series.

---

## Mental Model

**Contracts as Governance Artifacts**

Contract units embody the principle that **contracts govern runtime behavior**:

1. **Design Time**: Define schemas, failure modes, and policies in contract units
2. **Validation Time**: Use CLI to validate contracts during development
3. **Deployment Time**: Bind code and infrastructure to contract constraints
4. **Runtime**: System behavior conforms to contract specifications

This model ensures that governance decisions are explicit, auditable, and enforceable.

---

## Governance Status

Contract unit validation is part of Base120 v1.0.x and follows the governance model:

- ✅ Schema is frozen (semantic changes require major version)
- ✅ Validation rules are deterministic
- ✅ Reports are machine-readable
- ✅ Backward compatibility guaranteed within v1.x

For questions or issues, see the [Base120 repository](https://github.com/hummbl-dev/base120).
