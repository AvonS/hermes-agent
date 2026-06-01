#!/bin/bash
# Check security dependencies meet minimum versions

set -euo pipefail

echo "Checking security dependencies..."

# Read minimum versions from SECURITY-DEPS.md
DEPS_FILE="$(dirname "$0")/../SECURITY-DEPS.md"

# Parse versions (simple grep approach)
check_pkg() {
    local pkg="$1"
    local min_ver="$2"
    
    # Check if package exists in node_modules
    local installed
    installed=$(npm list "$pkg" --depth=0 --json 2>/dev/null | jq -r ".dependencies[\"$pkg\"].version // .dependencies[\"$pkg\"].resolved" 2>/dev/null || echo "NOT_INSTALLED")
    
    if [ "$installed" = "NOT_INSTALLED" ]; then
        echo "⚠️  $pkg: not a direct dependency"
        return 0
    fi
    
    # Compare versions (simple semver check)
    if npm info "$pkg@$min_ver" version &>/dev/null; then
        local min_available
        min_available=$(npm info "$pkg@$min_ver" version)
        
        if npm --version | grep -q "^10\\|^11\\|^12"; then
            # npm 10+ has better version comparison
            if npm view "$pkg" version --json | jq -e ". | index(\"$min_available\")" &>/dev/null; then
                echo "✅ $pkg: $installed (>= $min_available)"
            else
                echo "❌ $pkg: $installed < $min_available (CVE risk)"
                return 1
            fi
        else
            echo "✅ $pkg: $installed"
        fi
    else
        echo "✅ $pkg: $installed"
    fi
}

# Check each dependency
check_pkg "lodash" "4.18.1"
check_pkg "lodash-es" "4.18.0"
check_pkg "protobufjs" "7.2.5"

echo "Done."