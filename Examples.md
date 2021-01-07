# Envolved: usage examples

All these examples should work as-is

## 1- simple env vars

```python
from os import environ
from envolved import EnvVar

a = EnvVar('a', type=int)
environ['a'] = '15'
assert a.get() == 15
```

## 2- having a default value

```python
from os import environ
from envolved import EnvVar

a = EnvVar('a', type=int, default=0)
b = EnvVar('b', type=int, default=0)
environ['a'] = '15'
assert a.get() == 15
assert b.get() == 0

# defaults don't need to conform to the type
c = EnvVar('c', type=int, default=1.5)
assert c.get() == 1.5
```

## 3- case-sensitive env vars

```python
from os import environ
from envolved import EnvVar

# all EnvVars are case-insensitive by default
a = EnvVar('a', type=int)
environ['A'] = '15'
assert a.get() == 15

# we can make an env_var case-sensitive like so
b = EnvVar('b', type=int, case_sensitive=True, default='missing')
environ['B'] = '12'
assert b.get() == 'missing'
```

## 4- factories instead of types

```python
from os import environ
from re import compile
from envolved import EnvVar

a = EnvVar('a', type=compile)

environ['a'] = 'a+'
assert a.get() == compile('a+')
```

## 5- validation

```python
from os import environ
from envolved import EnvVar

a = EnvVar('a', type=int)


@a.validator
def ms_to_seconds(v):
    return v / 1000


environ['a'] = '1500'

assert a.get() == 1.5

# you can also use ensurers to ease some validations

b = EnvVar('b', type=int)


@b.ensurer
def not_odd(v):
    if v % 2 == 1:
        raise ValueError


environ['b'] = '12'

assert b.get() == 12

# defaults are unaffected by validators and ensurers
c = EnvVar('c', type=str, default='null')


@c.ensurer
def has_odd_len(v):
    if len(v) % 2 == 0:
        raise ValueError


assert c.get() == 'null'
```

## 6- EnvVars as Templates

```python
from os import environ
from envolved import EnvVar

# you can use one envvar as a template to create other envvars

conn_string = EnvVar('connection_string', type=str)

a_connection_string = conn_string.child('a_')
b_connection_string = conn_string.child('b_', default=None)

environ.update(
    a_connection_string='conn_str_1',
    b_connection_string='conn_str_2',
)

assert a_connection_string.get() == 'conn_str_1'
assert b_connection_string.get() == 'conn_str_2'

# Warning, once an envvar's value has been queried, it cannot be used as a template.
```

## 7- parsing bools

```python
from os import environ
from envolved import EnvVar
from envolved.parsers import BoolParser

# envolved can handle bools naturally
a = EnvVar('a', type=bool)

environ['a'] = 'true'

assert a.get() is True

# to handle strings differently, we need to create our own parsers
b = EnvVar('b', type=BoolParser(maps_to_true='yes', default=False))
# b will now interpret "yes" as true and any other value as false
environ['b'] = 'negatory'
assert b.get() is False
```

## 8- parsing lists

```python
from os import environ
from envolved import EnvVar
from envolved.parsers import CollectionParser

# we can use envolved to parse a delimited list
parser = CollectionParser(delimiter=';', inner_parser=int)
a = EnvVar('a', type=parser)
environ['a'] = '1;2;3'
assert a.get() == [1, 2, 3]
```

## 9- parsing dicts

```python
from os import environ
from envolved import EnvVar
from envolved.parsers import CollectionParser

# we can use envolved to parse a delimited list
parser = CollectionParser.pair_wise_delimited(
    pair_delimiter=';', key_value_delimiter=':',
    key_type=int, value_type=str)
a = EnvVar('a', type=parser)
environ['a'] = '1:one;2:two'
assert a.get() == {1: 'one', 2: 'two'}
```

## 9- parsing dicts with a different value for each key

```python
from os import environ
from envolved import EnvVar
from envolved.parsers import CollectionParser

# we can use envolved to parse a delimited list
value_types = {
    'host': str,
    'port': int
}
parser = CollectionParser.pair_wise_delimited(
    pair_delimiter='=', key_value_delimiter=';',
    key_type=int, value_type=value_types)
a = EnvVar('a', type=parser)
environ['a'] = 'port=12;host=local'
assert a.get() == {'host': 'local', 'port': 12}
```

## 10- parsing JSON

```python
from os import environ
from envolved import EnvVar
from envolved.parsers import JsonParser

# json parsers load the string as a json and ensure it is of the type specified
parser = JsonParser(float)

a = EnvVar('a', type=parser)

environ['a'] = '365.24'

assert a.get() == 365.24
```

## 11- parsing more complex JSON

```python
from os import environ
from typing import Dict, List, Optional, TypedDict
from envolved import EnvVar
from envolved.parsers import JsonParser

parser = JsonParser(Dict[str, List[Optional[float]]])

a = EnvVar('a', type=parser)

environ['a'] = '{"one":[1, null], "two":[2,4.5,8]}'

assert a.get() == {'one': [1, None], 'two': [2, 4.5, 8]}


# you can also used typed dicts (python 3.8 or higher)
class TD(TypedDict):
    one: object
    two: bool


parser = JsonParser(TD)
b = EnvVar('b', type=parser)
environ[b] = '{"one": [], "two": true}'

assert b.get() == {'one': [], 'two': True}


# you can even use function signatures (useful to signify that some fields are optional)
def foo(x: int, y: str, z: List[bool] = None): pass


parser = JsonParser(foo)
c = EnvVar('c', type=parser)
environ[c] = '{"x":15, "y":"hi"}'
assert c.get() == {'x': 15, 'y': 'hi'}
```

## 12- Schemas

```python
from os import environ
from envolved import EnvVar, Schema


# schemas are an easy way to group multiple variables together
class S(Schema):
    a = EnvVar(type=int)
    # type annotating a schema var is equivalent to setting its type parameter
    b: str = EnvVar()


# Warning: S is not a real class, calling it will fail!


s = EnvVar('s_', type=S)  # for schema variables the name is only its prefix
environ.update({
    's_a': '15',
    's_b': 'hi'
})

instance = s.get()

assert instance.a == 15
assert instance.b == 'hi'
```

## 13- Schemas with factories

```python
from os import environ
from typing import NamedTuple
from envolved import EnvVar, Schema


class Config(NamedTuple):
    a: int
    b: str


# you can use an existing class/factory as the type of a schema
# doing this will have two results:
# 1. The class/factory will be called with the arguments as its keyword arguments
# 2. the class/factory's type hinting will be used if the schema does not provide a type
class S(Schema, type=Config):
    a = EnvVar()  # no need to specify the type now, we get it from the type
    b = EnvVar(type=float, default='foo')  # though we can still override it if we want


s = EnvVar('s_', type=S)
environ.update({
    's_a': '15'
})

assert s.get() == Config(15, 'foo')
```

## 14-inline schemas

```python
from typing import NamedTuple
from envolved import EnvVar, Schema

# Schemas can be inlined instead of having a class declared for them

class Config(NamedTuple):
    a: int
    b: str

class S(Schema, type=Config):
    a = EnvVar()
    b = EnvVar(type=float, default='foo') 

# is equivelant to 

S = Schema(Config,
        a = EnvVar(),
        b = EnvVar(type=float, default='foo') 
        )
```