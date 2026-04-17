# Fork Versioning Scheme

## Format

```
<upstream_version>-avons.<fork_minor>.<fork_patch>
```

**Examples:**
- `0.10.0-avons.1.0` = upstream 0.10.0 + fork minor 1, patch 0
- `0.10.0-avons.1.1` = upstream 0.10.0 + fork minor 1, patch 1
- `0.11.0-avons.1.0` = upstream 0.11.0 + fork minor 1, patch 0

## Components

| Part | Meaning |
|------|---------|
| `0.10.0` | Upstream version from NousResearch/hermes-agent |
| `avons` | Fork identifier (AvonS/hermes-agent) |
| `1` | Fork minor version (incremented per fork release) |
| `0` | Fork patch version (hotfixes between releases) |

## Migration

When upstream releases a new version:
1. Update upstream version in fork (e.g., 0.10.0 → 0.11.0)
2. Reset fork minor/patch to `-avons.1.0`

| Fork Version | Upstream | Fork Changes |
|-------------|----------|--------------|
| 0.10.0-avons.1.0 | 0.10.0 | Initial fork release |
| 0.10.0-avons.1.1 | 0.10.0 | Hotfix #1 |
| 0.10.0-avons.2.0 | 0.10.0 | Fork release #2 |
| 0.11.0-avons.1.0 | 0.11.0 | Upstream upgrade |

## Why Not Semantic Version?

We keep upstream's major.minor.patch + add fork identifier:
- **Major/minor** - tracks upstream (0.10.0, 0.11.0, etc.)
- **Fork version** - our customizations (avons.X.Y)

This avoids "fork drift" and makes upstream sync clear.

---

## Changelog

### 0.10.0-avons.1.0 (2025-04-17)
**Upstream base:** 0.10.0

**Fork changes:**
- Add HERMES_HOME env var support
- Add fork git flow specification (specs/Overview/000-fork-git-flow.md)
- Add implementation plan (specs/Build-plan/000-fork-git-flow-impl.md)
- Add AGENTS.md with fork directory structure
- Add note to avoid hardcoding ~/.hermes in code
- Update INSTALL.md with fork setup instructions