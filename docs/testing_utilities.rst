Testing Utilities
=====================

Envolved makes testing environment variables easy with the :attr:`~basevar.EnvVar.monkeypatch` attribute and
:meth:`~basevar.EnvVar.patch` context method. They allows you to set a predefined EnvVar value and then restore the
original value when the test is finished.

.. code-block::
    :emphasize-lines: 5-6

    cache_time_ev = env_var('CACHE_TIME', type=10)

    class TestAppStartup(unittest.TestCase):
        def test_startup(self):
            with cache_time_ev.patch(10):
                # now within this context, cache_time_ev.get() will return 10
                my_app.startup()
            self.assertEqual(my_app.cache_time, 10)

note that `cache_time_ev.patch(10)` just sets attribute `cache_time_ev.monkeypatch` to ``10``, and restores it to its
previous value when the context is exited. We might as well have done:

.. code-block::
    :emphasize-lines: 5-6, 9

    cache_time_ev = env_var('CACHE_TIME', type=10)

    class TestAppStartup(unittest.TestCase):
        def test_startup(self):
            previous_cache_patch = cache_time_ev.monkeypatch
            cache_time_ev.monkeypatch = 10
            # now within this context, cache_time_ev.get() will return 10
            my_app.startup()
            cache_time_ev.monkeypatch = previous_cache_patch
            self.assertEqual(my_app.cache_time, 10)

Unittest
-------------

In :mod:`unittest` tests, we can use the :any:`unittest.mock.patch.object` method decorate a test method to the values we
want to test with.

.. code-block::
    :emphasize-lines: 4, 6

    cache_time_ev = env_var('CACHE_TIME', type=10)

    class TestAppStartup(unittest.TestCase):
        @unittest.patch.object(cache_time_ev, 'monkeypatch', 10)
        def test_startup(self):
            # now within this method, cache_time_ev.get() will return 10
            my_app.startup()
            self.assertEqual(my_app.cache_time, 10)

Pytest
------------

When using :mod:`pytest` we can use the
`monkeypatch fixture <https://docs.pytest.org/en/latest/how-to/monkeypatch.html>`_ fixture to patch our EnvVars.

.. code-block::
    :emphasize-lines: 2

    def test_app_startup(monkeypatch):
        monkeypatch.setattr(cache_time_ev, 'monkeypatch', 10)
        # from now on within this method, cache_time_ev.get() will return 10
        my_app.startup()
        assert my_app.cache_time == 10

Using monkeypatch for different scopes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes we may want to apply a monkeypatch over a non-function-scope fixture. We will find an error in this case
because the built-in monkeypatch fixture is only available in function scope. To overcome this, we can create our own
monkeypatch fixture.

.. code-block::

    from pytest import fixture, MonkeyPatch

    @fixture(scope='session')
    def session_monkeypatch(request):
        with MonkeyPatch.context() as m:
            yield m

    @fixture(scope='session')
    def app(session_monkeypatch):
        monkeypatch.setattr(cache_time_ev, 'monkeypatch', 10)
        app = MyApp()
        return app

    def test_app_cache_time(app):
        assert app.cache_time == 10

``monkeypatch`` doesn't affect the environment
----------------------------------------------

An important thing to note is that the ``monkeypatch`` fixture doesn't affect the actual environment, only the specific
EnvVar that was patched.

.. code-block::

    cache_time_ev = env_var('CACHE_TIME', type=int)

    def test_one(monkeypatch):
        monkeypatch.setattr(cache_time_ev, 'monkeypatch', 10)
        assert os.getenv('CACHE_TIME') == '10'  # this will fail

    cache_time_2_ev = env_var('CACHE_TIME', type=int)

    def test_two(monkeypatch):
        monkeypatch.setattr(cache_time_ev, 'monkeypatch', 10)
        assert cache_time_2_ev.get() == 10  # this will fail too

In cases where an environment variable is retrieved from different EnvVars, or with libraries other than envolved, we'll
have to set the environment directly, by using the :attr:`basevar.SingleEnvVar.key` property to get the actual
environment name. In pytest we can use the monkeypatch fixture to do this.

.. code-block::

    cache_time_ev = env_var('CACHE_TIME', type=int)

    def test_one(monkeypatch):
        monkeypatch.setenv(cache_time_ev.key, '10')
        assert os.getenv('CACHE_TIME') == '10'

    cache_time_2_ev = env_var('CACHE_TIME', type=int)

    def test_two(monkeypatch):
        monkeypatch.setenv(cache_time_ev.key, '10')
        assert cache_time_2_ev.get() == 10