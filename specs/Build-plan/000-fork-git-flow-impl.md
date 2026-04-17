# Fork Git Flow Implementation Plan

Fine-grained tasks to implement the fork-based distribution workflow.

## Prerequisites

- [x] Local clone of AvonS/hermes-agent at `$HERMES_HOME/hermes-agent`
- [x] `$HERMES_HOME` environment variable set
- [x] Shell access (bash/zsh)

**Status:** ✅ COMPLETE - all prerequisites met

---

## Task 1: Set Up hermes Directory

**Goal:** Create user config directory at `$HERMES_HOME`

- [x] 1.1 Create `$HERMES_HOME` parent directory
- [x] 1.2 Create `hermes/` subdirectory
- [x] 1.3 Add export to shell RC (`~/.zshrc` or `~/.bashrc`)
- [x] 1.4 Verify: `echo $HERMES_HOME` returns correct path

**Status:** ✅ COMPLETE - hermes directory already set up at `~/Work/Explore/hermes/hermes`

---

## Task 2: Set Up Local Git Hooks

**Goal:** Block direct commits to protected branches

- [ ] 2.1 Create `.git/hooks/pre-commit` script
- [ ] 2.2 Make it executable (`chmod +x`)
- [ ] 2.3 Test: try commit to `dev` branch (should fail)
- [ ] 2.4 Test: commit to `feature/test` (should succeed)

**Expected pre-commit content:**
```bash
#!/bin/bash
protected="main dev release"
branch=$(git branch --show-current)
for prot in $protected; do
    if [ "$branch" = "$prot" ]; then
        echo "❌ Direct commit to $prot blocked. Use hg wrapper."
        exit 1
    fi
done
```

---

## Task 3: Create hg Wrapper Script

**Goal:** Provide safe workflow commands

- [ ] 3.1 Create `~/bin/hg` wrapper script
- [ ] 3.2 Implement `hg feature start <name>`
- [ ] 3.3 Implement `hg feature finish`
- [ ] 3.4 Implement `hg release <version>`
- [ ] 3.5 Implement `hg sync`
- [ ] 3.6 Add toPATH and make executable

**Commands to implement:**
| Command | Action |
|---------|--------|
| `hg feature start <name>` | Create `feature/<name>` from dev, switch to it |
| `hg feature finish` | Merge feature into dev, switch back to dev |
| `hg release <version>` | Merge dev into release, create tag |
| `hg sync` | Fetch upstream, merge main → dev |
| `hg status` | Show current branch + pending changes |

---

## Task 4: Protect $HERMES_HOME

**Goal:** Ensure user data is never committed to git

- [x] 4.1 Initialize `hermes/` (dev) or `.hermes/` (prod) directory
- [x] 4.2 Create `.gitignore` with:
  ```
  .env
  sessions/
  memories/
  skills/
  state.db
  ```
- [x] 4.3 Verify: `git status` shows clean (no secrets)

**Status:** ✅ COMPLETE - hermes directory is not a git repo, protected from accidental commits

---

## Task 5: Initial Commit to Dev

**Goal:** Push first changes to fork dev branch

- [ ] 5.1 Switch to `dev` branch
- [ ] 5.2 Make a test commit (e.g., this plan file)
- [ ] 5.3 Push to `origin dev`

---

## Verification

Run these to verify setup:
```bash
# Should show dev branch
hg status

# Should fail
cd hermes-agent && git commit -m "test" --allow-empty
# Expected: "❌ Direct commit to dev blocked"

# Should succeed  
hg feature start test-feature
# Should be on: feature/test-feature
```

---

## Notes

- Task breakdown: 15 fine-grained tasks
- Estimated time: 1-2 hours
- Can be done incrementally