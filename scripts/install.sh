# install poetry and the dev-dependencies of the project
python -m pip install poetry==1.7.1
python -m poetry update --lock
python -m poetry install