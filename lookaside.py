#!/usr/bin/env python

# An aside file specifies files in that directory that are stored
# elsewhere.  This file should only contain file in the directory
# which the aside file resides in and it should be called '.aside'

import sys
import os
import os.path as systempath
import posixpath
import optparse
import logging
import hashlib
try:
    import simplejson as json # I hear simplejson is faster
except ImportError:
    import json

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class FileRecordJSONEncoderException(Exception): pass
class InvalidAsideFile(Exception): pass
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


class AsideFile(object):

    valid_formats = ('json',)

    def __init__(self, file_records=[]):
        self.file_records = file_records

    def __eq__(self, other):
        if self is other:
            return True
        if len(self.file_records) != len(other.file_records):
            log.debug('AsideFiles differ in number of files')
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
        return AsideFile(self.file_records[:])

    def __copy__(self):
        return AsideFile(self.file_records)

    def copy(self):
        return AsideFile(self.file_records[:])

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
                raise InvalidAsideFile("trying to read invalid aside file")

    def loads(self, data_string, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            try:
                self.file_records.extend(json.loads(data_string, cls=FileRecordJSONDecoder))
            except ValueError:
                raise InvalidAsideFile("trying to read invalid aside file")

    def dump(self, output_file, fmt='json'):
        assert fmt in self.valid_formats
        if fmt == 'json':
            return json.dump(self.file_records, output_file, cls=FileRecordJSONEncoder)

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

def find_aside_files(locations, aside_filename='.aside', recurse=False):
    """I scan directories for their .aside file. If I am
    told to recurse, I do that."""
    # TODO: support a syntax to skip specific dirs while recursing
    aside_files = []
    for location in locations:
        if systempath.isdir(location):
            for root,dirs,files in os.walk(location):
                if os.path.exists(os.path.join(root, aside_filename)):
                    log.debug('adding %s to the list of aside_files' % aside_filename)
                    aside_files.append(os.path.join(root,aside_filename))
                    log.debug('found aside file in %s' % root)
                if not recurse:
                    break
        else:
            log.critical('%s is not a directory' % location)
    return aside_files


def list_tracked_files(locations, aside_filename='.aside', recurse=False):
    """I know how print all the files in a location"""
    aside_files = find_aside_files(locations,
            aside_filename=aside_filename,
            recurse=recurse)
    for aside_name in aside_files:
        aside = AsideFile()
        with open(aside_name) as a:
            aside.load(a)
        for f in aside.file_records:
            name = f.filename
            present = "present" if f.present() else "absent"
            if f.present():
                if f.validate():
                    valid = "valid"
                elif not f.validate_size():
                    valid = "the wrong size"
                elif not f.validate_digest():
                    valid = "has the wrong digest"
                else:
                    valid = "INVALID"
            else:
                valid = "missing"
            log.info("%s is %s and %s" % (name, present, valid))

def add_files(filenames):
    #this function's logic on how to create these things
    #should be moved to FileRecord/AsideFile
    for filename in filenames:
        path,name = os.path.split(filename)
        aside_name = os.path.join(path, '.aside')
        if os.path.exists(aside_name):
            aside_file = AsideFile()
            with open(aside_name) as f, open(name) as data:
                aside_file.load(f)
                new_digest = digest_file(data)
                for record in aside_file.file_records:
                    if new_digest == record.digest:
                        log.info("Already tracked")

def process_command(args, recurse=False):
    """ I know how to take a list of program arguments and
    start doing the right thing with them"""
    cmd = args[0]
    cmd_args = args[1:]
    log.debug('using command %s' % cmd)
    if cmd == 'list':
        list_tracked_files(cmd_args, recurse=recurse)
    elif cmd == 'add':
        list_tracked_files(cmd_args)
    else:
        log.critical('command "%s" is not implemented' % cmd)


def main():
    # Set up logging, for now just to the console
    ch = logging.StreamHandler()
    cf = logging.Formatter("%(asctime)s - %(pathname)s - %(levelname)s - %(message)s")
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
    parser.add_option('-d', '--debug', default=False,
            dest='debug', action='store_true')
    parser.add_option('-r', '--recurse', default=False,
            dest='recurse', action='store_true',
            help='if specified, directories will be recursed when scanning for .aside files')
    (options, args) = parser.parse_args()

    # Use some of the option parser to figure out application
    # log level
    if options.debug:
        ch.setLevel(logging.DEBUG)
    elif options.verbose:
        ch.setLevel(logging.INFO)
    elif options.quiet:
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.WARN)
    log.addHandler(ch)

    # Doing this because I want all options before all arguments
    yet_seen_arg = False
    for i in sys.argv[1:]:
        if i.startswith('-') and yet_seen_arg:
            log.critical("arguments should occur before options")
            exit(1)
        if not i.startswith('-'):
            yet_seen_arg = True


    log.debug('processing command "%s"' % '", "'.join(args))
    if len(args) < 1:
        log.critical('You must specify a command')
        exit(1)
    process_command(args, options.recurse)

if __name__ == "__main__":
    main()
else:
    log.addHandler(logging.NullHandler())
    #log.addHandler(logging.StreamHandler())
