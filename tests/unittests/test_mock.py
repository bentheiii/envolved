import unittest
from os import getenv
from unittest import mock

from pytest import MonkeyPatch, fixture, raises

from envolved import MissingEnvError, env_var
from envolved.basevar import missing
from envolved.describe import exclude_from_description


def test_monkeypatch_setenviron(monkeypatch):
    a = env_var("a", type=int)
    monkeypatch.setenv(a.key, "1")
    assert a.get() == 1
    assert getenv("a") == "1"


def test_monkeypatch_cleanup():
    assert getenv("a") is None


def test_monkeypatch_append(monkeypatch):
    a = env_var("a", type=int)
    monkeypatch.setenv(a.key, "1")
    assert a.get() == 1
    monkeypatch.setenv(a.key, "2", prepend="3")
    assert a.get() == 231


def test_delenviron(monkeypatch):
    a = env_var("a", type=int, default=5)
    monkeypatch.setenv(a.key, "6")
    monkeypatch.delenv(a.key)
    assert a.get() == 5


def test_delenviron_raising(monkeypatch):
    a = env_var("a", type=int, default=5)
    with raises(KeyError):
        monkeypatch.delenv(a.key)
    assert a.get() == 5


def test_delenviron_missing_ok(monkeypatch):
    a = env_var("a", type=int, default=5)
    monkeypatch.delenv(a.key, raising=False)
    assert a.get() == 5


_a = env_var("a", type=int, default=5)
exclude_from_description(_a)


def test_setenv(monkeypatch):
    monkeypatch.setattr(_a, "monkeypatch", 6.25)
    assert _a.get() == 6.25


def test_monkeypatch_setenv_cleanup():
    assert _a.get() == 5


def test_delenv(monkeypatch):
    monkeypatch.setattr(_a, "monkeypatch", missing)
    with raises(MissingEnvError):
        _a.get()


@fixture(scope="module")
def module_level_mp():
    with MonkeyPatch.context() as mp:
        yield mp


def test_mlmp(module_level_mp):
    a = env_var("a", type=int, default=5)
    module_level_mp.setenv(a.key, "6")
    assert a.get() == 6


def follow_up_test_mlmp(module_level_mp):
    a = env_var("a", type=int, default=5)
    assert a.get() == 6


class TestUnittests(unittest.TestCase):
    @mock.patch.object(_a, "monkeypatch", 0.65)
    def test_unittest(self):
        assert _a.get() == 0.65
