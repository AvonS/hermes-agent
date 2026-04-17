# Hermes Forked Custom Distribution Specification

## Overview

This specification defines a fork-based distribution model for hermes-agent that allows:
1. User custom features to survive upstream upgrades
2. Clean git flow with safety nets
3. Security best practices (secrets in `.env` only, unprivileged execution)
4. Cross-platform support (Mac, Windows, Linux)
5. Multiple install methods (local, VPS, Docker)

**Minimum YOLO by default** — Security fixes in fork:
- Block dangerous commands by default
- Run as unprivileged user
- Isolate working directory from home
- Block access to all dotfiles (`~/.*`)
- Keep secrets in .env only

---

## 1. Branch Model

### 1.1 Branch Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        upstream/main                            │
│                      (NousResearch/hermes-agent)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑ sync
┌─────────────────────────────────────────────────────────────────┐
│                         fork/main                               │
│                    (synced from upstream)                      │
│              ↑ merge from dev    │                              │
│              │                   ↓                              │
│         fork/dev ◄──────────────────────────────────────────┐   │
│    (default branch)                                          │   │
│              ↑ merge from feature/*                          │   │
│              │                                           │   │
│    feature/fix-* ──►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►┘     │
│    feature/feat-* ───────────────────────────────────────────►   │
│                                                                 │
│              ↑ merge from dev                                  │
│              │                                                │
│         fork/release                                          │
│    (tagged versions: v0.1.0, v0.2.0...)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Branch Rules

| Branch | Purpose | Can push directly? | Merge from |
|--------|---------|-------------------|-----------|
| `main` | Sync with upstream | No (protected) | upstream/main |
| `dev` | Development base | No (protected) | main, feature/* |
| `release` | Production ready | No (protected) | dev |
| `feature/*` | Feature work | Yes | dev |

### 1.3 Local Clone Structure

```
~/Work/Explore/hermes/
├── hermes-agent/          # git clone of AvonS/hermes-agent
│   ├── .git/             # local repo
│   ├── .git/hooks/       # local hooks (blocks main/dev/release push)
│   └── ...
├── hermes/              # user config at $HERMES_HOME (NOT a git repo)
│   ├── config.yaml
│   ├── .env
│   └── skills/
└── specs/                # feature specs
```

---

## 2. Git Workflow

### 2.1 Protected Branches

Local git hooks prevent direct commits to protected branches:

```python
# .git/hooks/pre-commit (blocks main/dev/release)
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

### 2.2 hg Wrapper Commands

The `hg` wrapper script (~/bin/hg) provides safe workflow commands:

| Command | Action |
|---------|--------|
| `hg feature start <name>` | Create `feature/<name>` from dev, switch to it |
| `hg feature finish` | Merge feature into dev, switch back to dev |
| `hg release` | Merge dev into release, create tag |
| `hg sync` | Fetch upstream, merge main → dev |
| `hg status` | Show current branch + pending changes |

### 2.3 Typical Workflow

```bash
# 1. Start a new feature
hg feature start cli-flicker-fix

# 2. Make changes (edit files)
$EDITOR cli.py
git add -A && git commit -m "Fix CLI flicker"

# 3. Finish feature (merges to dev)
hg feature finish

# 4. When ready for release
hg release v0.2.0
```

---

## 3. Security Model

### 3.1 $HERMES_HOME Protection

**Never push $HERMES_HOME to git** — contains secrets (use `hermes/` in dev, `.hermes/` in prod):

```
$HERMES_HOME/       # LOCAL ONLY, NOT a git repo
├── .env              # API keys, tokens
├── sessions/         # conversation history
└── memories/         # agent memory
```

If accidentally initialized as git:
```bash
# Fix immediately
echo ".env" >> $HERMES_HOME/.gitignore
echo "sessions/" >> $HERMES_HOME/.gitignore
```

### 3.2 Execution Security

| Setting | Value | Rationale |
|---------|-------|----------|
| Run as | unprivileged user | Limit blast radius |
| Working dir | `$HERMES_HOME` | Isolate from home |
| Dotfiles | blocked (`~/.*`) | Prevent home access |
| Secrets | `$HERMES_HOME/.env` only | Single secret source |

---

## 4. Environment Variables

### 4.1 Required Variables

```bash
# Required - point to user data directory (parent of .hermes)
export HERMES_HOME=~/Work/Explore/hermes

# Optional - override default model
export HERMES_MODEL=anthropic/claude-sonnet-4

# Optional - enable debug logging
export HERMES_DEBUG=1
```

### 4.2 Config Precedence

1. `$HERMES_HOME/config.yaml` — primary config
2. `~/.hermes/config.yaml` — fallback (if HERMES_HOME not set)

---

## 5. Architecture (Detailed)

### 5.1 Fork-Based Distribution

```
┌─────────────────────────────────────────────────────────┐
│  hermes-agent (upstream/main)                           │
│           ↓                                            │
│  fork/main (sync with upstream)                        │
│           ↓                                            │
│  fork/dev (development base)                           │
│           ↓                                            │
│  fork/release (production ready)                      │
└─────────────────────────────────────────────────────────┘
```

### 5.1.1 Distribution Options

| Method | Command |
|--------|---------|
| Docker | Build from `fork/release` branch |
| Local | Run from local clone |

### 5.2 Component Responsibilities

| Component | Repository | Responsibility |
|-----------|------------|----------------|
| hermes-agent | upstream (NousResearch) | Base codebase |
| fork/main | AvonS/hermes-agent | Sync with upstream |
| fork/dev | AvonS/hermes-agent | Development, testing features |
| fork/release | AvonS/hermes-agent | Production-ready, deployable |
| $HERMES_HOME | local | User data (config, .env, skills) |

### 5.3 IMPORTANT ###  

At the time of installation User must create hemes home directory, preferably out thse the ~ ie /User/home/<user>

Example  :$HERMES_HOME = "~/Work/Explore/hermes"


**User config :** `$HERMES_HOME/config.yaml` (settings), `$HERMES_HOME/.env` (API keys)

**User config Fallback :** `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys)

## 5.4 Quick Start

#Create HERMES HOME and export

## add to .zhrc or equivalent
export HERMES_HOME=~/Work/hermes


```bash
# 1. Clone and checkout release
CD $HERMES_HOME
git clone https://github.com/AvonS/hermes-agent.git
cd hermes-agent
git checkout v0.1.0

# 2. Create virtual environment with uv
uv venv

# 3. Activate and install dependencies
source .venv/bin/activate
pip install -e .

# 4. Run setup
hermes setup
```

---