---
name: activate-venv
description: Activate the Python virtual environment before running Python commands in the terminal. Use when executing Python scripts, pip install, or any Python-related shell commands.
---

# Virtual Environment Activation

Always activate the virtual environment before running Python commands.

## Quick Reference

Prefix Python commands with venv activation:

```bash
source .venv/bin/activate && python script.py
source .venv/bin/activate && pip install package
source .venv/bin/activate && python -m pytest
```

Or use the helper script:

```bash
.cursor/skills/activate-venv/scripts/venv-run.sh python script.py
.cursor/skills/activate-venv/scripts/venv-run.sh pip install -r requirements.txt
```

## Setup

If the venv doesn't exist, create it first:

```bash
python3 -m venv .venv
source .venv/bin/activate && pip install -r requirements.txt
```

## Notes

- The venv is located at `.venv/` in the project root
- Shell sessions don't persist, so activate in each command chain
- Alternative: use `.venv/bin/python` directly without activation
