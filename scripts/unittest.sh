# run the unittests with branch coverage
poetry run python -m pytest --cov=./envolved --cov-report=xml --cov-report=term-missing tests/