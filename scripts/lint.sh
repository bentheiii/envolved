#!/bin/sh
# run various linters
set -e
echo "running isort..."
python -m isort . -c
echo "running flake8..."
poetry run flake8 --max-line-length 120 envolved tests
echo "running mypy..."
python3 -m mypy --show-error-codes envolved