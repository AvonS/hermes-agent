#!/usr/bin/env python3
"""
Fork Test Runner - Run fork-specific tests after upstream sync.

Usage:
    python scripts/run_fork_tests.py [--verbose]

This script runs the fork-specific test suite to verify no regressions
were introduced during upstream sync.
"""

import subprocess
import sys
from pathlib import Path

# Get hermes-agent directory (where this script lives)
SCRIPT_DIR = Path(__file__).parent.resolve()
HERMES_AGENT_DIR = SCRIPT_DIR.parent  # scripts/ is inside hermes-agent/

# Fork test files and directories
FORK_TESTS = [
    "tests/fork/",
    "tests/hermes_cli/test_model_switch_opencode_anthropic.py",
    "tests/tools/test_approval.py",
]

# Fork-managed files to verify exist
FORK_MANAGED_FILES = [
    "tests/conftest.py",
    ".github/workflows/tests.yml",
    ".github/workflows/supply-chain-audit.yml",
    "AGENTS.md",
]


def run_tests(verbose: bool = False) -> bool:
    """Run fork-specific tests."""
    cmd = [
        sys.executable, "-m", "pytest",
        *FORK_TESTS,
        "-v" if verbose else "-q",
        "--override-ini=addopts=",
    ]
    
    result = subprocess.run(cmd, cwd=HERMES_AGENT_DIR)
    return result.returncode == 0


def verify_fork_managed_files() -> bool:
    """Verify fork-managed files exist."""
    missing = []
    for f in FORK_MANAGED_FILES:
        path = HERMES_AGENT_DIR / f
        if not path.exists():
            missing.append(f)
    
    if missing:
        print(f"Missing fork-managed files: {missing}")
        return False
    return True


def check_workflow_triggers() -> bool:
    """Verify workflow triggers are set to fork branches."""
    issues = []
    
    # Check tests.yml triggers dev
    tests_workflow = HERMES_AGENT_DIR / ".github/workflows/tests.yml"
    if tests_workflow.exists():
        content = tests_workflow.read_text()
        if "branches: [dev]" not in content:
            issues.append("tests.yml should trigger on dev branch")
        if "branches: [main]" in content:
            issues.append("tests.yml should NOT trigger on main branch")
    
    # Check nix.yml is disabled
    nix_workflow = HERMES_AGENT_DIR / ".github/workflows/nix.yml"
    if nix_workflow.exists():
        content = nix_workflow.read_text()
        if "branches: [do-not-run]" not in content:
            issues.append("nix.yml should be disabled (do-not-run)")
    
    if issues:
        print("Workflow trigger issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run fork tests after upstream sync")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Fork Test Runner - Post-Sync Verification")
    print("=" * 60)
    
    # Step 1: Verify fork-managed files
    print("\n[1/3] Verifying fork-managed files...")
    if not verify_fork_managed_files():
        print("❌ FAIL: Missing fork-managed files")
        sys.exit(1)
    print("✅ OK: Fork-managed files present")
    
    # Step 2: Check workflow triggers
    print("\n[2/3] Checking workflow triggers...")
    if not check_workflow_triggers():
        print("❌ FAIL: Workflow triggers not configured")
        sys.exit(1)
    print("✅ OK: Workflow triggers correct")
    
    # Step 3: Run tests
    print("\n[3/3] Running fork tests...")
    if not run_tests(args.verbose):
        print("❌ FAIL: Tests failed")
        sys.exit(1)
    print("✅ OK: All tests passed")
    
    print("\n" + "=" * 60)
    print("✅ Fork verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()