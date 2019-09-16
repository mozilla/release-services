# Tooltool

This is tooltool.  Tooltool is a program that helps make downloading large
binaries easier in a CI environment.  The program creates a json based manifest
that is small compared to the binaries.  That manifest is transmitted to the
machine that needs the binary somehow (checked in, included in tarball, etc)
where the machine will run tooltool to download.

When using the fetch mode, the program will check to see if the file exists
locally.  If this file does not exist locally the program will try to fetch
from one of the base URLs provided.  The API that tooltool uses to fetch files
is exceedingly simple.  the API is that each file request will look for an http
resource that is a combination of an arbitrary base url, a directory that is
named as the hashing algorithm used and the hashing results of each file stored.

Example, using base url of "http://localhost:8080/tooltool", algorithm of "sha512"
and a file that hashes to "abcedf0123456789", tooltool would look for the file
at "http://localhost:8080/tooltool/sha512/abcdef0123456789".  If there is a local
file that has the filename specified in the manifest already, tooltool will not
overwrite by default.  In this case, tooltool will exit with a non-0 exit value.
If overwrite mode is enabled, tooltool will overwrite the local file with the
file specified in the manifest.

## Server

This repository contains only the tooltool client -- `tooltool.py`.
The tooltool server component is a part of [RelengAPI](https://github.com/mozilla/build-relengapi).

If you want to use the client, just copy out `tooltool.py` -- it has no
dependencies.

## Development

To hack on the tooltool client, install into a virtualenv with

    pip install -e .[test]

Send pull requests through GitHub.

Both the client and the server components are covered by Travis, via the
`validate.sh` script which you can run yourself.
