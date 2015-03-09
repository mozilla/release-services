# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class File(wsme.types.Base):

    """A representation of a single file, identified by its contents rather
    than its filename.  Depending on context, this may contain URLs to download
    or upload the file."""

    #: The size of the file, in bytes
    size = int

    #: The sha512 digest of the file contents
    digest = unicode

    #: The digest algorithm (reserved for future expansion;
    #: must always be 'sha512')
    algorithm = unicode

    #: The visibility level of this file.  When making an upload, the uploader
    #: is (legally!) responsible for selecting the correct visibility level.
    visibility = wsme.types.wsattr(
        wsme.types.Enum(unicode, 'public', 'internal'),
        mandatory=True)

    #: The URL from which this file can be downlaoded via HTTP GET
    get_url = wsme.types.wsattr(unicode, mandatory=False)

    #: The URL to which this file can be uploaded via HTTP PUT.  The URL
    #: requires the request content-type to be ``application/octet-stream``.
    put_url = wsme.types.wsattr(unicode, mandatory=False)


class UploadBatch(wsme.types.Base):

    """An upload batch describes a collection of related files that
    are uploaded together -- similar to a version-control commit.  The
    message and files list must be non-empty."""

    #: Identifier for this batch
    id = wsme.types.wsattr(int, mandatory=False)

    #: The author (uploader) of the batch.  On submitting a new batch,
    #: this must be the email of the authenticated user.
    author = wsme.types.wsattr(unicode, mandatory=True)

    #: The message for the batch.  Format this like a version-control message.
    message = wsme.types.wsattr(unicode, mandatory=True)

    #: The collection of files in this batch, keyed by filename.  Note that
    #: filenames containing path separators (``\`` and ``/``) will be rejected the
    #: tooltool client.
    files = wsme.types.wsattr({unicode: File}, mandatory=True)
