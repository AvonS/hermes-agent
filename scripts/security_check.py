#!/usr/bin/env python3
"""
Security check script - runs on changed files only.
Designed for pre-commit hooks and CI pipelines.

Usage:
    python scripts/security_check.py              # check staged files
    python scripts/security_check.py --base main   # compare against main
    python scripts/security_check.py --base dev   # compare against dev
    python scripts/security_check.py --full           # full repo scan (bypass)
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Extensions to check
CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx"}
DEP_FILES = {"requirements.txt", "pyproject.toml", "package.json", "uv.lock"}


from typing import Optional

def run_cmd(cmd: list[str], cwd: Optional[Path] = None) -> tuple[int, str]:
    """Run command and return (exit_code, stdout+stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=300
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 124, "Timeout"
    except FileNotFoundError:
        return 127, f"Command not found: {cmd[0]}"
    except Exception as e:
        return 1, str(e)


def get_changed_files(base: str = "HEAD", cached: bool = True) -> set[Path]:
    """Get changed files compared to base."""
    files = set()
    
    # Get list of changed files
    if cached:
        cmd = ["git", "diff", "--cached", "--name-only", base]
    else:
        cmd = ["git", "diff", "--name-only", base]
    
    code, out = run_cmd(cmd)
    if code == 0:
        for f in out.strip().split("\n"):
            if f and Path(f).suffix in CODE_EXTENSIONS:
                files.add(Path(f))
    
    # Also check untracked Python files
    cmd = ["git", "status", "--porcelain"]
    code, out = run_cmd(cmd)
    if code == 0:
        for line in out.strip().split("\n"):
            if line.startswith("?? ") and Path(line[2:]).suffix in CODE_EXTENSIONS:
                files.add(Path(line[2:]))
    
    return files


def get_dep_files() -> list[Path]:
    """Find dependency files in repo."""
    repo_root = Path(__file__).parent.parent
    deps = []
    for f in DEP_FILES:
        path = repo_root / f
        if path.exists():
            deps.append(path)
    return deps


def check_bandit(files: set[Path]) -> tuple[int, str]:
    """Run bandit on changed Python files."""
    if not files:
        return 0, "No Python files changed"
    
    # Filter to Python files only
    py_files = [str(f) for f in files if f.suffix == ".py"]
    if not py_files:
        return 0, "No Python files to check"
    
    print(f"  Running bandit on {len(py_files)} file(s)...")
    return run_cmd(["bandit", "-r", "-f", "txt", *py_files])


def check_safety() -> tuple[int, str]:
    """Check Python dependencies for vulnerabilities."""
    deps = get_dep_files()
    py_deps = [str(f) for f in deps if f.suffix in {".txt", ".toml"}]
    
    if not py_deps:
        return 0, "No Python dep files found"
    
    print(f"  Running safety on {len(py_deps)} file(s)...")
    return run_cmd(["safety", "check", "--json", "--file", py_deps[0]])


def check_pip_audit() -> tuple[int, str]:
    """Check Python dependencies with pip-audit."""
    deps = get_dep_files()
    uv_lock = [f for f in deps if f.name == "uv.lock"]
    
    if not uv_lock:
        return 0, "No uv.lock found"
    
    print(f"  Running pip-audit on uv.lock...")
    return run_cmd(["pip-audit", "-r", str(uv_lock[0]), "--format", "json"])


def check_npm_audit() -> tuple[int, str]:
    """Check npm dependencies."""
    deps = get_dep_files()
    pkg = [f for f in deps if f.name == "package.json"]
    
    if not pkg:
        return 0, "No package.json found"
    
    print(f"  Running npm audit...")
    return run_cmd(["npm", "audit", "--json"], cwd=pkg[0].parent)


def main():
    parser = argparse.ArgumentParser(description="Security check on changed files")
    parser.add_argument("--base", default="HEAD", help="Base commit/branch to compare")
    parser.add_argument("--cached", action="store_true", default=True, help="Check staged files")
    parser.add_argument("--cached-only", dest="cached", action="store_false", help="Check unstaged files")
    parser.add_argument("--full", action="store_true", help="Full repo scan (bypass)")
    parser.add_argument("--all", action="store_true", help="Run all checks (default: security only)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent
    print(f"=== Security Check ===")
    print(f"Repo: {repo_root.name}")
    
    if args.full:
        print("Mode: FULL REPO SCAN")
        files = set(repo_root.rglob("*.py"))
    else:
        files = get_changed_files(args.base, args.cached)
        print(f"Mode: CHANGED FILES ({args.base})")
        print(f"Changed: {len(files)} file(s)")
    
    if not files and not args.full:
        print("No files to check.")
        return 0
    
    # Run security checks
    all_passed = True
    
    # Bandit (always run on Python files)
    if files:
        code, out = check_bandit(files)
        if code != 0:
            print(f"[FAIL] bandit found issues")
            if not args.quiet:
                print(out[:2000])
            all_passed = False
        else:
            print(f"[PASS] bandit")
    
    # Safety (Python deps)
    code, out = check_safety()
    if code == 0:
        print(f"[PASS] safety")
    elif code == 127:
        print(f"[SKIP] safety not installed")
    else:
        print(f"[FAIL] safety found vulnerabilities")
        if not args.quiet:
            print(out[:2000])
        all_passed = False
    
    # pip-audit (Python deps)
    code, out = check_pip_audit()
    if code == 0:
        print(f"[PASS] pip-audit")
    elif code == 127:
        print(f"[SKIP] pip-audit not installed")
    else:
        print(f"[FAIL] pip-audit found vulnerabilities")
        if not args.quiet:
            print(out[:2000])
        all_passed = False
    
    # npm audit (JS deps)  
    code, out = check_npm_audit()
    if code == 0:
        print(f"[PASS] npm audit")
    elif code == 127:
        print(f"[SKIP] npm not available")
    else:
        print(f"[FAIL] npm audit found vulnerabilities")
        if not args.quiet:
            print(out[:2000])
        all_passed = False
    
    print("=" * 20)
    if all_passed:
        print("✅ All security checks passed")
        return 0
    else:
        print("❌ Security issues found")
        return 1


if __name__ == "__main__":
    sys.exit(main())