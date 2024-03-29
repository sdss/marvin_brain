Marvin's Brain Change Log
=========================

[0.3.0] - 2022/07/27
--------------------
- Drop support for Python 2, Python < 3.8
- Minimum requirements now requires Python > 3.8
- Adds tests to testing suite

[0.2.2] - 2021/11/22
--------------------
- Fixed a bug in the API response when the response is not a dictionary
- Adding new github actions for build, test, and release on tag

[0.2.1] - 2021/11/19
--------------------
- Pinning versions of all dependencies

[0.2.0] - 2020/09/20
--------------------
- refactoring for code health
- added setup.py and cfg
- moved to sdsstools for logging and config
- moved tests to top level

[0.1.4] - 2020/08/31
--------------------
- Syntax change to accommodate networkx 2.4.x deprecations

[0.1.3] - 2020/08/05
--------------------
- Added `magrathea.sdss.org` mirror option

[0.1.2] - 2019/12/11
--------------------

Changed
^^^^^^^
- Setting ``verify`` default back to True
- Changed JHU db check to look for SCISERVER environment variable
- Added new get_yaml_loader function to get proper yaml Loader for 3.1/5.1 spec
- Used new yaml Loader to accommodate 5.1 spec

[0.1.1] - 2018/12/10
--------------------

Changed
^^^^^^^
- Added a ``verify`` keyword argument to Interaction to allow disabling of SSL certification on requests
- Setting ``verify`` to False as a hack for dr15 release day until CHPC can fix.


[0.1.0] - 2018/12/03
--------------------

Fixed
^^^^^
- Issue with Interaction class not always propagating a new authype down into BrainAuth

Changed
^^^^^^^
- Switched SDSS user authentication over to Credentails (collaboration.wiki) from the old Inspection
- Added a `use_test` custom config kwarg to switch API urls from production to test servers
- Moved functionality to collect all web routes from a Flask web app into a standalone callable function

Added
^^^^^
- CHANGELOG.rst to begin recording changes
- API token authentication using `Flask-JWT-Extended <hhttps://flask-jwt-extended.readthedocs.io/en/latest>`_
- new `BrainAuth` class to override standard requests library handling of authentication.
- Options on `Interaction` class to stream response back in iterative chunks
- Response compression options for `json` or `msgpack` compression.
- A custom brain.yml file for configuration
- Added a brain version and bumpversion config
