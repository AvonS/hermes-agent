# Hermes Agent - Installation Guide

## Quick Start

```bash
# 1. Clone and checkout release
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

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- API keys in `~/.hermes/.env` (see `.env.example`)

## Installation

### 1. Clone the Release

```bash
git clone https://github.com/AvonS/hermes-agent.git
cd hermes-agent
git checkout v0.1.0
```

### 2. Create Virtual Environment

Using **uv** (recommended - faster):

```bash
uv venv
```

Or with pip:

```bash
python3 -m venv .venv
```

### 3. Activate & Install

```bash
# Activate the environment
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### 4. Configure

```bash
# Run interactive setup
hermes setup
```

Or manually:
```bash
cp ~/.hermes/.env.example ~/.hermes/.env
# Edit ~/.hermes/.env with your API keys
```

## Shell Alias (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Hermes Agent alias
alias hermes='cd /path/to/hermes-agent && source .venv/bin/activate && hermes'
```

Replace `/path/to/hermes-agent` with your actual path.

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

Now just type `hermes` to start!

## Running

```bash
# CLI mode
hermes

# Gateway mode (Telegram, Slack, etc.)
hermes gateway run

# Background mode
hermes gateway run --background
```

## Updating

```bash
git fetch origin
git checkout v0.1.0  # or newer release tag
pip install -e .      # reinstall if needed
```

## Troubleshooting

### "command not found: hermes"
- Ensure `.venv/bin` is in your PATH, or use the alias above
- Run `pip install -e .` again in the activated environment

### API key errors
- Check `~/.hermes/.env` contains your keys
- Required: `OPENROUTER_API_KEY` or similar

### Port already in use
- Kill existing process: `pkill -f hermes`
- Or run on different port: `hermes gateway run --port 8080`