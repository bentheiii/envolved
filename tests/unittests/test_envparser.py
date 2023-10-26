from os import name

from pytest import raises, skip

from envolved.envparser import env_parser

if name == "nt":
    skip("windows is always case-insensitive", allow_module_level=True)


def test_parse_real_time(monkeypatch):
    with raises(KeyError):
        env_parser.get(False, "a")
    monkeypatch.setenv("a", "x")
    assert env_parser.get(False, "a") == "x"


def test_exact_override(monkeypatch):
    monkeypatch.setenv("A", "0")
    assert env_parser.get(False, "a") == "0"
    monkeypatch.setenv("a", "1")
    assert env_parser.get(False, "a") == "1"
    monkeypatch.delenv("a")
    assert env_parser.get(False, "a") == "0"
