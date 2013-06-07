#!/usr/bin/env python

#tooltool is a lookaside cache implemented in Python
#Copyright (C) 2011 John H. Ford <john@johnford.info>
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation version 2
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# An manifest file specifies files in that directory that are stored
# elsewhere.  This file should only contain file in the directory
# which the manifest file resides in and it should be called 'manifest.manifest'

__version__ = '1'

import os
import optparse
import logging
import hashlib
import urllib2
import shutil
import sys
import time

try:
    import simplejson as json  # I hear simplejson is faster
except ImportError:
    import json

log = logging.getLogger(__name__)


class FileRecordJSONEncoderException(Exception):
    pass


class InvalidManifest(Exception):
    pass


class ExceptionWithFilename(Exception):

    def __init__(self, filename):
        Exception.__init__(self)
        self.filename = filename


class DigestMismatchException(ExceptionWithFilename):
    pass


class MissingFileException(ExceptionWithFilename):
    pass


class FileRecord(object):

    def __init__(self, filename, size, digest, algorithm):
        object.__init__(self)
        self.filename = filename
        self.size = size
        self.digest = digest
        self.algorithm = algorithm
        log.debug("creating %s 0x%x" % (self.__class__.__name__, id(self)))

    def __eq__(self, other):
        if self is other:
            return True
        if self.filename == other.filename and \
           self.size == other.size and \
           self.digest == other.digest and \
           self.algorithm == other.algorithm:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "%s.%s(filename='%s', size='%s', digest='%s', algorithm='%s')" % (__name__,
                                                                                 self.__class__.__name__,
                                                                                 self.filename,
                                                                                 self.size,
                                                                                 self.digest, self.algorithm)

    def present(self):
        # Doesn't check validity
        return os.path.exists(self.filename)

    def validate_size(self):
        if self.present():
            return self.size == os.path.getsize(self.filename)
        else:
            log.debug("trying to validate size on a missing file, %s", self.filename)
            raise MissingFileException(filename=self.filename)

    def validate_digest(self):
        if self.present():
            with open(self.filename, 'rb') as f:
                return self.digest == digest_file(f, self.algorithm)
        else:
            log.debug("trying to validate digest on a missing file, %s', self.filename")
            raise MissingFileException(filename=self.filename)

    def validate(self):
        if self.validate_size():
            if self.validate_digest():
                return True
        return False

    def describe(self):
        if self.present() and self.validate():
            return "'%s' is present and valid" % self.filename
        elif self.present():
            return "'%s' is present and invalid" % self.filename
        else:
            return "'%s' is absent" % self.filename


def create_file_record(filename, algorithm):
    fo = open(filename, 'rb')
    stored_filename = os.path.split(filename)[1]
    fr = FileRecord(stored_filename, os.path.getsize(filename), digest_file(fo, algorithm), algorithm)
    fo.close()
    return fr


class FileRecordJSONEncoder(json.JSONEncoder):

    def encode_file_record(self, obj):
        if not issubclass(type(obj), FileRecord):
            err = "FileRecordJSONEncoder is only for FileRecord and lists of FileRecords, not %s" % obj.__class__.__name__
            log.warn(err)
            raise FileRecordJSONEncoderException(err)
        else:
            return {'filename': obj.filename, 'size': obj.size, 'algorithm': obj.algorithm, 'digest': obj.digest}

    def default(self, f):
        if issubclass(type(f), list):
            record_list = []
            for i in f:
                record_list.append(self.encode_file_record(i))
            return record_list
        else:
            return self.encode_file_record(f)


class FileRecordJSONDecoder(json.JSONDecoder):
    """I help the json module materialize a FileRecord from
    a JSON file.  I understand FileRecords and lists of
    FileRecords.  I ignore things that I don't expect for now"""
    # TODO: make this more explicit in what it's looking for
    # and error out on unexpected things

    def process_file_records(self, obj):
        if isinstance(obj, list):
            record_list = []
            for i in obj:
                record = self.process_file_records(i)
                if issubclass(type(record), FileRecord):
                    record_list.append(record)
            return record_list
        if isinstance(obj, dict) and \
           len(obj.keys()) == 4 and \
           'filename' in obj and \
           'size' in obj and \
           'algorithm' in obj and \
           'digest' in obj:
            rv = FileRecord(obj['filename'], obj['size'], obj['digest'], obj['algorithm'])
            log.debug("materialized %s" % rv)
            return rv
        return obj

    def decode(self, s):
        decoded = json.JSONDecoder.decode(self, s)
        rv = self.process_file_records(decoded)
        return rv


