#!/bin/sh
# run various linters
set -e
python -m ruff format .
python -m ruff . --select I,F401 --fix --show-fixes
