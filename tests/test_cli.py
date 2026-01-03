"""Tests for Base120 CLI."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXAMPLES_PATH = ROOT / "examples" / "contracts"


def test_cli_validate_valid_contract(tmp_path):
    """Test CLI with a valid contract."""
    contract_path = EXAMPLES_PATH / "valid-basic-contract.json"
    output_path = tmp_path / "test_valid_report.json"
    
    result = subprocess.run(
        [sys.executable, "-m", "base120.cli", "validate-contract", 
         str(contract_path), "-o", output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Expected success but got: {result.stderr}"
    assert Path(output_path).exists()
    
    # Check report content
    with open(output_path) as f:
        report = json.load(f)
    
    assert report["service_name"] == "user-authentication-service"
    assert report["validation_status"] == "pass"
    assert len(report["errors"]) == 0
    assert "validated_environments" in report["compatibility"]


def test_cli_validate_invalid_contract(tmp_path):
    """Test CLI with an invalid contract (termination edge)."""
    contract_path = EXAMPLES_PATH / "invalid-termination-edge.json"
    output_path = tmp_path / "test_invalid_report.json"
    
    result = subprocess.run(
        [sys.executable, "-m", "base120.cli", "validate-contract",
         str(contract_path), "-o", output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1, "Expected failure exit code"
    assert Path(output_path).exists()
    
    # Check report content
    with open(output_path) as f:
        report = json.load(f)
    
    assert report["service_name"] == "invalid-service"
    assert report["validation_status"] == "fail"
    assert len(report["errors"]) > 0


def test_cli_validate_missing_metadata(tmp_path):
    """Test CLI with a contract missing required metadata."""
    contract_path = EXAMPLES_PATH / "invalid-missing-metadata.json"
    output_path = tmp_path / "test_missing_metadata_report.json"
    
    result = subprocess.run(
        [sys.executable, "-m", "base120.cli", "validate-contract",
         str(contract_path), "-o", output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1, "Expected failure exit code"
    assert Path(output_path).exists()
    
    # Check report content
    with open(output_path) as f:
        report = json.load(f)
    
    assert report["validation_status"] == "fail"
    assert len(report["errors"]) > 0
    assert any("metadata" in err.lower() for err in report["errors"])


def test_cli_file_not_found():
    """Test CLI with non-existent file."""
    result = subprocess.run(
        [sys.executable, "-m", "base120.cli", "validate-contract",
         "/nonexistent/file.json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 2, "Expected file-not-found exit code"
    assert "not found" in result.stderr.lower()


def test_cli_invalid_json(tmp_path):
    """Test CLI with malformed JSON."""
    # Create a temp file with invalid JSON
    temp_file = tmp_path / "invalid.json"
    temp_file.write_text("{ invalid json }")
    
    result = subprocess.run(
        [sys.executable, "-m", "base120.cli", "validate-contract",
         str(temp_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 3, "Expected invalid-json exit code"
    assert "invalid json" in result.stderr.lower()


def test_cli_default_output_path():
    """Test CLI uses default output path when not specified."""
    contract_path = EXAMPLES_PATH / "valid-basic-contract.json"
    default_output = Path("contract_report.json")
    
    # Clean up any existing default output
    if default_output.exists():
        default_output.unlink()
    
    result = subprocess.run(
        [sys.executable, "-m", "base120.cli", "validate-contract",
         str(contract_path)],
        capture_output=True,
        text=True,
        cwd=ROOT
    )
    
    assert result.returncode == 0
    # Default output should be created
    output_path = ROOT / default_output
    assert output_path.exists(), "Default output file should be created"
    
    # Clean up
    output_path.unlink()