class Manifest(object):

    valid_formats = ('json',)

    def __init__(self, file_records=None):
        self.file_records = file_records or []

    def __eq__(self, other):
        if self is other:
            return True
        if len(self.file_records) != len(other.file_records):
            log.debug('Manifests differ in number of files')
            return False
        #TODO: Lists in a different order should be equal
        for record in range(0, len(self.file_records)):
            if self.file_records[record] != other.file_records[record]:
                log.debug('FileRecords differ, %s vs %s' % (self.file_records[record],
                                                            other.file_records[record]))
                return False
        return True

    def __deepcopy__(self, memo):
        # This is required for a deep copy
        return Manifest(self.file_records[:])

    def __copy__(self):
        return Manifest(self.file_records)

    def copy(self):
        return Manifest(self.file_records[:])

    def present(self):
        return all(i.present() for i in self.file_records)

    def validate_sizes(self):
        return all(i.validate_size() for i in self.file_records)

    def validate_digests(self):
        return all(i.validate_digest() for i in self.file_records)

    def validate(self):
        return all(i.validate() for i in self.file_records)

    def sort(self):
        #TODO: WRITE TESTS
        self.file_records.sort(key=lambda x: x.size)

    def load(self, data_file, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            try:
                self.file_records.extend(json.load(data_file, cls=FileRecordJSONDecoder))
                self.sort()
            except ValueError:
                raise InvalidManifest("trying to read invalid manifest file")

    def loads(self, data_string, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            try:
                self.file_records.extend(json.loads(data_string, cls=FileRecordJSONDecoder))
                self.sort()
            except ValueError:
                raise InvalidManifest("trying to read invalid manifest file")

    def dump(self, output_file, fmt='json'):
        assert fmt in self.valid_formats
        self.sort()
        if fmt == 'json':
            rv = json.dump(self.file_records, output_file, indent=0, cls=FileRecordJSONEncoder)
            print >> output_file, ''
            return rv

    def dumps(self, fmt='json'):
        assert fmt in self.valid_formats
        self.sort()
        if fmt == 'json':
            return json.dumps(self.file_records, cls=FileRecordJSONEncoder)


def digest_file(f, a):
    """I take a file like object 'f' and return a hex-string containing
    of the result of the algorithm 'a' applied to 'f'."""
    h = hashlib.new(a)
    chunk_size = 1024 * 10
    data = f.read(chunk_size)
    while data:
        h.update(data)
        data = f.read(chunk_size)
    if hasattr(f, 'name'):
        log.debug('hashed %s with %s to be %s', f.name, a, h.hexdigest())
    else:
        log.debug('hashed a file with %s to be %s', a, h.hexdigest())
    return h.hexdigest()


# TODO: write tests for this function
def open_manifest(manifest_file):
    """I know how to take a filename and load it into a Manifest object"""
    if os.path.exists(manifest_file):
        manifest = Manifest()
        with open(manifest_file) as f:
            manifest.load(f)
            log.debug("loaded manifest from file '%s'" % manifest_file)
        return manifest
    else:
        log.debug("tried to load absent file '%s' as manifest" % manifest_file)
        raise InvalidManifest("manifest file '%s' does not exist" % manifest_file)


# TODO: write tests for this function
def list_manifest(manifest_file):
    """I know how print all the files in a location"""
    try:
        manifest = open_manifest(manifest_file)
    except InvalidManifest:
        log.error("failed to load manifest file at '%s'" % manifest_file)
        return False
    for f in manifest.file_records:
        print "%s\t%s\t%s" % ("P" if f.present() else "-",
                              "V" if f.present() and f.validate() else "-",
                              f.filename)
    return True


def validate_manifest(manifest_file):
    """I validate that all files in a manifest are present and valid but
    don't fetch or delete them if they aren't"""
    try:
        manifest = open_manifest(manifest_file)
    except InvalidManifest:
        log.error("failed to load manifest file at '%s'" % manifest_file)
        return False
    invalid_files = []
    absent_files = []
    for f in manifest.file_records:
        if not f.present():
            absent_files.append(f)
        else:
            if not f.validate():
                invalid_files.append(f)
    if len(invalid_files + absent_files) == 0:
        return True
    else:
        return False


# TODO: write tests for this function
def add_files(manifest_file, algorithm, filenames):
    # returns True if all files successfully added, False if not
    # and doesn't catch library Exceptions.  If any files are already
    # tracked in the manifest, return will be False because they weren't
    # added
    all_files_added = True
    # Create a old_manifest object to add to
    if os.path.exists(manifest_file):
        old_manifest = open_manifest(manifest_file)
    else:
        old_manifest = Manifest()
        log.debug("creating a new manifest file")
    new_manifest = Manifest()  # use a different manifest for the output
    for filename in filenames:
        log.debug("adding %s" % filename)
        path, name = os.path.split(filename)
        new_fr = create_file_record(filename, algorithm)
        log.debug("appending a new file record to manifest file")
        add = True
        for fr in old_manifest.file_records:
            log.debug("manifest file has '%s'" % "', ".join([x.filename for x in old_manifest.file_records]))
            if new_fr == fr and new_fr.validate():
                # TODO: Decide if this case should really cause a False return
                log.info("file already in old_manifest file and matches")
                add = False
            elif new_fr == fr and not new_fr.validate():
                log.error("file already in old_manifest file but is invalid")
                add = False
            if filename == fr.filename:
                log.error("manifest already contains file named %s" % filename)
                add = False
        if add:
            new_manifest.file_records.append(new_fr)
            log.debug("added '%s' to manifest" % filename)
        else:
            all_files_added = False
    with open(manifest_file, 'wb') as output:
        new_manifest.dump(output, fmt='json')
    return all_files_added


def touch(f):
    """Used to modify mtime in cached files;
    mtime is used by the purge command"""
    try:
        os.utime(f, None)
    except:
        log.warn('impossible to update utime of file %s' % f)


# TODO: write tests for this function
def fetch_file(base_urls, file_record, overwrite=False, grabchunk=1024 * 4, cache_folder=None):
    # A file which is requested to be fetched that exists locally will be hashed.
    # If the hash matches the requested file's hash, nothing will be done and the
    # function will return.  If the function is told to overwrite and there is a
    # digest mismatch, the exiting file will be overwritten

    #case 1: file already in current working directory
    if file_record.present():
        if file_record.validate():
            log.info("existing '%s' is valid, not fetching" % file_record.filename)
            return True
        if overwrite:
            log.info("overwriting '%s' as requested" % file_record.filename)
        else:
            # All of the following is for a useful error message
            with open(file_record.filename, 'rb') as f:
                d = digest_file(f, file_record.algorithm)
            log.error("digest mismatch between manifest(%s...) and local file(%s...)" %
                      (file_record.digest[:8], d[:8]))
            log.debug("full digests: manifest (%s) local file (%s)" % (file_record.digest, d))
            # Let's bail!
            return False

    # case 2: file already in cache
    if cache_folder:
        try:
            shutil.copy(os.path.join(cache_folder, file_record.digest), os.path.join(os.getcwd(), file_record.filename))
            log.info("File %s retrieved from local cache %s" % (file_record.filename, cache_folder))
            touch(os.path.join(cache_folder, file_record.digest))
            return True
        except IOError:
            log.info("File %s not present in local cache folder %s" % (file_record.filename, cache_folder))

    #case 3: file needs to be fetched from remote url; local cache (if any) needs to be updated
    fetched = False
    for base_url in base_urls:
        # Generate the URL for the file on the server side
        url = "%s/%s/%s" % (base_url, file_record.algorithm, file_record.digest)

        log.info("Attempting to fetch from '%s'..." % base_url)

        # TODO: This should be abstracted to make generic retrival protocol handling easy
        # Well, the file doesn't exist locally.  Let's fetch it.
        try:
            f = urllib2.urlopen(url)
            log.debug("opened %s for reading" % url)
            with open(file_record.filename, 'wb') as out:
                k = True
                size = 0
                while k:
                    # TODO: print statistics as file transfers happen both for info and to stop
                    # buildbot timeouts
                    indata = f.read(grabchunk)
                    out.write(indata)
                    size += len(indata)
                    if indata == '':
                        k = False
                log.info("File %s fetched from %s" % (file_record.filename, base_url))
                fetched = True
        except (urllib2.URLError, urllib2.HTTPError, ValueError) as e:
            log.info("...failed to fetch '%s' from %s" % (file_record.filename, base_url))
            log.debug("%s" % e)
        except IOError:
            log.info("failed to write to '%s'" % file_record.filename, exc_info=True)

    # I am managing a cache and a new file has just been retrieved from a remote location
    if cache_folder and fetched:
        log.info("Updating local cache %s..." % cache_folder)
        try:
            shutil.copy(os.path.join(os.getcwd(), file_record.filename), os.path.join(cache_folder, file_record.digest))
            log.info("Local cache %s updated with %s" % (cache_folder, file_record.filename))
            touch(os.path.join(cache_folder, file_record.digest))
        except IOError:
            log.info('Impossible to add file %s to cache folder %s' % (file_record.filename, cache_folder), exc_info=True)
    return fetched


# TODO: write tests for this function
def fetch_files(manifest_file, base_urls, overwrite, filenames=[], cache_folder=None):
    # Lets load the manifest file
    try:
        manifest = open_manifest(manifest_file)
    except InvalidManifest:
        log.error("failed to load manifest file at '%s'" % manifest_file)
        return False
    # We want to track files that fail to be fetched as well as
    # files that are fetched
    failed_files = []

    # Lets go through the manifest and fetch the files that we want
    fetched_files = []
    for f in manifest.file_records:
        if f.filename in filenames or len(filenames) == 0:
            log.debug("fetching %s" % f.filename)
            if fetch_file(base_urls, f, overwrite, cache_folder=cache_folder):
                fetched_files.append(f)
            else:
                failed_files.append(f.filename)
        else:
            log.debug("skipping %s" % f.filename)

    # Even if we get the file, lets ensure that it matches what the
    # manifest specified
    for localfile in fetched_files:
        if not localfile.validate():
            failed_files.append(f.filename)
            log.error("'%s'" % localfile.describe())

    # If we failed to fetch or validate a file, we need to fail
    if len(failed_files) > 0:
        log.error("The following files failed: '%s'" % "', ".join(failed_files))
        return False
    return True

if sys.platform == 'win32':
    # os.statvfs doesn't work on Windows
    import win32file

    def freespace(p):
        secsPerClus, bytesPerSec, nFreeClus, totClus = win32file.GetDiskFreeSpace(p)
        return secsPerClus * bytesPerSec * nFreeClus
else:

    def freespace(p):
        "Returns the number of bytes free under directory `p`"
        r = os.statvfs(p)
        return r.f_frsize * r.f_bavail


def remove(absolute_file_path):
    try:
        os.remove(absolute_file_path)
    except OSError as e:
        log.info("Impossible to remove %s" % absolute_file_path, exc_info=True)


def purge(folder, gigs):
    """If gigs is non 0, it deletes files in `folder` until `gigs` GB are free, starting from older files.
    If gigs is 0, a full purge will be performed.
    No recursive deletion of files in subfolder is performed."""

    gigs *= 1024 * 1024 * 1024

    files = []
    try:
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            # it delete files in folder without going into subfolders, assuming the cache has a flat structure
            if not os.path.isfile(p):
                continue
            mtime = os.path.getmtime(p)
            files.append((mtime, p))
    except:
        log.info('Impossible to list content of folder %s' % folder, exc_info=True)

    files.sort()

    if gigs:
        enough_free_space_yet = False
        while files and not enough_free_space_yet:
            mtime, f = files.pop(0)

            if freespace(folder) >= gigs:
                enough_free_space_yet = True
            else:
                log.info("removing %s to free up space" % f)
                remove(f)
    else:
        #full cleanup
        while files:
            mtime, f = files.pop(0)
            log.info("Full cache purge: removing %s" % f)
            remove(f)


# TODO: write tests for this function
def process_command(options, args):
    """ I know how to take a list of program arguments and
    start doing the right thing with them"""
    cmd = args[0]
    cmd_args = args[1:]
    log.debug("processing '%s' command with args '%s'" % (cmd, '", "'.join(cmd_args)))
    log.debug("using options: %s" % options)

    #better to check early and exit in case the provided cache folder does not exist
    if options.get('cache_folder'):
        if (not os.path.exists(options.get('cache_folder'))):
            try:
                log.info("The specified cache_folder %s does not exist" % options.get('cache_folder'))
                os.makedirs(options.get('cache_folder'), 0700)
                log.info("cache_folder %s has been created" % options.get('cache_folder'))
            except OSError:
                log.critical('Impossible to create folder "%s"' % options.get('cache_folder'), exc_info=True)
                return False

    if cmd == 'list':
        return list_manifest(options['manifest'])
    if cmd == 'validate':
        return validate_manifest(options['manifest'])
    elif cmd == 'add':
        return add_files(options['manifest'], options['algorithm'], cmd_args)
    elif cmd == 'purge':
        if not options.get('cache_folder'):
            log.critical('please specify the cache_folder to be purged with -c or --cache_folder option')
            return False
        else:
            purge(folder=options['cache_folder'], gigs=options['size'])
    elif cmd == 'fetch':
        if not options.get('base_url'):
            log.critical('fetch command requires at least one url provided using ' +
                         'the url option in the command line')
            return False
        return fetch_files(options['manifest'], options['base_url'], options['overwrite'], cmd_args, cache_folder=options['cache_folder'])
    else:
        log.critical('command "%s" is not implemented' % cmd)
        return False


# fetching api:
#   http://hostname/algorithm/hash
#   example: http://people.mozilla.org/sha1/1234567890abcedf
# This will make it possible to have the server allow clients to
# use different algorithms than what was uploaded to the server

# TODO: Implement the following features:
#   -optimization: do small files first, justification is that they are faster
#    and cause a faster failure if they are invalid
#   -store permissions
#   -local renames i.e. call the file one thing on the server and
#    something different locally
#   -deal with the cases:
#     -local data matches file requested with different filename
#     -two different files with same name, different hash
#   -?only ever locally to digest as filename, symlink to real name
#   -?maybe deal with files as a dir of the filename with all files in that dir as the versions of that file
#      - e.g. ./python-2.6.7.dmg/0123456789abcdef and ./python-2.6.7.dmg/abcdef0123456789


def main():
    # Set up logging, for now just to the console
    ch = logging.StreamHandler()
    cf = logging.Formatter("%(levelname)s - %(message)s")
    ch.setFormatter(cf)

    # Set up option parsing
    parser = optparse.OptionParser()
    # I wish there was a way to say "only allow args to be
    # sequential and at the end of the argv.
    # OH! i could step through sys.argv and check for things starting without -/-- before things starting with them
    parser.add_option('-q', '--quiet', default=False,
                      dest='quiet', action='store_true')
    parser.add_option('-v', '--verbose', default=False,
                      dest='verbose', action='store_true')
    parser.add_option('-m', '--manifest', default='manifest.tt',
                      dest='manifest', action='store',
                      help='specify the manifest file to be operated on')
    parser.add_option('-d', '--algorithm', default='sha512',
                      dest='algorithm', action='store',
                      help='openssl hashing algorithm to use')
    parser.add_option('-o', '--overwrite', default=False,
                      dest='overwrite', action='store_true',
                      help='if fetching, remote copy will overwrite a local copy that is different. ')
    parser.add_option('--url', dest='base_url', action='append',
                      help='base url for fetching files')
    parser.add_option('-c', '--cache_folder', dest='cache_folder',
                      help='Local cache folder')
    parser.add_option('-s', '--size',
                      help='free space required (in GB)', dest='size',
                      type='float', default=0.)

    (options_obj, args) = parser.parse_args()
    # Dictionaries are easier to work with
    options = vars(options_obj)
    # Use some of the option parser to figure out application
    # log level
    if options.get('verbose'):
        ch.setLevel(logging.DEBUG)
    elif options.get('quiet'):
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.INFO)
    log.addHandler(ch)

    if not 'manifest' in options:
        parser.error("no manifest file specified")

    if len(args) < 1:
        parser.error('You must specify a command')
    exit(0 if process_command(options, args) else 1)

if __name__ == "__main__":
    main()
else:
    log.addHandler(logging.NullHandler())
    #log.addHandler(logging.StreamHandler())
