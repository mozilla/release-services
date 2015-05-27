Documentation
=============

The ``relengapi-docs`` package builds documentation from reStructuredText files, and must write the built HTML somewhere in this process.
By default, this is a sibling directory to the documentation source, but in a production environment that directory may not be writeable.
To customize the location, set ``DOCS_BUILD_DIR``.


