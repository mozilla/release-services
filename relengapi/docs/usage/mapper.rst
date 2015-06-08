Mapper
======

What is it?
-----------

When we convert hg repositories to git, and vice versa, the hg changeset SHA (the 40 character hexadecimal string that you get when you commit a change) is different to the git commit id (the equivalent SHA used by git).

In order to keep track of which hg changeset SHAs relate to which git commit SHAs, we keep a database of the mappings, together with details about the project the SHAs come from, and what time they were inserted into the database.

The vcs sync tool (checked into mozharness) is the tool which performs the conversion between hg repos and git repos, and this is documented separately.
It is responsible for performing the conversion - this is outside the scope of mapper.

Mapper is an HTTP API that allows:

 *  insertion of new mappings and projects (a "project" is essentially the name of the repo - e.g. build-tools) (HTTP POST)
 *  insertion of git/hg mappings for a given project (HTTP POST)
 *  retrieval of mappings for a given project (HTTP GET)

Behind the scenes, it is reading/writing from the database (using sqlalchemy).

Note: the vcs sync tool is a client of the mapper: it is vcs sync that inserts into mapper (i.e. uses the HTTP POST methods).
The other clients of mapper are:

 *  people / developers - wanting to query mappings
 *  ``b2g_build.py`` - the build script for b2g - since this needs to lookup SHAs in order to reference frozen commit versions in manifests

API
---

Maps are represented in a text format, with one mapping per line, in the format "git_commit SPACE hg_changeset"

.. api:endpoint:: mapper.get_rev
    GET /mapper/<projects>/rev/<vcs_type>/<commit>

    :param projects: Comma-delimited project names(s) string
    :param vcs: String 'hg' or 'git' to categorize the commit you are passing
            (not the type you wish to receive back)
    :param commit: Revision or partial revision string of SHA to be converted
    :respose: mapfile line

    Return the hg changeset SHA for a git commit id, or vice versa.

    Exceptions:
     *  HTTP 400: Unknown VCS or malformed SHA
     *  HTTP 404: No corresponding SHA found
     *  HTTP 500: Multiple corresponding SHAs found

    Example: https://api.pub.build.mozilla.org/mapper/build-puppet/rev/git/69d64a8a18e6e001eb015646a82bcdaba0e78a24
    Example: https://api.pub.build.mozilla.org/mapper/build-puppet/rev/hg/68f1b2b9996c4e33aa57771b3478932c9fb7e161

.. api:endpoint:: mapper.get_full_mapfile
    GET /mapper/<projects>/mapfile/full

    :param projects: Comma-delimited project names(s) string
    :response: mapfile

    Get a map file containing mappings for one or more projects.

    Exceptions:
     *  HTTP 404: No results found

    Example: https://api.pub.build.mozilla.org/mapper/build-puppet/mapfile/full

.. api:endpoint:: mapper.get_mapfile_since
    GET /<project>/mapfile/since/<since>

    :param projects: Comma-delimited project names(s) string
    :param since: Timestamp in a format parsed by [dateutil.parser.parse]
        (https://labix.org/python-dateutil) evaluated based on the time the record
        was inserted into mapper database, not the time of commit and not the time
        of conversion.
    :response: mapfile

    Get a map file since the given date.

    Exceptions:
     *  HTTP 400: Invalid date format specified
     *  HTTP 404: No results found

    Example: https://api.pub.build.mozilla.org/mapper/build-mozharness/mapfile/since/29.05.2014%2017:02:09%20CEST

.. api:endpoint:: mapper.insert_many_no_dups
    POST /<project>/insert

    :param project: Single project name string
    :body: map file
    :response: ``{}``

    Insert many git-hg mapping entries, returning an error on duplicate SHAs.

    Exceptions:
     *  HTTP 400: Request content-type is not 'text/plain'
     *  HTTP 400: Malformed SHA
     *  HTTP 404: Project not found
     *  HTTP 409: Duplicate mappings found
     *  HTTP 500: Multiple matching projects found with same name

    Example: https://api.pub.build.mozilla.org/mapper/insert

.. api:endpoint:: mapper.insert_many_ignore_dups
    POST /<project>/insert/ignoredups

    :param project: Single project name string
    :body: map file
    :response: ``{}``

    Like :api:endpoint:`mapper.insert_many_no_dups`, but duplicate entries are silently ignored.

    Exceptions:
     *  HTTP 400: Request content-type is not 'text/plain'
     *  HTTP 400: Malformed SHA
     *  HTTP 404: Project not found
     *  HTTP 500: Multiple matching projects found with same name

    Example: https://api.pub.build.mozilla.org/mapper/insert/ignoredups

.. api:endpoint:: mapper.insert_one
    POST  /<project>/insert/<git_commit>/<hg_changeset>

    :param project: Single project name string
    :param git_commit: 40 char hexadecimal string
    :param hg_changeset: 40 char hexadecimal string
    :response: a JSON representation of the inserted data

    Insert a single git-hg mapping.
    The response looks like this:

    .. code-block:: none

        {
            'date_added': <date>,
            'project_name': <project>,
            'git_commit': <git SHA>,
            'hg_changeset': <hg SHA>,
        }

    Exceptions:
     *  HTTP 400: Malformed SHA
     *  HTTP 404: Project not found in database
     *  HTTP 409: Mapping already exists for this project
     *  HTTP 500: Problem inserting new mapping into database
     *  HTTP 500: Multiple matching projects found with same name

    Example: https://api.pub.build.mozilla.org/mapper/insert/69d64a8a18e6e001eb015646a82bcdaba0e78a24/68f1b2b9996c4e33aa57771b3478932c9fb7e161

.. api:endpoint:: mapper.add_project
    POST /<project>

    :param project: Single project name string
    :response: ``{}``

    Insert a new project into the database.

    Exceptions:
     *  HTTP 409: Project already exists

    Example: https://api.pub.build.mozilla.org/mapper/build-puppet

