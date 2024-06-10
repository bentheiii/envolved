String Parsing- parsing EnvVars easily
==========================================

Envolved comes with a rich suite of parsers out of the box, to be used the the ``type`` param for
:func:`Single-Variable EnvVars <envvar.env_var>`.

Primitive parsers
-----------------

By default, any callable that accepts a string can be used as a parser, this includes many built-in types and factories
like ``int``, ``float``, ``datetime.fromisoformat``, ``json.loads``, ``re.compile``, and even ``str``.

Special parsers
---------------

Some built-in callables translate to special predefined parsers. For example, the ``bool`` type would be pretty
ineffective on its own as a parser, which is why envolved knows to treat the ``bool`` type as a special parser that
translates the string ``"True"`` and ``"False"`` to ``True`` and ``False`` respectively.

.. code-block:: python

    enable_cache_ev = env_var("ENABLE_CACHE", type=bool)

    os.environ["ENABLE_CACHE"] = "False"

    assert enable_cache_ev.get() is False

Users can disable the special meaning of some types by wrapping them in a dummy callable.

.. code-block:: python

    enable_cache_ev = env_var("ENABLE_CACHE", type=lambda x: bool(x))

    os.environ["ENABLE_CACHE"] = "False"

    assert enable_cache_ev.get() is True

All the special parsers are:

* ``bytes``: encodes the string as UTF-8
* ``bool``: translates the string ``"True"`` and ``"False"`` to ``True`` and ``False`` respectively (equivalent to
  ``BoolParser(['true'], ['false'])``, see :class:`~parsers.BoolParser`).
* ``complex``: parses the string as a complex number, treating "i" as an imaginary unit in addition to "j".
* union type ``A | None`` or ``typing.Union[A, None]`` or ``typing.Optional[A]``: Will treat the parser as though it
  only parses ``A``.
* enum type ``E``: translates each enum name to the corresponding enum member, ignoring cases (equivalent to
  ``LookupParser.case_insensitive(E)`` see :class:`~parsers.LookupParser`).
* pydantic ``BaseModel``: parses the string as JSON and validates it against the model (both pydantic v1 and v2 
  models are supported).
* pydantic ``TypeAdapter``: parses the string as JSON and validates it against the adapted type.


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
                 opener: str | typing.Pattern = '', closer: str | typing.Pattern = '', *, strip: bool = True)

    A parser to translate a delimited string to a collection of values.

    :param delimiter: The delimiter string or pattern to split the string on.
    :param inner_parser: The parser to use to parse the elements of the collection. Note this parser is treated the
     same an an EnvVar type, so :ref:`string_parsing:Special parsers` apply.
    :param output_type: The type to use to aggregate the parsed items to a collection. Defaults to list.
    :param opener: If set, specifies a string or pattern that should be at the beginning of the delimited string.
    :param closer: If set, specifies a string or pattern that should be at the end of the delimited string. Note that providing
     a pattern will slow down the parsing process.
    :param strip: Whether or not to strip whitespaces from the beginning and end of each item.

    .. code-block:: python

        countries = env_var("COUNTRIES", type=CollectionParser(",", str.lower, set))

        os.environ["COUNTRIES"] = "United States,Canada,Mexico"

        assert countries.get() == {"united states", "canada", "mexico"}

    .. classmethod:: pair_wise_delimited(pair_delimiter: str | typing.Pattern, \
                key_value_delimiter: str | typing.Pattern, \
                key_type: ParserInput[K],  \
                value_type: ParserInput[V] | collections.abc.Mapping[K, ParserInput[V]], \
                output_type: collections.abc.Callable[[collections.abc.Iterable[tuple[K,V]]], G] = ..., *, \
                key_first: bool = True, opener: str | typing.Pattern = '', \
                closer: str | typing.Pattern = '', strip: bool = True, strip_keys: bool = True, strip_values: bool = True) -> CollectionParser[G]

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
        :param strip: Acts the same as in the :class:`constructor <CollectionParser>`.
        :param strip_keys: Whether or not to strip whitespaces from the beginning and end of each key in every pair.
        :param strip_values: Whether or not to strip whitespaces from the beginning and end of each value in every pair.

        .. code-block:: python
            :caption: Using CollectionParser.pair_wise_delimited to parse arbitrary HTTP headers.

            headers_ev = env_var("HTTP_HEADERS",
                                 type=CollectionParser.pair_wise_delimited(";", ":", str.upper,
                                                                           str))

            os.environ["HTTP_HEADERS"] = "Foo:bar;baz:qux"

            assert headers_ev.get() == {"FOO": "bar", "BAZ": "qux"}

        .. code-block:: python
            :caption: Using CollectionParser.pair_wise_delimited to parse a key-value collection with differing value
                      types.

            server_params_ev = env_var("SERVER_PARAMS",
                                        type=CollectionParser.pair_wise_delimited(";", ":", str, {
                                                                                  'host': str,
                                                                                  'port': int,
                                                                                  'is_ssl': bool,}))

            os.environ["SERVER_PARAMS"] = "host:localhost;port:8080;is_ssl:false"

            assert server_params_ev.get() == {"host": "localhost", "port": 8080, "is_ssl": False}

