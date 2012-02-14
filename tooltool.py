#!/usr/bin/env python

# An manifest file specifies files in that directory that are stored
# elsewhere.  This file should only contain file in the directory
# which the manifest file resides in and it should be called 'manifest.manifest'

__version__ = '1'

import sys
import os
import os.path as systempath
import posixpath
import optparse
import logging
import hashlib
import urllib2
import time
try:
    import simplejson as json # I hear simplejson is faster
except ImportError:
    import json

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class FileRecordJSONEncoderException(Exception): pass
class InvalidManifest(Exception): pass
class ExceptionWithFilename(Exception):
    def __init__(self, filename):
        Exception.__init__(self)
        self.filename = filename

class DigestMismatchException(ExceptionWithFilename): pass
class MissingFileException(ExceptionWithFilename): pass

class FileRecord(object):
    def __init__(self, filename, size, digest, algorithm):
        #TODO: Add the ability to create a FileRecord that generates
        # the size and digest based on filesystem contents
        object.__init__(self)
        self.filename = filename
        self.size = size
        self.digest = digest
        self.algorithm = algorithm
        log.debug("creating %s 0x%x" % (self.__class__.__name__, id(self)))

    def __eq__(self, other):
        if self is other:
            return True
        if self.filename == other.filename:
            if self.size == other.size:
                if self.digest == other.digest:
                    if self.algorithm == other.algorithm:
                        return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "%s.%s(filename='%s', size='%s', digest='%s', algorithm='%s')" % (__name__,
                self.__class__.__name__,
                self.filename, self.size, self.digest, self.algorithm)

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
            with open(self.filename) as f:
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
            err="FileRecordJSONEncoder is only for FileRecord and lists of FileRecords, not %s" % obj.__class__.__name__
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
           obj.has_key('filename') and \
           obj.has_key('size') and \
           obj.has_key('algorithm') and \
           obj.has_key('digest'):
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

    def __init__(self, file_records=[]):
        self.file_records = file_records

    def __eq__(self, other):
        if self is other:
            return True
        if len(self.file_records) != len(other.file_records):
            log.debug('Manifests differ in number of files')
            return False
        #TODO: Lists in a different order should be equal
        for record in range(0,len(self.file_records)):
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
        for i in self.file_records:
            if not i.present():
                return False
        return True

    def validate_sizes(self):
        for i in self.file_records:
            if not i.validate_size():
                return False
        return True

    def validate_digests(self):
        for i in self.file_records:
            if not i.validate_digest():
                return False
        return True

    def validate(self):
        for i in self.file_records:
            if not i.validate():
                return False
        return True

    def load(self, data_file, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            try:
                self.file_records.extend(json.load(data_file, cls=FileRecordJSONDecoder))
            except ValueError:
                raise InvalidManifest("trying to read invalid manifest file")

    def loads(self, data_string, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            try:
                self.file_records.extend(json.loads(data_string, cls=FileRecordJSONDecoder))
            except ValueError:
                raise InvalidManifest("trying to read invalid manifest file")

    def dump(self, output_file, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            rv = json.dump(self.file_records, output_file, indent=0, cls=FileRecordJSONEncoder)
            print >> output_file, ''
            return rv

    def dumps(self, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            return json.dumps(self.file_records, cls=FileRecordJSONEncoder)


def digest_file(f,a):
    """I take a file like object 'f' and return a hex-string containing
    of the result of the algorithm 'a' applied to 'f'."""
    h = hashlib.new(a)
    chunk_size = 1024*10
    data = f.read(chunk_size)
    while data:
        h.update(data)
        data = f.read(chunk_size)
    if hasattr(f, 'name'):
        log.debug('hashed %s with %s to be %s', f.name, a, h.hexdigest())
    else:
        log.debug('hashed a file with %s to be %s', a, h.hexdigest())
    return h.hexdigest()

def open_manifest(manifest_file):
    """I know how to take a filename and load it into a Manifest object"""
    manifest = Manifest()
    if os.path.exists(manifest_file):
        with open(manifest_file) as f:
            manifest.load(f)
            log.debug("loaded manifest from file '%s'" % manifest_file)
            return manifest
    else:
        log.debug("tried to load absent file '%s' as manifest" % manifest_file)
        raise InvalidManifest("manifest file '%s' does not exist" % manifest_file)

def list_manifest(manifest_file):
    """I know how print all the files in a location"""
    try:
        manifest = open_manifest(manifest_file)
    except InvalidManifest:
        log.error("failed to load manifest file at '%s'" % manifest_file)
        return False
    for f in manifest.file_records:
        print f.describe()

def add_files(manifest_file, algorithm, filenames):
    # Create a manifest object to add to
    if os.path.exists(manifest_file):
        manifest = open_manifest(manifest_file)
    else:
        log.debug("creating a new manifest file")
    new_manifest = Manifest() # use a different manifest for the output
    for filename in filenames:
        log.debug("adding %s" % filename)
        path, name = os.path.split(filename)
        new_fr = create_file_record(filename, 'sha512')
        log.debug("appending a new file record to manifest file")
        add = True
        for fr in manifest.file_records:
            log.debug("manifest file has '%s'" % "', ".join([x.filename for x in manifest.file_records]))
            if new_fr == fr and new_fr.validate():
                log.info("file already in manifest file and matches")
                add = False
            elif new_fr == fr and not new_fr.validate():
                log.error("file already in manifest file but is invalid")
                add = False
            if filename == fr.filename:
                log.error("manifest already contains file named %s" % filename)
                add = False
        if add:
            new_manifest.file_records.append(new_fr)
    with open(manifest_file, 'wb') as output:
        new_manifest.dump(output, fmt='json')

def fetch_file(base_url, file_record, overwrite=False, grabchunk=1024*8):
    # A file which is requested to be fetched that exists locally will be hashed.
    # If the hash matches the requested file's hash, nothing will be done and the
    # function will return.  If the function is told to overwrite and there is a 
    # digest mismatch, the exiting file will be overwritten
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
            log.error("digest mismatch between manifest(%s...) and local file(%s...)" % \
                    (file_record.digest[:8], d[:8]))
            log.debug("full digests: manifest (%s) local file (%s)" % (file_record.digest, d))
            # Let's bail!
            return False

    # Generate the URL for the file on the server side
    url = "%s/%s/%s" % (base_url, file_record.algorithm, file_record.digest)

    # Well, the file doesn't exist locally.  Lets fetch it.
    try:
        f = urllib2.urlopen(url)
        log.debug("opened %s for reading" % url)
        with open(file_record.filename, 'wb') as out:
            k = True
            size = 0
            t = time.time()
            while k:
                indata = f.read(grabchunk)
                out.write(indata)
                size += len(indata)
                # TODO: verify that this speed is valid
                log.debug("AVG SPEED: %0.2f Bytes/Second TOTAL TRANSFERED: %i" % (float(size / (time.time() - t)),
                                                                                 size))
                if indata == '':
                    k = False
            if size != file_record.size:
                log.error("transfer from %s to %s failed due to a difference of %d bytes" % (url,
                            file_record.filename, file_record.size - size))
                return False
            log.info("fetched %s" % file_record.filename)
    except urllib2.URLError as urlerror:
        log.error("FAILED TO GRAB %s: %s" % (url, urlerror))
        return False
    except urllib2.HTTPError as httperror:
        log.error("FAILED TO GRAB %s: %s" % (url, httperror))
        return False
    except IOError as ioerror:
        log.error("FAILED TO WRITE TO %s" % file_record.filename)
        return False
    return True


def fetch_files(manifest_file, base_url, overwrite, filenames=[]):
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
        if f.filename in filenames:
            log.debug("fetching %s" % f.filename)
            if fetch_file(base_url, f, overwrite):
                fetched_files.append(f)
            else:
                failed_files.append(f.filename)
                log.error("fetching '%s' failed" % f.filename)
        else:
            log.debug("skipping %s" % f.filename)

    # Even if we get the file, lets ensure that it matches what the
    # manifest specified
    for localfile in fetched_files:
        if not localfile.validate():
            log.error("'%s' failed validation" % localfile.filename)

    # If we failed to fetch or validate a file, we need to fail
    if len(failed_files) > 0:
        log.error("The following files failed: '%s'" % "', ".join(failed_files))
        return False
    return True


def process_command(options, args):
    """ I know how to take a list of program arguments and
    start doing the right thing with them"""
    cmd = args[0]
    cmd_args = args[1:]
    log.debug('using command %s' % cmd)
    if cmd == 'list':
        return list_manifest(options.manifest)
    elif cmd == 'add':
        return add_files(options.manifest, options.algorithm, cmd_args)
    elif cmd == 'fetch':
        return fetch_files(options.manifest, 'http://localhost:8080', options.overwrite, cmd_args)
    else:
        log.critical('command "%s" is not implemented' % cmd)
        return False

# fetching api:
#   http://hostname/algorithm/hash
#   example: http://people.mozilla.org/sha1/1234567890abcedf
# This will make it possible to have the server allow clients to
# use different algorithms than what was uploaded to the server

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
    parser.add_option('-r', '--recurse', default=True,
            dest='recurse', action='store_false',
            help='if specified, directories will be recursed when scanning for .manifest files')
    parser.add_option('-m', '--manifest', default='manifest.tt',
            dest='manifest', action='store',
            help='specify the manifest file to be operated on')
    parser.add_option('-d', '--algorithm', default='sha512',
            dest='algorithm', action='store',
            help='openssl hashing algorithm to use')
    parser.add_option('-o', '--overwrite', default=False,
            dest='overwrite', action='store_true',
            help='if fetching, remote copy will overwrite a local copy that is different. ' +
                 'UNIMPLEMENTED: if adding, the local file will overwrite the manifest copy')
    (options, args) = parser.parse_args()

    # Use some of the option parser to figure out application
    # log level
    if options.verbose:
        ch.setLevel(logging.DEBUG)
    elif options.quiet:
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.INFO)
    log.addHandler(ch)

    if not options.manifest:
        log.critical("no manifest file specified")
        exit(1)

# THIS IS BUSTED
#    # Doing this because I want all options before all arguments
#    yet_seen_arg = False
#    for i in sys.argv[1:]:
#        if i.startswith('-') and yet_seen_arg:
#            log.critical("arguments should occur before options")
#            exit(1)
#        if not i.startswith('-'):
#            yet_seen_arg = True

    log.debug('processing command "%s"' % '", "'.join(args))
    if len(args) < 1:
        log.critical('You must specify a command')
        exit(1)
    exit(0 if process_command(options, args) else 1)

if __name__ == "__main__":
    main()
else:
    log.addHandler(logging.NullHandler())
    #log.addHandler(logging.StreamHandler())
