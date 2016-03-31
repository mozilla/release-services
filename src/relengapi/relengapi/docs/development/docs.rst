Documentation
=============

RelengAPI documentation is processed with `Sphinx <http://sphinx-doc.org/>`_.

Top-Level Chapters
------------------

As you can see from the documentation you're reading, the Releng API documentation is divided into a few high-level chapters, including this one, "Development".
Documentation for blueprints will follow this same pattern.

Adding a Chapter
................

To add a new chapter (which should only happen rarely!), add a new element to ``DOCS_DIRS`` in ``setup.py``.

Writing Blueprint Documentation
-------------------------------

Every project that implements a blueprint can include documentation.
This documentation should be placed in the project's ``docs``, directory, in ``docs/{chapter}/{project-name}/index.rst``.
The ``project-name`` here should correspond to the lowercase version of the name in the project's ``setup.py``.
Be *very* careful not to add files in any intermediate directories, as those will override files in the base Releng API project.

The ``index.rst`` file can contain a ``toctree`` pointing to other files, or just the desired content.

For example, usage documentation for a "bumper" project would be in ``docs/usage/relengapi-bumper/index.rst``.

See :ref:`api-documentation` for information on documenting REST API endpoints and types.

Building Documentation
----------------------

Before it can be seen, documentation must be "built".
If your project is installed in a virtualenv with ``setup.py develop`` or the equivalent ``pip install -e``, then you must use the ``--develop`` (``-d``) argument to ``relengapi build-docs``.
This option re-copies the documentation from the source tree to the location where Sphinx expects to find it (under ``sys.prefix``).
