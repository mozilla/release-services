#!/usr/bin/env python

# An aside file specifies files in that directory that are stored
# elsewhere.  This file should only contain file in the directory
# which the aside file resides in

import os
import os.path as systempath
import posixpath
import optparse
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class InvalidAsideFile(Exception): pass

def pretty_files(files):
    """ I am a function that makes a list of filename strings
    into a string that surrounds each filename in a quote and
    inserts a comma between filenames"""
    return '"%s"' % '", "'.join(files)

def validate_aside_file(aside_filename):
    """Once implemented, I will take a filename and validate
    it as an aside file.  For now, I do nothing.  I return the
    filename that I am given and raise an exception if it's
    invalid.  I only work with file content"""
    log.debug('%s is a valid aside file NOOP' % aside_filename)
    return aside_filename

def guess_aside_file(filename):
    """I will guess if a filename is an aside file.  I only look
    at the filename"""
    rv = systempath.isfile(filename) and filename.endswith('.aside')
    log.debug('%s %s an aside file' % (filename, 'is' if rv else 'is NOT'))

def find_aside_files(locations, recurse=False):
    """I find all .aside files at locations.  If a location
    is already a .aside file, I include it verbatim.  If I
    am told do, I will recurse directories passed as locations"""
    aside_files = []
    for location in locations:
        if systempath.isfile(location):
            log.debug('checking %s' % location)
            aside_files.append(validate_aside_file(location))
        elif systempath.isdir(location):
            for root,dirs,files in os.walk(location):
                for f in files:
                    if guess_aside_file(systempath.join(root,f)):
                        aside_files.append(validate_aside_file(systempath.join(root,f)))
                if not recurse:
                    break
    # TODO: remove duplicates in this list
    return aside_files



def process_command(args, recurse=False):
    cmd = args[0]
    cmd_args = args[1:]
    log.debug('using command %s' % cmd)
    if cmd == 'retreive':
        log.debug('validating aside files %s' % pretty_files(cmd_args))
        aside_files = find_aside_files(cmd_args, recurse=recurse)
    else:
        log.critical('command "%s" is not implemented' % cmd)



def main():
    # Set up logging, for now just to the console
    ch = logging.StreamHandler()
    cf = logging.Formatter("%(asctime)s - %(pathname)s - %(levelname)s - %(message)s")
    ch.setFormatter(cf)

    # Set up option parsing
    parser = optparse.OptionParser()
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

    log.debug('processing files at "%s"' % '", "'.join(args))
    if len(args) < 1:
        log.critical('You must specify a command')
        exit(1)
    process_command(args, options.recurse)

if __name__ == "__main__":
    main()
else:
    log.setHandler(logging.NullHandler())
