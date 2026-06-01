#!/bin/bash
# Install fork-specific git hooks
# Run this after cloning or pulling updates

HOOK_DIR="$(dirname "$0")/.git/hooks"
mkdir -p "$HOOK_DIR"

# Pre-commit hook (blocks direct commits to protected branches)
cp "$(dirname "$0")/scripts/pre-commit-hook" "$HOOK_DIR/pre-commit" 2>/dev/null || {
    cat > "$HOOK_DIR/pre-commit" << 'HOOK'
#!/bin/bash
# Pre-commit hook to block direct commits to protected branches
# Fork-specific: prevents accidental commits to main, dev, release

protected="main dev release"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    exit 0
fi

branch=$(git branch --show-current 2>/dev/null)

for prot in $protected; do
    if [ "$branch" = "$prot" ]; then
        echo "❌ Direct commit to '$prot' is blocked."
        echo "   Use the feature branch workflow:"
        echo "   - hg feature start <name>  to start a feature"
        echo "   - hg feature finish   to finish and merge"
        exit 1
    fi
done

exit 0
HOOK
    chmod +x "$HOOK_DIR/pre-commit"
}

echo "✓ Installed pre-commit hook"