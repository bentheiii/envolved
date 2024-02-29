# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
from enum import EnumMeta
from importlib import import_module
from inspect import getsourcefile, getsourcelines
from traceback import print_exc
from unittest.mock import Mock

# -- Project information -----------------------------------------------------

project = "envolved"
copyright = "2020, ben avrahami"
author = "ben avrahami"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.intersphinx", "sphinx.ext.linkcode", "sphinx.ext.autosectionlabel", "furo"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pytest": ("https://docs.pytest.org/en/latest/", None),
}

python_use_unqualified_type_names = True
add_module_names = False
autosectionlabel_prefix_document = True

import ast
import os

import envolved

release = envolved.__version__ or "master"


# Resolve function for the linkcode extension.
def linkcode_resolve(domain, info):
    def is_assignment_node(node: ast.AST, var_name: str) -> bool:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    return True
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == var_name:
            return True
        return False

    def get_assignment_node(node: ast.AST, var_name: str):
        if is_assignment_node(node, var_name):
            return node
        if isinstance(node, (ast.Module, ast.If, ast.For, ast.While, ast.With)):
            for child in node.body:
                result = get_assignment_node(child, var_name)
                if result:
                    return result
        return None

    def find_var_lines(parent_source, parent_start_lineno, var_name):
        root = ast.parse("".join(parent_source))
        node = get_assignment_node(root, var_name)
        if node:
            lineno = node.lineno
            end_lineno = node.end_lineno
            return parent_source[lineno : end_lineno + 1], lineno + parent_start_lineno
        return parent_source, parent_start_lineno

    def find_source():
        if info["module"]:
            obj = import_module("envolved." + info["module"])
        else:
            obj = envolved
        parts = info["fullname"].split(".")
        for part in parts[:-1]:
            obj = getattr(obj, part)
        try:
            item = getattr(obj, parts[-1])
        except AttributeError:
            item_name = parts[-1]
        else:
            if (
                isinstance(item, (str, int, float, bool, bytes, type(None), Mock))
                or isinstance(type(item), EnumMeta)
                or type(item) in (object,)
            ):
                # the object is a variable, we search for it's declaration manually
                item_name = parts[-1]
            else:
                while hasattr(item, "fget"):  # for properties
                    item = item.fget
                while hasattr(item, "func"):  # for cached properties
                    item = item.func
                while hasattr(item, "__func__"):  # for wrappers
                    item = item.__func__
                while hasattr(item, "__wrapped__"):  # for wrappers
                    item = item.__wrapped__
                obj = item
                item_name = None

        fn = getsourcefile(obj)
        fn = os.path.relpath(fn, start=os.path.dirname(envolved.__file__))
        source, lineno = getsourcelines(obj)
        if item_name:
            source, lineno = find_var_lines(source, lineno, item_name)
        return fn, lineno, lineno + len(source) - 1

    if domain != "py":
        return None
    try:
        fn, lineno, endno = find_source()
        filename = f"envolved/{fn}#L{lineno}-L{endno}"
    except Exception as e:
        print(f"error getting link code {info}")
        print_exc()
        raise
    return "https://github.com/bentheiii/envolved/blob/%s/%s" % (release, filename)


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

html_theme_options = {
    "source_repository": "https://github.com/biocatchltd/yellowbox",
    "source_branch": "master",
    "source_directory": "docs/",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
