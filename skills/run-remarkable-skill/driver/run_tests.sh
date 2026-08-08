#!/bin/bash
# Runs the full quality gate for rmpull/: doctests, lint, typecheck.
# Requires ./setup.sh to have been run first (needs driver/venv).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
cd "$SCRIPT_DIR"

echo "==> doctests"
"$VENV/bin/python3" -m doctest rmpull/svg_units.py rmpull/calibration.py rmpull/archive.py -v \
  | tail -1

echo "==> ruff"
"$VENV/bin/ruff" check rmpull pull_annotated.py

echo "==> pyrefly"
"$VENV/bin/pyrefly" check --python-interpreter-path "$VENV/bin/python3" rmpull pull_annotated.py

echo "==> all checks passed"
