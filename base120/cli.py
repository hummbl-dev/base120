"""Base120 command-line interface."""
import sys
import json
import argparse
from pathlib import Path
from typing import Any

from base120.contract.validate import validate_contract
from base120.contract.report import generate_report


def load_json_file(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Error: Failed to read {path}: {e}", file=sys.stderr)
        sys.exit(4)


def validate_contract_command(args: argparse.Namespace) -> int:
    """
    Validate a contract unit file.
    
    Returns:
        0 if validation succeeds
        1 if validation fails
        2+ for other errors (file not found, invalid JSON, etc.)
    """
    contract_path = Path(args.contract_path)
    
    # Load contract unit
    contract = load_json_file(contract_path)
    
    # Load contract schema
    schema_path = Path(__file__).parent.parent / "schemas" / "v1.0.0" / "contract.schema.json"
    contract_schema = load_json_file(schema_path)
    
    # Validate contract
    is_valid, errors, warnings = validate_contract(contract, contract_schema)
    
    # Extract metadata for report
    service_name = contract.get("service_name", "unknown")
    metadata = contract.get("metadata", {})
    compatibility = metadata.get("compatibility", {})
    environments = compatibility.get("environments", [])
    
    # Generate report
    report = generate_report(
        service_name=service_name,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        validated_environments=environments
    )
    
    # Write report to file
    output_path = Path(args.output)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        print(f"Validation report written to: {output_path}")
    except Exception as e:
        print(f"Error: Failed to write report to {output_path}: {e}", file=sys.stderr)
        sys.exit(5)
    
    # Print validation results to stdout
    print(f"\nService: {service_name}")
    print(f"Status: {report['validation_status'].upper()}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    if is_valid:
        print("\n✓ Contract validation PASSED")
        return 0
    else:
        print("\n✗ Contract validation FAILED")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='base120',
        description='Base120 governance substrate CLI'
    )
    
    subparsers = parser.add_subparsers(
        title='commands',
        dest='command',
        required=True
    )
    
    # validate-contract command
    validate_parser = subparsers.add_parser(
        'validate-contract',
        help='Validate a contract unit file'
    )
    validate_parser.add_argument(
        'contract_path',
        help='Path to the contract unit JSON file'
    )
    validate_parser.add_argument(
        '-o', '--output',
        default='contract_report.json',
        help='Output path for validation report (default: contract_report.json)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Route to command handler
    if args.command == 'validate-contract':
        return validate_contract_command(args)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