.. class:: FindIterCollectionParser(element_pattern: typing.Pattern, element_func: collections.abc.Callable[[re.Match], E], \
                    output_type: collections.abc.Callable[[collections.abc.Iterator[E]], G] = list, \
                    opener: str | typing.Pattern = '', closer: str | typing.Pattern = '')

    A parser to translate a string to a collection of values by splitting the string to continguous elements that match
    a regex pattern. This parser is useful for parsing strings that have a repeating, complex structure, or in cases where
    a :class:`naive split <CollectionParser>` would split the string incorrectly.

    :param element_pattern: A regex pattern to find the elements in the string.
    :param element_func: A function that takes a regex match object and returns an element.
    :param output_type: The type to use to aggregate the parsed items to a collection. Defaults to list.
    :param opener: If set, specifies a string or pattern that should be at the beginning of the string.
    :param closer: If set, specifies a string or pattern that should be at the end of the string. Note that providing
     a pattern will slow down the parsing process.

    .. code-block:: python
        :caption: Using FindIterCollectionParser to parse a string of comma-separated groups of numbers.

        def parse_group(match: re.Match) -> set[int]:
            return {int(x) for x in match.group(1).split(',')}

        groups_ev = env_var("GROUPS", type=FindIterCollectionParser(
            re.compile(r"{([,\d]+)}(,|$)"),
            parse_group
        ))

        os.environ["GROUPS"] = "{1,2,3},{4,5,6},{7,8,9}"

        assert groups_ev.get() == [{1, 2, 3}, {4, 5, 6}, {7, 8, 9}]


.. class:: MatchParser(cases: collections.abc.Iterable[tuple[typing.Pattern[str] | str, T]] | \
            collections.abc.Mapping[str, T] | type[enum.Enum], fallback: T = ...)

    A parser that checks a string against a se of cases, returning the value of first case that matches.

    :param cases: An iterable of match-value pairs. The match can be a string or a regex pattern (which will need to
                  fully match the string). The case list can also be a mapping of strings to values, or an enum type, in
                  which case the names of the enum members will be used as the matches.
    :param fallback: The value to return if no case matches. If not specified, an exception will be raised.

    .. code-block:: python

        class Color(enum.Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        color_ev = env_var("COLOR", type=MatchParser(Color))

        os.environ["COLOR"] = "RED"

        assert color_ev.get() == Color.RED

    .. classmethod:: case_insensitive(cases: collections.abc.Iterable[tuple[str, T]] | \
                      collections.abc.Mapping[str, T] | type[enum.Enum], fallback: T = ...) -> MatchParser[T]

        Create a :class:`MatchParser` where the matches are case insensitive. If two cases are equivalent under
        case-insensitivity, an error will be raised.

        :param cases: Acts the same as in the :class:`constructor <MatchParser>`. Regex patterns are not supported.
        :param fallback: Acts the same as in the :class:`constructor <MatchParser>`.

.. class:: LookupParser(lookup: collection.abc.Iterable[tuple[str, T]] | \
            collections.abc.Mapping[str, T] | type[enum.Enum], fallback: T = ...)

    A parser that checks a string against a set of cases, returning the value of the matching case. This is a more efficient
    version of :class:`MatchParser` that uses a dictionary to store the cases.

    :param lookup: An iterable of match-value pairs, a mapping of strings to values, or an enum type,
                   in which case the names of the enum members will be used as the matches.
    :param fallback: The value to return if no case matches. If not specified, an exception will be raised.

    .. code-block:: python

        class Color(enum.Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        color_ev = env_var("COLOR", type=LookupParser(Color))

        os.environ["COLOR"] = "RED"

        assert color_ev.get() == Color.RED

    .. classmethod:: case_insensitive(lookup: collection.abc.Iterable[tuple[str, T]] | \
                      collections.abc.Mapping[str, T] | type[enum.Enum], fallback: T = ...) -> LookupParser[T]

        Create a :class:`LookupParser` where the matches are case insensitive. If two cases are equivalent under
        case-insensitivity, an error will be raised.

        :param lookup: Acts the same as in the :class:`constructor <LookupParser>`.
        :param fallback: Acts the same as in the :class:`constructor <LookupParser>`.