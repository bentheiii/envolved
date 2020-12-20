This is a template project for a github project including:
 * workflows for testing, linting and publishing
 * sphinx documentation
 * poetry project file
 * benchmarking support
 
 After creating a project from this template:
 * Call `scripts/fill_template.py` to replace all the placeholder values. Alternatively, replace all occurrences of `<$...$>` (regex: `<\$[^\$]*\$>`) with their appropriate values for your project.
 * Add the following secrets to yor github repository:
    * `pypi_user`: your username on pypi.
    * `pypi_password`: your password on pypi.