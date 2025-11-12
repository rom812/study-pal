#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/setup_env.sh [.venv]
# Creates a Python virtual environment (defaults to .venv) and installs requirements.

VENV_PATH="${1:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "Creating virtual environment at ${VENV_PATH}..."
"${PYTHON_BIN}" -m venv "${VENV_PATH}"

source "${VENV_PATH}/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing project requirements..."
pip install -r requirements.txt

echo "Environment ready. Activate with: source ${VENV_PATH}/bin/activate"
