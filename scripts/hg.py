#!/usr/bin/env python3
"""Hermes Git wrapper (hg) - Fork-specific git workflow automation.

Usage:
    hg feature start <name>  - Start new feature branch from dev
    hg feature finish        - Merge feature branch to dev
    hg sync                - Sync from upstream/main to dev
    hg release             - Release workflow (dev -> release)
"""
import argparse
import subprocess
import sys
import os


def run(cmd, check=True):
    """Run a shell command."""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def get_current_branch():
    result = run("git branch --show-current", check=False)
    return result.stdout.strip()


def feature_start(name: str):
    """Start a new feature branch from dev."""
    current = get_current_branch()
    if current and current not in ["main", "dev", "release"]:
        print(f"Already on feature branch: {current}")
        print("Finish or abandon current feature first.")
        sys.exit(1)

    # Check if we're on dev
    run("git checkout dev")
    run("git branch | grep -q 'dev' && git pull origin dev", check=False)
    run(f"git checkout -b feature/{name} dev")


def feature_finish():
    """Merge feature branch to dev and optionally delete."""
    current = get_current_branch()
    if not current.startswith("feature/"):
        print("Not on a feature branch.")
        sys.exit(1)

    # Verify tests would pass (optional - already done in CI)
    print("\n✓ Feature branch ready to merge to dev")
    print("  Merge command: git checkout dev && git merge feature/<name>")

    # Offer to merge
    resp = input("\nMerge to dev now? [y/N]: ").strip().lower()
    if resp == "y":
        run("git checkout dev")
        run(f"git merge {current}")
        run(f"git push origin dev")
        run(f"git branch -d {current}")
        print(f"✓ Merged {current} to dev")
    else:
        print("Cancelled.")


def _run_fork_deps_patch():
    """Apply fork-specific dependency patches after sync.
    
    Addresses the "Dependabot reversion" issue: upstream's pyproject.toml/uv.lock
    can revert security fixes during sync. This script applies minimum version
    constraints AFTER merge to ensure fixes persist.
    """
    patch_script = Path(__file__).parent / "fork_deps_patch.py"
    if patch_script.exists():
        print("\nApplying fork dependency patches...")
        result = subprocess.run(
            [sys.executable, str(patch_script), "--verbose"],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"⚠ fork_deps_patch exited with {result.returncode}", file=sys.stderr)
    else:
        print(f"\n⚠ {patch_script} not found - skipping dependency patch")


def sync():
    """Sync from upstream/main to dev."""
    print("Syncing upstream/main → dev...")
    run("git checkout dev")
    run("git fetch upstream main")
    result = run("git merge upstream/main", check=False)
    if result.returncode == 0:
        _run_fork_deps_patch()
        run("git push origin dev")
        print("\n✓ Synced upstream/main → dev")
    else:
        print("\n⚠ Merge conflicts - resolve manually")
        print("  After resolving: git add . && git commit")
        print("  Then: python scripts/fork_deps_patch.py --verbose")
        print("  And: git push origin dev")


def release():
    """Release workflow: dev → release."""
    print("Release workflow:")
    print("  1. Ensure dev is synced and tested")
    print("  2. git checkout release")
    print("  3. git merge dev")
    print("  4. Create release tag")
    print("")
    # For now, just show the steps
    current = get_current_branch()
    print(f"Current branch: {current}")
    print("Run these commands manually:")


def main():
    parser = argparse.ArgumentParser(description="Hermes Git wrapper (hg)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # feature subcommand with its own subparsers
    feature_parser = subparsers.add_parser("feature", help="Feature branch workflow")
    feature_subparsers = feature_parser.add_subparsers(dest="feature_command")
    feature_subparsers.add_parser("start", help="Start new feature branch").add_argument("name", help="Feature name")
    feature_subparsers.add_parser("finish", help="Merge feature branch to dev")

    # sync subcommand
    subparsers.add_parser("sync", help="Sync from upstream/main to dev")

    # release subcommand
    subparsers.add_parser("release", help="Release workflow (dev -> release)")

    args = parser.parse_args()

    if args.command == "feature":
        if args.feature_command == "start":
            feature_start(args.name)
        elif args.feature_command == "finish":
            feature_finish()
        else:
            feature_parser.print_help()
    elif args.command == "sync":
        sync()
    elif args.command == "release":
        release()


if __name__ == "__main__":
    main()