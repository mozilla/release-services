Documentation
=============

RelengAPI documentation is processed with `Sphinx <http://sphinx-doc.org/markup/toctree.html>`_.

Top-Level Chapters
------------------

As you can see from the documentation you're reading, the Releng API documentation is divided into a few high-level chapters, including this one, "Development".
Documentation for blueprints will follow this same pattern.

Blueprint Documentation
-----------------------

Every project that implements a blueprint can include documentation.
This documentation should be placed in ``relengapi/docs``, in subdirectories named after the appropripate top-level chapter.
The ``index.rst`` file in this directory can contain a ``toctree`` pointing to other files, or just the desired content.

For example, a usage documentation for a blueprint might be in ``relengapi/docs/usage/index.rst``.
