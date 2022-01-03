from assert_typecheck import DMyPyRunner
from pytest import fixture


@fixture()
def mypy_runner():
    with DMyPyRunner() as runner:
        yield runner
