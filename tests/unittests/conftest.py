from pytest import fixture

from envolved.envparser import env_parser


@fixture
def set_env(monkeypatch):
    def ret(key, value):
        monkeypatch.setenv(key, value)
        env_parser.reload()

    return ret

@fixture
def del_env(monkeypatch):
    def ret(key):
        monkeypatch.delenv(key, raising=False)
        env_parser.reload()

    return ret
