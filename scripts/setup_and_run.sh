#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${PYTHON:-python3}"

log() {
  printf "[setup] %s\n" "$*"
}

if [[ ! -d "${VENV_PATH}" ]]; then
  log "Creating virtual environment at ${VENV_PATH}"
  "${PYTHON_BIN}" -m venv "${VENV_PATH}"
fi

source "${VENV_PATH}/bin/activate"

log "Upgrading pip"
python -m pip install --upgrade pip >/dev/null

log "Installing runtime requirements"
python -m pip install --quiet -r "${PROJECT_ROOT}/requirements.txt"

log "Installing developer tooling (ruff for linting)"
python -m pip install --quiet "ruff>=0.5"

log "Running lint checks"
ruff "${PROJECT_ROOT}"

log "Running tests"
pytest "${PROJECT_ROOT}/tests"

log "Starting application in headless mode for smoke validation"
python "${PROJECT_ROOT}/app.py" --headless --no-hotkeys --no-tray

log "Setup and validation complete"
