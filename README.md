# Envolved
Envolved is a library to make environment variable parsing powerful and effortless.

documentation: https://envolved.readthedocs.io/en/latest/

```python
from envolved import env_var, EnvVar

# create an env var with an int value
foo: EnvVar[int] = env_var('FOO', type=int, default=0)
value_of_foo = foo.get()  # this method will check for the environment variable FOO, and parse it as an int

# we can also have some more complex parsers
from typing import List, Optional
from envolved.parsers import CollectionParser

foo = env_var('FOO', type=CollectionParser(',', int))
foo.get()  # now we will parse the value of FOO as a comma-separated list of ints

# we can also use schemas to combine multiple environment variables
from dataclasses import dataclass


@dataclass
# say we want the environment to describe a ConnectionSetting
class ConnectionSetting:
    host: str
    port: int
    user: Optional[str]
    password: Optional[str]


connection_settings: EnvVar[ConnectionSetting] = env_var('service_', type=ConnectionSetting, args={
    'host': env_var('hostname'),
    # we now define an env var as an argument. Its suffix will be "hostname", and its type will be inferred from the
    # type's annotation
    'port': env_var('port'),
    'user': env_var('username', type=str),  # for most types, we can infer the type from the annotation, though we can
    # also override it if we want
    'password': env_var('password', type=str, default=None)  # we can also set a default value per arg
})
service_connection_settings: ConnectionSetting = connection_settings.get()
# this will look in 4 environment variables:
# host will be extracted from service_hostname
# port will be extracted from service_port, then converted to an int
# user will be extracted from service_username
# password will be extracted from service_password, and will default to None
# finally, ConnectionSetting will be called with the parameters
```
