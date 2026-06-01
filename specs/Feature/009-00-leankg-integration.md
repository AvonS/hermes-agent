# 009-00-leankg-integration.md

## Problem Statement
Hermes currently lacks a standardized, fork‑specific mechanism for loading third‑party plug‑ins written for the Anthropic Claude ecosystem (e.g., the LeanKG `claude-plugin`). Without an explicit plug‑in folder and manifest loader, community contributed plug‑ins cannot be dropped into the Hermes environment, discovered at runtime, or automatically registered for use. This limits extensibility and the ability to adopt proven plug‑in patterns such as those demonstrated by the LeanKG project.

## Expected Behavior
1. **Plug‑in Discovery** – At startup Hermes scans a designated plug‑in directory (e.g., `$HERMES_HOME/.hermes/plugins/claude`) for files matching the LeanKG plug‑in manifest format (`plugin.json`).  
2. **Manifest Validation** – Each discovered manifest is validated against a minimal schema:
   - `name` (string) – human‑readable plug‑in name.  
   - `version` (string) – semantic version.  
   - `entrypoints` (object) – maps command names to executable scripts or functions.  
   - `dependencies` (array) – optional list of required Hermes skills or system packages.  
3. **Automatic Registration** – Valid plug‑ins are registered in Hermes’ internal plug‑in registry, making their commands available as if they were native Hermes sub‑commands (e.g., `hermes claude‑login`, `hermes claude‑invoke <operation>`).  
4. **Lifecycle Hooks** – Plug‑ins may provide optional lifecycle scripts (`install`, `upgrade`, `remove`) placed in a `hooks/` sub‑folder that Hermes will execute at the corresponding lifecycle event.  
5. **Isolation** – Each plug‑in runs in its own sandboxed process (via `subprocess.Popen` with a deterministic environment) to prevent accidental state leakage.  

## Why Fork‑Specific
The plug‑in loading architecture is not part of upstream Hermes; it is a **fork‑managed extension** that enables community plug‑ins to be version‑controlled alongside the fork without being overwritten during upstream sync. By keeping the plug‑in directory and loader within the fork, we can iterate quickly, add testing hooks, and maintain compatibility with the fork’s release process while preserving the ability to re‑apply changes after each upstream merge.

## Risks if Lost
- **FutureSyncClobber** – If the plug‑in folder and loader are not formally registered in the fork‑maintenance checklist, an upstream sync could delete or overwrite the directory, causing loss of all third‑party plug‑ins.  
- **MissedCommunityGrowth** – Without documentation, external contributors cannot discover how to publish plug‑ins for Hermes, stalling ecosystem growth.  
- **InconsistentBehavior** – Informal plug‑in usage may diverge across forks, leading to fragmented implementations and maintenance burden.  

## Initial Tasks (draft)

1. **Create Plug‑in Directory** – `mkdir -p $HERMES_HOME/.hermes/plugins/claude`.  
2. **Copy LeanKG Manifest** – Copy the contents of `https://github.com/FreePeak/LeanKG/tree/main/.claude-plugin` into the new directory, preserving sub‑folders (`hooks/`, `skills/`, `INSTALL.md`, `plugin.json`).  
3. **Schema Bind** – Add a validation step (`scripts/validate_plugin_schema.py`) that checks each `plugin.json` against the schema defined in `specs/Feature/009-00-leankg-integration.md`.  
4. **Implement Loader** – Extend `hermes_cli/plugins.py` (or create a new module) to scan the plug‑in directory on Hermes start‑up, load each `plugin.json`, and register entrypoints.  
5. **Add Lifecycle Hooks** – Ensure Hermes executes `hooks/install`, `hooks/upgrade`, and `hooks/remove` scripts (if present) at the appropriate moments.  
6. **Write Test Skill** – Add a minimal “hello‑world” plug‑in under `skills/` that demonstrates the plug‑in loading flow; include a corresponding test `tests/fork/test_plugins.py` that asserts the plug‑in appears in `hermes plugin list`.  
7. **Update Documentation** – Add a short “Plug‑in Development” section to the project wiki (`wiki/AGENTS.md` or `wiki-session-knowledge-base`) outlining the directory layout, manifest format, and testing workflow.  
8. **Verify Integration** – Run `hermes plugin list` and confirm the new plug‑in appears, then invoke a sample command to confirm functionality.  

*All tasks should be tracked in a Build‑plan file (e.g., `specs/Build-plan/009-00-leankg-integration.md`) once the spec is approved.*
