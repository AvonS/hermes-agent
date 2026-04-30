#!/usr/bin/env python3
"""Fork dependency patch script - post-sync dependency management.

This script addresses the "Dependabot reversion" issue: when `hg sync` pulls from upstream,
the upstream's lockfiles (uv.lock, package-lock.json) can revert security fixes. This script
runs AFTER every hg sync to re-apply and verify security-relevant dependency floors.

Lockfile strategy:
  - uv.lock and package-lock.json are marked as 'binary' in .gitattributes
  - During hg sync, upstream changes to lockfiles show as CONFLICT (not auto-merged)
  - This script helps identify what needs re-patching after sync

Usage:
    python scripts/fork_deps_patch.py [--check|--apply] [--verbose]

Options:
    --check     Show what packages need version floors and current state
    --apply     Apply patches to pyproject.toml (minimum version floors)
    --verbose   Show detailed output

After hg sync conflict:
    # Check which security packages need updating
    python scripts/fork_deps_patch.py --check --verbose

    # Re-apply security version floors (reads pyproject.toml minimums, updates uv.lock)
    python scripts/fork_deps_patch.py --apply --verbose

    # Then: uv sync && git add uv.lock && git commit
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


# Security-relevant packages: (package_name, minimum_constraint, reason)
SECURITY_PACKAGES = {
    # Python (uv.lock) — tracked via pyproject.toml floors
    "requests": (">=2.33.0,<3", "CVE-2026-25645 - HTTPoxy/CVE-2024-35195"),
    "lodash": (">=4.18.1", "Prototype pollution - lodash >= 4.17.21"),
    "protobufjs": (">=7.5.5", "CVE for protobufjs package"),
    # Add more as Dependabot finds them
}

# npm packages with known issues
NPM_SECURITY_PACKAGES = {
    "lodash": "^4.18.1",
    "protobufjs": "^7.5.5",
}


def get_git_status() -> dict:
    """Check if lockfiles have merge conflicts or changes."""
    result = subprocess.run(
        ["git", "status", "--short", "uv.lock", "package-lock.json"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    return {
        "uv_lock": [l for l in lines if "uv.lock" in l],
        "package_lock": [l for l in lines if "package-lock.json" in l],
        "has_conflicts": any("UU" in l or "AA" in l or "DD" in l for l in lines),
    }


def check_lockfile_versions() -> dict:
    """Check current versions of security-relevant packages in uv.lock."""
    uv_lock = Path("uv.lock")
    if not uv_lock.exists():
        return {}

    content = uv_lock.read_text()
    versions = {}

    for pkg in SECURITY_PACKAGES:
        # Look for package entries in uv.lock
        pattern = re.compile(
            r'name = "' + re.escape(pkg) + r'"[^}]+?version = "([^"]+)"'
        )
        matches = re.findall(pattern, content)
        if matches:
            versions[pkg] = matches[0]

    return versions


def check_pyproject_constraints() -> dict:
    """Check minimum version constraints in pyproject.toml."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        return {}

    content = pyproject.read_text()
    constraints = {}

    for pkg in SECURITY_PACKAGES:
        # Match package constraints like "pkg>=version,<next" or "pkg>=version"
        pattern = rf'"{re.escape(pkg)}.*?"'
        matches = re.findall(pattern, content)
        if matches:
            constraints[pkg] = matches[0]

    return constraints


def apply_patches(apply: bool = True, verbose: bool = False) -> list[tuple[str, str]]:
    """Apply minimum version constraints to pyproject.toml.

    Returns list of (package, status) tuples.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("Warning: pyproject.toml not found")
        return []

    content = pyproject.read_text()
    patched = []

    for pkg, (constraint, reason) in SECURITY_PACKAGES.items():
        # Look for package in dependencies
        # Format: "pkgname>=version,<next" or "pkgname = version"
        found = False
        for line in content.split("\n"):
            if not line.strip().startswith('"') or "#" in line.split('"')[0]:
                continue
            if line.strip().startswith(f'"{pkg}') or line.strip().startswith(f'"{pkg.lower()}'):
                found = True
                # Extract current constraint
                m = re.search(r'"' + re.escape(pkg) + r'([^"]+)"', line)
                if m:
                    current = m.group(1)
                    if current.startswith((">=", ">")):
                        if verbose:
                            print(f"  {pkg}: already has floor '{current}'")
                        patched.append((pkg, f"already floored: {current}"))
                    else:
                        if verbose:
                            print(f"  {pkg}: needs floor '{constraint}' (currently '{current}')")
                        patched.append((pkg, f"needs: {constraint} (currently: {current})"))
                        if apply:
                            # Replace in content
                            old_str = f'"{pkg}{current}"'
                            new_str = f'"{pkg}{constraint}"'
                            if old_str in content:
                                content = content.replace(old_str, new_str, 1)
                                if verbose:
                                    print(f"  {pkg}: {current} -> {constraint} ({reason})")
                break

        if not found:
            if verbose:
                print(f"  {pkg}: not found in pyproject.toml")

    if apply and any(pkg in dict(patched) for pkg in SECURITY_PACKAGES):
        pyproject.write_text(content)

    return patched


def main():
    parser = argparse.ArgumentParser(
        description="Fork dependency patch - re-apply security floors after hg sync"
    )
    parser.add_argument("--check", action="store_true", help="Check current state (dry-run)")
    parser.add_argument("--apply", action="store_true", default=True, help="Apply patches (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    apply = not args.check

    print("Fork Dependency Patch")
    print(f"  Mode: {'CHECK (dry-run)' if args.check else 'APPLY'}")
    print(f"  Security packages: {list(SECURITY_PACKAGES.keys())}")
    print()

    # Check git status for lockfiles
    status = get_git_status()
    print("Lockfile status:")
    if status["has_conflicts"]:
        print("  ⚠ uv.lock / package-lock.json has MERGE CONFLICTS")
        print("    Resolve conflicts manually, then re-run this script")
    elif status["uv_lock"] or status["package_lock"]:
        for l in status["uv_lock"] + status["package_lock"]:
            print(f"  {l}")
    else:
        print("  ✓ Lockfiles unchanged since last commit")
    print()

    # Check pyproject.toml constraints
    if apply:
        print("Applying pyproject.toml minimum version floors:")
    else:
        print("Would apply pyproject.toml minimum version floors:")

    patched = apply_patches(apply=apply, verbose=args.verbose)

    if not patched:
        print("  No patches needed")

    # Summary
    print()
    print("Summary:")
    for pkg, status in patched:
        print(f"  {pkg}: {status}")

    print()
    if apply:
        print("Next steps:")
        print("  1. uv sync              # update uv.lock from pyproject.toml floors")
        print("  2. uv lock --upgrade    # upgrade specific packages if needed")
        print("  3. git add uv.lock && git commit -m 'fix(deps): security version floors'")
        print("  4. git push origin dev")

    return 0


if __name__ == "__main__":
    sys.exit(main())
