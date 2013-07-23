#!/usr/bin/env python

#tooltool is a lookaside cache implemented in Python
#Copyright (C) 2013 Mozilla Foundation
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

import logging
import logging.handlers
import json
import os
import shutil

import re

import tooltool  # to read manifests

import datetime

LOG_FILENAME = 'tooltool_sync.log'
DEFAULT_LOG_LEVEL = logging.DEBUG

log = logging.getLogger(__name__)
log.setLevel(DEFAULT_LOG_LEVEL)

handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=1000000,
                                               backupCount=100,
                                               )


formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

handler.setLevel(DEFAULT_LOG_LEVEL)
handler.setFormatter(formatter)
log.addHandler(handler)


CONFIG_FILENAME = 'config.json'


def validate_config(config):

    matching = {}
    root = ""

    if config['root'] and os.path.exists(config['root']) and os.path.isdir(config['root']):
        root = config['root']
    else:
        log.critical("The configuration file does not contain a valid root folder")
        exit(1)

    if config['matching'] and type(config['matching']) is dict:
        matching = config['matching']
    else:
        log.critical("The configuration file does not contain a matching section (a dictionary)")
        exit(1)

    pathsOK = True
    for distribution_level in matching:
        destination = matching[distribution_level]
        if not (os.path.exists(destination) and os.path.isdir(destination)):
            log.critical("The folder %s, mentioned in the configuration file,  does not exist" % destination)
            pathsOK = False
    if not pathsOK:
        exit(1)

    return root, matching


def load_json(filename):
    try:
        f = open(filename, 'r')
        data = json.load(f)
        f.close()
    except IOError as e:
        log.critical("Impossible to read file %s; I/O error(%s): %s" % (filename, e.errno, e.strerror))
        exit(1)
    except ValueError as e:
        log.critical("Impossible to load file %s; Value error: %s" % (filename, e))
        exit(1)
    except:
        log.critical("Unexpected error: %s" % sys.exc_info()[0])
        exit(1)

    return data


def persist_json(data, filepath):
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, indent = 2)


def load_config():
    config = load_json(CONFIG_FILENAME)
    return validate_config(config)


PROCESSED_DIGESTS = "processed_digests.json"
if not os.path.exists(PROCESSED_DIGESTS):
    persist_json({}, PROCESSED_DIGESTS)

#{digest:(manifest)}

processed_files = load_json(PROCESSED_DIGESTS)

PROCESSED_MANIFESTS = "processed_manifests.json"
if not os.path.exists(PROCESSED_MANIFESTS):
    persist_json({}, PROCESSED_MANIFESTS)

#{processed_manifest:(user, notes, distribution_type )}

processed_manifests = load_json(PROCESSED_MANIFESTS)


def already_processed(digest):
    return digest in processed_files
    #TODO


def get_upload_folder(root, user, distribution_type):
    #e.g. /home/something/tooltool_root/bob/pvt
    return os.path.join(os.path.join(root, user), distribution_type)


def getDigests(manifest):
    manifest = tooltool.open_manifest(manifest)
    return [(x.digest, x.algorithm) for x in manifest.file_records]


def isnew(upload_folder, manifestname):
    for digest in [x for (x, y) in getDigests(os.path.join(upload_folder, manifestname))]:
        if already_processed(digest):
            return False
    return True


def begins_with_timestamp(filename):
    p = re.compile("\d+_\d+_\d+-\d+.\d+.\d+")
    return p.match(filename)


def main():

    root, matching = load_config()
    users = []
    for (_dirpath, dirnames, _files) in os.walk(root):
        users.extend(dirnames)
        break  # not to navigate subfolders

    for user in users:
        for distribution_type in matching:
            files = []

            upload_folder = get_upload_folder(root, user, distribution_type)
            for (dirpath, _dirnames, _files) in os.walk(upload_folder):
                files.extend(_files)
                break  # not to navigate subfolders

            # "new" means that it has to be processed
            new_manifests = [filename for filename in files if (filename.endswith(".tt") and not begins_with_timestamp(filename) and isnew(upload_folder, filename))]

            for new_manifest in new_manifests:
                new_manifest_path = os.path.join(upload_folder, new_manifest)
                destination = matching[distribution_type]
                timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H.%M.%S")
                processed_manifest_name = "%s.%s" % (timestamp, new_manifest)
                digests = getDigests(new_manifest_path)
                # checking that ALL files mentioned in the manifest are in the upload folder, otherwise I cannot proceed copying
                allFilesAreOK = True  # I am an optimist!
                for digest, algorithm in digests:
                    digest_path = os.path.join(upload_folder, digest)
                    if not os.path.exists(digest_path):
                        allFilesAreOK = False
                        log.error("Impossible to process manifest %s because one of the mentioned file does not exist" % new_manifest)
                    else:
                        log.debug("Found file %s, let's check the content" % digest)
                        with open(digest_path, 'rb') as f:
                            d = tooltool.digest_file(f, algorithm)
                            if d == digest:
                                log.debug("Great! File %s is what he declares to be!")
                            else:
                                allFilesAreOK = False
                                log.error("Impossible to process manifest %s because the mentioned file %s has an incorrect content" % (new_manifest, digest))

                if allFilesAreOK:

                    # copying the digest files to destination
                    copyOK = True
                    for digest, _algorithm in digests:
                        comment = ""
                        comment_filename = new_manifest.replace(".tt", ".txt")
                        comment_filepath = os.path.join(upload_folder, new_manifest.replace(".tt", ".txt"))
                        if os.path.exists(comment_filepath):
                            with open(comment_filepath) as f:
                                comment = f.read()

                        try:
                            shutil.copy(digest_path, os.path.join(destination, "temp%s" % digest))
                        except IOError as e:
                            log.error("Impossible to copy file %s to %s; I/O error(%s): %s" % (digest_path, destination, e.errno, e.strerror))
                            copyOK = False
                            break
                    if copyOK:
                        # updating metadata
                        for digest, _algorithm in digests:
                            processed_files[digest] = processed_manifest_name
                        processed_manifests[processed_manifest_name] = (user, comment, distribution_type)

                        renamingOK = True
                        for digest, _algorithm in digests:
                            try:
                                os.rename(os.path.join(destination, "temp%s" % digest), os.path.join(destination, digest))
                            except:
                                log.error("Impossible to rename file %s to %s;" % (os.path.join(destination, "temp%s" % digest), os.path.join(destination, digest)))
                                renamingOK = False
                            # persist changes to json files

                        if renamingOK:
                            # rename original manifest name appending timestanp
                            os.rename(new_manifest_path, os.path.join(upload_folder, processed_manifest_name))
                            # keep a local copy of the processed manifest
                            shutil.copy(os.path.join(upload_folder, processed_manifest_name), os.getcwd())
                            # rename the comment file, just appending a timestamp
                            os.rename(comment_filepath, os.path.join(upload_folder, "%s.%s" % (timestamp, comment_filename)))
                            # persists the json metadata files
                            persist_json(processed_files, PROCESSED_DIGESTS)
                            persist_json(processed_manifests, PROCESSED_MANIFESTS)
                        else:
                            # no changes to the metadata, no changes to the original upload folder, maybe next time...
                            pass
                if allFilesAreOK and copyOK and renamingOK:
                    pass
                else:
                    log.error("Manifest %s has NOT been processed" % new_manifest)

if __name__ == "__main__":
    main()
