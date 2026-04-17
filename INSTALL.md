# Installation Guide

This guide covers installing Hermes Agent from source (after cloning the repository). For the quick one-line installer, see [README.md](README.md).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Clone and Setup](#clone-and-setup)
- [Install with Optional Extras](#install-with-optional-extras)
  - [Core Only (Minimal)](#core-only-minimal)
  - [Messaging Platforms](#messaging-platforms)
  - [All Features](#all-features)
- [Adding Additional Packages After Install](#adding-additional-packages-after-install)
- [Verify Installation](#verify-installation)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.11 or higher
- `uv` (recommended) or `pip`
- Git

Install `uv` (fast Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Clone and Setup

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
uv venv venv --python 3.11
source venv/bin/activate
```

---

## Install with Optional Extras

Hermes uses Python's "optional extras" system. The base install provides core functionality; extras add specific features.

### Core Only (Minimal)

Basic CLI without messaging platforms, voice, or advanced terminal backends:

```bash
uv pip install -e .
```

**Includes**: OpenAI/Anthropic clients, web tools, file tools, basic terminal, skills system.

### Messaging Platforms

**Required for Telegram, Discord, Slack, WhatsApp gateway:**

```bash
uv pip install -e ".[messaging]"
```

**What's included**:
- `python-telegram-bot` — Telegram bot support
- `discord.py` — Discord bot support
- `slack-bolt`, `slack-sdk` — Slack integration
- `aiohttp` — Async HTTP for webhooks
- `qrcode` — QR code generation for WhatsApp pairing

### All Features

Install everything except platform-specific exclusions:

```bash
uv pip install -e ".[all]"
```

**Note**: This excludes `voice` extra on macOS (due to wheel-only dependencies incompatible with Homebrew builds). Install voice separately if needed.

---

## Adding Additional Packages After Install

If you installed a minimal set and later need more features, you can add extras without reinstalling everything.

### Add Messaging Support (for Telegram/Discord/Slack)

```bash
# If you previously only installed core
uv pip install -e ".[messaging]"
```

**Verify Telegram works**:
```bash
hermes gateway status
# Should show: telegram: connected
```

### Add Voice Support (Speech-to-Text)

```bash
uv pip install -e ".[voice]"
```

**Note**: Voice support requires `faster-whisper` which has compiled dependencies. If you get wheel build errors on macOS, voice features may not be available.

### Add Cron Scheduling

```bash
uv pip install -e ".[cron]"
```

### Add Cloud Terminal Backends

```bash
# Modal serverless
uv pip install -e ".[modal]"

# Daytona development environments
uv pip install -e ".[daytona]"
```

### Add Multiple Extras

```bash
# Example: messaging + cron + voice
uv pip install -e ".[messaging,cron,voice]"

# For development work
uv pip install -e ".[messaging,cron,dev]"
```

### List Available Extras

See all available extras in `pyproject.toml` under `[project.optional-dependencies]`:

```bash
grep -A 1 "^\[project.optional-dependencies\]" pyproject.toml
```

Common extras:
| Extra | Features |
|-------|----------|
| `messaging` | Telegram, Discord, Slack, WhatsApp |
| `cron` | Scheduled task automation |
| `voice` | Speech-to-text transcription |
| `modal` | Modal.com serverless backend |
| `daytona` | Daytona dev environment backend |
| `dev` | pytest, debug tools |
| `matrix` | Matrix chat protocol (Linux only) |
| `homeassistant` | Home Assistant integration |
| `mcp` | MCP (Model Context Protocol) servers |
| `termux` | Android/Termux curated set |

---

## Verify Installation

```bash
# Check CLI works
hermes --version

# Run diagnostics
hermes doctor

# Test Telegram (if configured)
hermes gateway status
```

---

## Troubleshooting

### "No adapter available for telegram"

**Cause**: `python-telegram-bot` not installed (missing `[messaging]` extra)

**Fix**:
```bash
uv pip install -e ".[messaging]"
hermes gateway restart
```

### "HTTPXRequest.__init__() got an unexpected keyword argument 'httpx_kwargs'"

**Cause**: Version mismatch between `python-telegram-bot` and Hermes code

**Fix**: Install the `[messaging]` extra which pins the correct version:
```bash
uv pip install -e ".[messaging]"
```

Or if using a fork/older version, disable fallback IPs:
```bash
export HERMES_TELEGRAM_DISABLE_FALLBACK_IPS=true
```

### "Module not found" when running tools

**Cause**: Missing optional extra for that toolset

**Fix**: Check `pyproject.toml` for the relevant extra and install it:
```bash
uv pip install -e ".[EXTRA_NAME]"
```

---

## Next Steps

After installation:

```bash
# Configure your LLM provider
hermes model

# Set up Telegram/Discord/etc (if you installed [messaging])
hermes gateway setup

# Start chatting
hermes
```

See [full documentation](https://hermes-agent.nousresearch.com/docs/) for more.
