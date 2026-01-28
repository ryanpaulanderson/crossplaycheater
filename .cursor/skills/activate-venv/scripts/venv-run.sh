#!/bin/bash
# Run a command inside the project's virtual environment
# Usage: venv-run.sh <command> [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH" >&2
    echo "Create it with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
fi

source "$VENV_PATH/bin/activate"
exec "$@"
