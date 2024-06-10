# envolved Changelog
## 1.6.0
### Added
* added `AbsoluteName` to create env vars with names that never have a prefix
### Documentation
* fixed code snippets around documentation
## 1.5.0
### Removed
* `envolved` no longer supports python 3.7
### Added
* `FindIterCollectionParser`
* `with_prefix` can now override many of an env-var's parameters
### Fixed
* `CollectionParser`'s `opener` and `closer` arguments now correctly handle matches that would be split by the delimiter
* `CollectionParser`'s `closer` argument now correctly handles overlapping matches
* `CollectionParser`'s `closer` argument is now faster when using non-regex matches
* `CollectionParser.pair_wise_delimited` will now be more memory efficient when using a mapping `value_type`
### Internal
* fixed some documentation typos
## 1.4.0
### Deprecated
* this is the last release to support python 3.7
### Changed
* `BoolParser` is now a subclass of `LookupParser`
### Fixed
* environment sys-hooks can now handle invalid arguments gracefully
### Internal
* update formatter to ruff 0.3.0
* unittests now automatically run on all supported platforms
* using sluth for documentation
## 1.3.0
### Added
* single-environment variable can now be given additional arguments, that are passed to the parser.
* env-var defaults can now be wrapped in a `Factory` to allow for a default Factory.
### Changed
* type annotation correctness is no longer supported for python 3.7
### Documentation
* Fixed some typos in the documentation
## 1.2.1
### Fixed
* The children of envvars that are excluded from the description are now also excluded.
## 1.2.0
### Added
* new argument `strip_items` for `CollectionParser`.
* new arguments `strip_keys` and `strip_values` for `CollectionParser.pairwise_delimited`.
* `missing`, `as_default`, `no_patch`, and `discard` consts are now available in the `envolved` namespace.
* envvar descriptions can now also be a sequence of strings to denote multiple paragraphs.
* many new options for describing env vars
* inferred env vars can now be used for parameters that don't have a type hint, so long as the default and type are provided.
### Fixed
* the default `case_sensitive` value for `inferred_env_var`s is now `False` instead of `True`.
* envvars create with `with_prefix` are now correctly added to the description
* calling `describe_env_vars` without any envvars defined no longer raises an error
### Docs
* changed documentation theme with furo
### Deprecations
* usage of the `basevar` and `infer_env_var` modules is deprecated
* usage of the `envvar` function to create inferred envvars is deprecated
## 1.1.2
### Fixed
* changed type of `args` to be an invariant `Mapping` instead of a `dict`
## 1.1.1
### Fixed
* fixed type hint for auto-typed env vars.
## 1.1.0
### Added
* Single env vars can now accept pydantic models and type adapters, they will be parsed as jsons.
* added `py.typed` file to the package.
* added `inferred_env_var` to the root `envolved` namespace.
* schema env vars can now have keyword arguments passed to their `get` method, to add values to the schema.
* new parse: `LookupParser`, as a faster alternative to `MatchParser` (that does not support regex matches).
### Changed
* the special parser of `Enum`s is now `LookupParser` instead of `MatchParser`.
### Fixed
* `exclude_from_description` now ignores inferred env vars.
## 1.0.0
### Added
* `inferred_env_var` to explicitly infer the type, name and default value of an env var.
* `pos_args` to allow for positional arguments in a schema.
* `discard` default value for schema args, which discards an argument from the schema if the value is missing.
* `MatchParser` to return values from discrete matches. This is now the default parser for Mappings and Enums.
* `Optional`s can now be used as parsers 
* added official support for python 3.11 and 3.12
### Deprecated
* auto-typed env vars are deprecated, use `infer_env_var` instead.
### Fixed
* fixed possible race condition when reloading the environment parser, causing multiple reloads.
* significantly improved performance for case-insensitive env var repeat retrieval.
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