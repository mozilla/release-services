Contributing to RelengAPI
=========================

RelengAPI is developed on GitHub.
To contribute, create a pull request for a topic branch, in the normal GitHub style.
Every pull request is tested by Travis-CI.
Patches that do not pass will not be merged.

Patch Review Checklist
----------------------

Reviewers should use this checklist to verify that all of the required pieces for a patch are present.
It is in GitHub-flavored Markdown format for ease of copy-pasting.

.. code-block:: none

    * documentation updated
      * [ ] under `relengapi/docs/usage` if the change is visible to RelengAPI users
      * [ ] in docstrings and REST API field comments for API changes
      * [ ] under `relengapi/docs/deployment` if the change is visible to RelengAPI operators (e.g., config changes)
      * [ ] under `relengapi/docs/development` if the change is visible to RelengAPI developers (e.g., additions to `relengapi.lib`)
    * test coverage
      * [ ] all new code is 100% covered by tests
      * [ ] new REST API methods have all interesting combinations of input tested, including error conditions
      * [ ] tests do not require any external resources (use mocks instead)
      * [ ] tests do not depend on time (`time.sleep`, etc.)
    * style (much of this is verified by `validate.sh`
      * [ ] pep8, pyflakes-compliant
      * [ ] one import per line, sorted lexically
      * [ ] all files have an MPL license header
    * code quality
      * [ ] configuration is read from the configuration file, not embedded in source files
      * [ ] generic functionality is implemented in `relengapi.lib`
      * [ ] no code outside of a blueprint explicitly imports code in that blueprint
