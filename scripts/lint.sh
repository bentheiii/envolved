#!/bin/sh
# run various linters
set -e
python -m ruff . --check
python -m ruff format . --check