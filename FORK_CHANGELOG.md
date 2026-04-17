# Fork Versioning Scheme

## Format

```
<upstream_version>-avons.<fork_minor>.<fork_patch>
```

Where `upstream_version` comes from `pyproject.toml`.

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
**Upstream base:** from `pyproject.toml`

**Fork changes:**
- Add HERMES_HOME env var support
- Add fork git flow specification (specs/Overview/000-fork-git-flow.md)
- Add implementation plan (specs/Build-plan/000-fork-git-flow-impl.md)
- Add AGENTS.md with fork directory structure
- Add note to avoid hardcoding ~/.hermes in code
- Update INSTALL.md with fork setup instructions

---

## Workflow: Feature → Dev → Release

### Branch Model
```
feature/<name>     # feature branch from dev
       ↓
dev              # development branch (default)
       ↓
release          # production branch (tagged releases)
```

### Process
1. **Create feature branch** from `dev`:
   ```bash
   git checkout -b feature/my-feature dev
   ```

2. **Work** on feature, commit regularly

3. **Merge to dev**:
   ```bash
   git checkout dev
   git merge feature/my-feature
   ```

4. **Test on dev**, verify changes

5. **Merge dev → release**:
   ```bash
   git checkout release
   git merge dev
   ```

6. **Create release** (run GitHub Actions workflow):
   - Go to: Actions → Fork Release → Run workflow
   - Choose "patch" or "minor"
   - Creates tag: `0.10.0-avons.1.0`

### Rollback
```bash
# Revert merge commit on dev
git revert -m 1 <merge-commit>
```

### Sync with Upstream
```bash
git fetch upstream main
git checkout dev
git merge upstream/main
# Fix any conflicts, test, then merge to release
```