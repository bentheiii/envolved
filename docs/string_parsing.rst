String Parsing- parsing EnvVars easily
==========================================

Envolved comes with a rich suite of parsers out of the box, to be used the the ``type`` param for
:func:`Single -Variable EnvVars <envvar.env_var>`.

Primitive parsers
-----------------

By default, any callable that accepts a string can be used as a parser, this includes many built-in types and factories
like ``int``, ``float``, ``datetime.fromisoformat``, ``json.loads``, ``re.compile``, and even ``str``.

Special parsers
---------------

Some built-in callables translate to special predefined parsers. For example, the ``bool`` type would be pretty
ineffective on its own as a parser, which is why envolved knows to treat the ``bool`` type as a special parser that
translates the string ``"True"`` and ``"False"`` to ``True`` and ``False`` respectively.

.. code-block::

    enable_cache_ev = env_var("ENABLE_CACHE", type=bool)

    os.environ["ENABLE_CACHE"] = "False"

    assert enable_cache_ev.get() == False

Users can disable the special meaning of some types by wrapping them in a dummy callable.

.. code-block::

    enable_cache_ev = env_var("ENABLE_CACHE", type=lambda x: bool(x))

    os.environ["ENABLE_CACHE"] = "False"

    assert enable_cache_ev.get() == True

All the special parsers are:

* ``bytes``: encodes the string as UTF-8
* ``bool``: translates the string ``"True"`` and ``"False"`` to ``True`` and ``False`` respectively (equivalent to
    ``BoolParser(['true'], ['false'])``, see :class:`BoolParser`).
* ``complex``: parses the string as a complex number, treating "i" as an imaginary unit in addition to "j".

Utility Parsers
---------------
.. module:: parsers

.. class:: BoolParser(maps_to_true: collections.abc.Iterable[str] = (), \
                      maps_to_false: collections.abc.Iterable[str] = (), *, default: bool | None = None, \
                      case_sensitive: bool = False)

    A parser to translate strings to ``True`` or ``False``.

    :param maps_to_true: A list of strings that translate to ``True``.
    :param maps_to_false: A list of strings that translate to ``False``.
    :param default: The default value to return if the string is not mapped to either value. Set to ``None`` to raise an
        exception.
    :param case_sensitive: Whether the strings to match are case sensitive.

.. class:: CollectionParser(delimiter: str | typing.Pattern, inner_parser: ParserInput[E], \
                 output_type: collections.abc.Callable[[collections.abc.Iterator[E]], G] = list, \
                 opener: str | typing.Pattern = '', closer: str | typing.Pattern = '')

    A parser to translate a delimited string to a collection of values.

    :param delimiter: The delimiter string or pattern to split the string on.
    :param inner_parser: The parser to use to parse the elements of the collection. Note this parser is treated the
     same an an EnvVar type, so :ref:`string_parsing:Special parsers` apply.
    :param output_type: The type to use to aggregate the parsed items to a collection defaults to list.
    :param opener: If set, specifies a string or pattern that should be at the beginning of the delimited string.
    :param closer: If set, specifies a string or pattern that should be at the end of the delimited string.

    .. code-block::

        countries = env_var("COUNTRIES", type=CollectionParser(",", str.to_lower, set))

        os.environ["COUNTRIES"] = "United States,Canada,Mexico"

        assert countries.get() == {"united states", "canada", "mexico"}

    .. classmethod:: pair_wise_delimited(pair_delimiter: str | typing.Pattern, \
                key_value_delimiter: str | typing.Pattern, \
                key_type: ParserInput[K],  \
                value_type: ParserInput[V] | collections.abc.Mapping[K, ParserInput[V]], \
                output_type: collections.abc.Callable[[collections.abc.Iterable[tuple[K,V]]], G] = ..., *, \
                key_first: bool = True, opener: str | typing.Pattern = '', \
                closer: str | typing.Pattern = '') -> CollectionParser

        A factory method to create a :class:`CollectionParser` where each item is a delimited key-value pair.

        :param pair_delimiter: The delimiter string or pattern between any two key-value pairs.
        :param key_value_delimiter: The delimiter string or pattern between the key and the value.
        :param key_type: The parser to use to parse the keys. Note this parser is treated the same an an EnvVar type,
            so :ref:`string_parsing:Special parsers` apply.
        :param value_type: The parser to use to parse the values. Note this parser is treated the same an an EnvVar
            type, so :ref:`string_parsing:Special parsers` apply. This can also be a mapping from keys to parsers, to
            specify different parsers for different keys.
        :param output_type: The type to use to aggregate the parsed key-value pairs to a collection. Defaults to a
            ``dict`` that raises an exception if a key appears more than once.
        :param key_first: If set to ``True`` (the default), the first element in each key-value pair will be interpreted
            as the key. If set to ``False``, the second element in each key-value pair will be interpreted as the key.
        :param opener: Acts the same as in the :class:`constructor <CollectionParser>`.
        :param closer: Acts the same as in the :class:`constructor <CollectionParser>`.

        .. code-block::
            :caption: Using CollectionParser.pair_wise_delimited to parse arbitrary HTTP headers.

            headers_ev = env_var("HTTP_HEADERS",
                                 type=CollectionParser.pair_wise_delimited(";", ":", str.to_upper,
                                                                           str))

            os.environ["HTTP_HEADERS"] = "Foo:bar;baz:qux"

            assert headers_ev.get() == {"FOO": "bar", "BAZ": "qux"}

        .. code-block::
            :caption: Using CollectionParser.pair_wise_delimited to parse a key-value collection with differing value
                      types.

            server_params_ev = env_var("SERVER_PARAMS",
                                        type=CollectionParser.pair_wise_delimited(";", ":", str, {
                                                                                  'host': str,
                                                                                  'port': int,
                                                                                  'is_ssl': bool,}))

            os.environ["SERVER_PARAMS"] = "host:localhost;port:8080;is_ssl:false"

            assert server_params_ev.get() == {"host": "localhost", "port": 8080, "is_ssl": False}