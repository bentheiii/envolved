# run the unittests with branch coverage
set -e
coverage run --branch --include="envolved/*" -m pytest tests/
coverage html
coverage report -m
coverage xml
python3 -m mypy --show-error-codes tests/unittests/