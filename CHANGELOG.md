# envolved Changelog
## 1.0.0
### Added
* `inferred_env_var` to explicitly infer the type, name and default value of an env var.
* `pos_args` to allow for positional arguments in a schema.
* `discard` default value for schema args, which discards an argument from the schema if the value is missing.
* `MatchParser` to return values from discrete matches. This is now the default parser for Mappings and Enums.
* `Optional`s can now be used as parsers 
* added official support for python 3.11 and 3.12
### Deprecated
* auto-typed env vars are deprecate, use `infer_env_var` instead.
### Internal
* use ruff + black for formatting
## 0.5.0
This release is a complete overhaul of the project. Refer to the documentation for details.
## 0.4.1
### Fixed
* Partial Schema error is no longer triggered from default members
## 0.4.0
### Changed
* Env Vars no longer default to case sensitive if not uppercase.
### Added
* Env vars can now be supplied with `prefix_capture`, causing them to become a prefix env var.
* all env vars can now be supplied with the optional `description` keyword argument.
* `describe_env_vars` to make a best-effort attempt to describe all the environment variables defined.
* `raise_for_partial` parameter for schema vars, to not accept partially filled schemas, regardless of default value.
## 0.3.0
### Removed
* The caching mechanism from basic vars has been removed
## 0.2.0
### Removed
* `env_parser.reload`- the parser is now self-updating!
* `MappingEnvVar`- use `Schema(dict, ...)` instead
* The same envvar cannot be used twice in the same schema anymore
### Added
* The environment parsing is now self-updating, no more need to manually reload the environment when testing.
* When manifesting `EnvVar`s, additional keyword arguments can be provided.
* When creating a schema, you can now omit the factory type to just use a `SimpleNamespace`.
* Validators can now be used inside a schema class.
* Validators can now be static methods.
* EnvVar children can now overwrite template parameters.
* EnvVar template can be without a name.
* `BoolParser`'s parameters now all have default values.
### Fixed
* Inner variables without a default value would act as though given a default value.
* If the variadic annotation of `__new__` and `__init__` would disagree, we would have `__new__`'s win out, this has been corrected.
* `EnvVar` is now safe to use both as a parent and as a manifest
* EnvVar validators now correctly transition to children
### Internal
* added examples page
## 0.1.1
### Fixed
* removed recordclasses dependency
## 0.1.0
* initial release