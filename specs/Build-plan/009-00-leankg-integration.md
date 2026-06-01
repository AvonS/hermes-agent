## Tasks
- [ ] 1. Create the fork‑managed plug‑in directory: `mkdir -p $HERMES_HOME/.hermes/plugins/claude`
- [ ] 2. Copy the LeanKG plug‑in source (`https://github.com/FreePeak/LeanKG/tree/main/.claude-plugin`) into `$HERMES_HOME/.hermes/plugins/claude`, preserving sub‑folders (`hooks/`, `skills/`, `INSTALL.md`, `plugin.json`)
- [ ] 3. Add a schema validation script `scripts/validate_plugin_schema.py` that checks each `plugin.json` against the minimal schema (name, version, entrypoints, dependencies)
- [ ] 4. Extend or create `hermes_cli/plugins.py` (or equivalent loader module) to scan the plug‑in directory on Hermes start‑up, validate manifests, and register entrypoints as native sub‑commands
- [ ] 5. Implement lifecycle‑hook execution (`hooks/install`, `hooks/upgrade`, `hooks/remove`) so that any scripts placed in those folders run at the appropriate lifecycle event
- [ ] 6. Write a minimal “hello‑world” plug‑in under `skills/` (e.g., `hello_claude.py`) that demonstrates the plug‑in loading flow; add corresponding test `tests/fork/test_plugins.py` asserting the plug‑in appears in `hermes plugin list`
- [ ] 7. Update documentation: add a “Plug‑in Development” section to the project wiki (`wiki/AGENTS.md` or `wiki-session-knowledge-base`) covering directory layout, manifest format, and testing workflow
- [ ] 8. Verify integration by running `hermes plugin list` and invoking a sample plug‑in command; ensure all checklist items pass

## Test Plan
- [ ] Add unit test `tests/fork/test_plugins.py` to verify plug‑in discovery and registration
- [ ] Run the full fork test suite: `pytest tests/fork/ -v`
- [ ] Confirm that the new plug‑in appears in `hermes plugin list` and can execute a test command successfully

## Implementation Details
- **File locations**:  
  - Directory: `$HERMES_HOME/.hermes/plugins/claude` (fork‑managed)  
  - Validation script: `scripts/validate_plugin_schema.py`  
  - Loader module: `hermes_cli/plugins.py` (modify or create)  
  - Lifecycle hook scripts: `hooks/` sub‑folders inside each plug‑in  
  - Test skill: `skills/hello_claude.py` (or similar)  
  - Test file: `tests/fork/test_plugins.py`  

- **Code changes**:  
  - Extend plug‑in discovery logic to handle `.json` manifests and optional `hooks/*` scripts.  
  - Register discovered entrypoints in Hermes’ command registry so they are accessible via `hermes <plugin‑command>`.  
  - Ensure isolation by spawning plug‑in commands in separate subprocesses with a clean environment.  

- **Verification**:  
  - After implementing the loader, run `hermes plugin list` and observe the new plug‑in listed.  
  - Execute a sample plug‑in command (e.g., `hermes hello-claude`) and confirm expected output.  
  - Ensure the test suite passes and that no existing upstream‑synced tests are broken.
