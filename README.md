# Envolved
Envolved is a library to make environment variable parsing powerful and effortless.

```python
from envolved import EnvVar

# create an env var with an int value
foo: EnvVar[int] = EnvVar('FOO', type=int, default=0)
value_of_foo = foo.get()  # this method will check for the environment variable FOO, and parse it as an int

# we can also have some more complex parsers
from typing import List, Optional
from envolved.parsers import JsonParser

foo = EnvVar('FOO', type=JsonParser(List[float]))
foo.get()  # now we will parse the value of FOO as a JSON list, and ensure that all its inner values are numbers

# we can also use schemas to combine multiple environment variables
from envolved import Schema
from dataclasses import dataclass


@dataclass
# say we want the environment to describe a ConnectionSetting
class ConnectionSetting:
    host: str
    port: int
    user: Optional[str]
    password: Optional[str]
    
# note that schemas work with any factory or class that annotates its constructor, dataclass is used for simplicity

class ConnectionSettingSchema(Schema, type=ConnectionSetting):
    host = EnvVar('hostname') 
    # we now define an env var inside the schema. Its suffix will be "hostname", and its type will be inferred from the
    # type's annotation
    port = EnvVar()  # if we like the parameter name as the env var suffix, we can leave the env var empty
    user: str = EnvVar('username')  # we can annotate the schema members to override the type inference
    password = EnvVar(type=str, default=None)  # we can set a default to show that the type var may be missing

connection_settings: EnvVar[ConnectionSetting] = EnvVar('service_', type=ConnectionSettingSchema)
service_connection_settings: ConnectionSetting = connection_settings.get() 
# this will look in 4 environment variables:
# host will be extracted from service_hostname
# port will be extracted from service_port, then converted to an int
# user will be extracted from service_username
# password will be extracted from service_password, and will default to None
# finally, ConnectionSetting will be called with the parameters
```
