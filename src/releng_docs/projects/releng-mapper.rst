.. _releng-mapper-project:

Project: releng-mapper
======================

:production: https://mapper.mozilla-releng.net
:staging: https://mapper.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

When we convert hg repositories to git, and vice versa, the hg changeset SHA (the 40 character hexadecimal string that
you get when you commit a change) is different to the git commit id (the equivalent SHA used by git).

In order to keep track of which hg changeset SHAs relate to which git commit SHAs, we keep a database of the mappings,
together with details about the project the SHAs come from, and what time they were inserted into the database.

The vcs sync tool (checked into mozharness) is the tool which performs the conversion between hg repos and git repos,
and this is documented separately. It is responsible for performing the conversion - this is outside the scope of mapper.

Mapper is an HTTP API that allows:

 *  insertion of new mappings and projects (a "project" is essentially the name of the repo - e.g. build-tools) (HTTP POST)
 *  insertion of git/hg mappings for a given project (HTTP POST)
 *  retrieval of mappings for a given project (HTTP GET)

Behind the scenes, it is reading/writing from the database (using sqlalchemy).

Note: the vcs sync tool is a client of the mapper: it is vcs sync that inserts into mapper (i.e. uses the HTTP POST methods).
The other clients of mapper are:

 *  people / developers - wanting to query mappings
 *  ``b2g_build.py`` - the build script for b2g - since this needs to lookup SHAs in order to reference frozen commit versions in manifests


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
