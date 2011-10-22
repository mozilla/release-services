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

class InvalidAsideFileException(Exception): pass
class ExceptionWithFilename(Exception):
    def __init__(self, filename):
        Exception.__init__(self)
        self.filename = filename

class DigestMismatchException(ExceptionWithFilename): pass
class MissingFileException(ExceptionWithFilename): pass

class FileRecord(object):
    def __init__(self, filename, size, digest, algorithm):
        object.__init__(self)
        self.filename = filename
        self.size = size
        self.digest = digest
        self.algorithm = algorithm
        log.debug("creating AsideRecord %d", id(self))

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
                return self.digest == hash_file(f, self.algorithm)
        else:
            log.debug("trying to validate digest on a missing file, %s', self.filename")
            raise MissingFileException(filename=self.filename)

    def validate(self):
        if self.validate_size():
            if self.validate_digest():
                return True
        return False


def hash_file(f,a):
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



def pretty_files(files):
    """ I convert a list of filenames into something that
    is easier to print out for human consumption"""
    return '"%s"' % '", "'.join(files)

def validate_aside_file(aside_filename):
    """Once implemented, I will take a filename and validate
    it as an aside file.  For now, I do nothing.  I return the
    filename that I am given and raise an exception if it's
    invalid.  I only work with file content"""
    log.debug('%s is a valid aside file NOOP' % aside_filename)
    return aside_filename

def find_aside_file(location):
    """I will guess if a filename is an aside file.  I only look
    at the filename"""
    aside_filename = None
    if systempath.isdir(location) and systempath.isfile(systempath.join(location, '.aside')):
        aside_filename = systempath.join(location, '.aside')
        log.debug('aside for %s is %s' % (location, aside_filename))
    else:
        log.debug('no aside present for %s' % location)
    return aside_filename

def find_aside_files(locations, recurse=False):
    """I scan directories for their .aside file. If I am
    told to recurse, I do that."""
    # TODO: support a syntax to skip specific dirs while recursing
    aside_files = []
    for location in locations:
        if systempath.isdir(location):
            for root,dirs,files in os.walk(location):
                aside_filename = find_aside_file(root)
                if aside_filename:
                    log.debug('adding %s to the list of aside_files' % aside_filename)
                    aside_files.append(validate_aside_file(aside_filename))
                if not recurse:
                    break
        else:
            log.critical('%s is not a directory' % location)
    log.debug('found these aside files %s' % pretty_files(aside_files))
    return aside_files


def get_all(locations, recurse=False):
    """I know how to retreive all files specified by
    a lookaside cache"""
    aside_files = find_aside_files(locations, recurse=recurse)
    log.info('Retrieving all files in:')
    for aside_file in aside_files:
        log.info('  -%s' % systempath.split(aside_file)[0])

def add_to_aside_file(aside_file, filename):
    """I know how to add a file to an aside_file. If the aside
    file doesn't exist, I know how to create it, but I don't
    know how to add that file to a version control system."""
    if not systempath.isfile(aside_file):
        pass #Create it here!
        log.warn('if you are version tracking, you should add "%s" to your repository as it was just created' % aside_file)
    # Add to the file here
    log.info("adding %s to aside files") # BROKEN HERE

def add_files(filenames):
    #this function is stupid
    files_by_location = {}
    for filename in filenames:
        location = systempath.split(filename)[0]
        aside_file = find_aside_file(location)
        if files_by_location.has_key(location):
            record = files_by_location[location]
            assert files_by_location[location]['aside_file'] == aside_file
        else:
            record = {}
            files_by_location[location] = record
        record['aside_file'] = aside_file
        if record.has_key('filenames'):
            record['filenames'].append(filename)
        else:
            record['filenames'] = [filename]

    #NEED TO DO THIS SOMEWHERE if not systempath.isfile(aside_file):
            #log.warn('this command will create %s. you should add it to your repository')

def process_command(args, recurse=False):
    """ I know how to take a list of program arguments and
    start doing the right thing with them"""
    cmd = args[0]
    cmd_args = args[1:]
    log.debug('using command %s' % cmd)
    if cmd == 'get-all':
        get_all(cmd_args, recurse)
    elif cmd == 'add-file':
        add_files(cmd_args, recurse)
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
