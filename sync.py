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

import smtplib
from email.mime.text import MIMEText

STRFRTIME = "%Y_%m_%d-%H.%M.%S"
TIMESTAMP_REGEX = re.sub(r"%\D", "\d+", STRFRTIME)

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
    smtp_server = ""
    smtp_port = None
    smtp_from = ""
    email_addresses = {}
    smtp_user = ""
    smtp_password = ""

    if 'upload_root' in config and config['upload_root'] and os.path.exists(config['upload_root']) and os.path.isdir(config['upload_root']):
        root = config['upload_root']
    else:
        msg = "The configuration file does not contain a valid upload_root value"
        log.critical()
        raise SystemExit(msg)

    if 'target_folders' in config and config['target_folders'] and isinstance(config['target_folders'], dict):
        matching = config['target_folders']
    else:
        mag = "The configuration file does not specify the target folders for each distribution type (a dictionary named target_folders is needed)"
        log.critical(msg)
        raise SystemExit(msg)

    if 'smtp_server' in config and config['smtp_server']:
        smtp_server = config['smtp_server']
    else:
        msg = "The configuration file does not specify the smtp server to be used for email notifications"
        log.critical(msg)
        raise SystemExit(msg)

    if 'smtp_port' in config and config['smtp_port']:
        smtp_port = config['smtp_port']
    else:
        msg = "The configuration file does not specify the smtp port to be used for email notifications"
        log.critical(msg)
        raise SystemExit(msg)

    if 'smtp_from' in config and config['smtp_from']:
        smtp_from = config['smtp_from']
    else:
        msg = "The configuration file does not specify the 'from' email address to be used for email notifications"
        log.critical(msg)
        raise SystemExit(msg)

    if 'email_addresses' in config and config['email_addresses'] and isinstance(config['email_addresses'], dict):
        email_addresses = config['email_addresses']
    else:
        #This is not blocking since by default I wil use user@mozilla.com
        log.warning("The configuration file does not specify any addresses to be used for email notifications")

    if 'smtp_user' in config and config['smtp_user']:
        smtp_user = config['smtp_user']
    else:
        msg = "The configuration file does not specify the smtp user to be used for email notifications"
        log.critical(msg)
        raise SystemExit(msg)

    if 'smtp_password' in config and config['smtp_password']:
        smtp_password = config['smtp_password']
    else:
        msg = "The configuration file does not specify the smtp password to be used for email notifications"
        log.critical(msg)
        raise SystemExit(msg)

    messages = []
    for distribution_level in matching:
        destination = matching[distribution_level]
        if not (os.path.exists(destination) and os.path.isdir(destination)):
            msg = "The folder %s, mentioned in the configuration file,  does not exist" % destination
            log.critical(msg)
            messages.append(msg)
    if len(messages) > 0:
        raise SystemExit(messages)

    return root, matching, smtp_server, smtp_port, smtp_from, email_addresses, smtp_user, smtp_password


def load_json(filename):
    try:
        f = open(filename, 'r')
        data = json.load(f)
        f.close()
    except IOError as e:
        msg = "Impossible to read file %s; I/O error(%s): %s" % (filename, e.errno, e.strerror)
        log.critical(msg)
        raise SystemExit(msg)
    except ValueError as e:
        msg = "Impossible to load file %s; Value error: %s" % (filename, e)
        log.critical(msg)
        raise SystemExit(msg)
    except:
        msg = "Unexpected error: %s" % sys.exc_info()[0]
        log.critical(msg)
        raise SystemExit(msg)

    return data


def load_config():
    config = load_json(CONFIG_FILENAME)
    return validate_config(config)


def get_upload_folder(root, user, distribution_type):
    #e.g. /home/something/tooltool_root/bob/pvt
    return os.path.join(os.path.join(root, user), distribution_type)


def getDigests(manifest):
    manifest = tooltool.open_manifest(manifest)
    return [(x.digest, x.algorithm) for x in manifest.file_records]


def begins_with_timestamp(filename):
    p = re.compile(TIMESTAMP_REGEX)
    return p.match(filename)


class Notifier:

    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password, smtp_from, email_addresses):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.email_addresses = email_addresses
        print 'created object'

    def get_address(self, user):
        if user in self.email_addresses:
            return self.email_addresses[user]
        else:
            return "%s@mozilla.com" % user

    def sendmail(self, user_to_be_notified, subject, body):
        print "creating smtp object"
        s = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5)
        print "created smtlib object"
        s.starttls()
        s.login(self.smtp_user, self.smtp_password)
        print 'logged in'
        msg = MIMEText(body)
        recipients = []
        recipients.append(self.get_address(user_to_be_notified))
        # all notifications are also sent to the sync maintainer
        recipients.append(self.smtp_from)
        msg['Subject'] = subject
        msg['From'] = self.smtp_from
        msg['To'] = ", ".join(recipients)
        s.sendmail(self.smtp_from, recipients, msg.as_string())
        s.quit()


def main():
    print "validating config"

    root, matching, smtp_server, smtp_port, smtp_from, email_addresses, smtp_user, smtp_password = load_config()
    print "Config validated!"

    notifier = Notifier(smtp_server, smtp_port, smtp_user, smtp_password, smtp_from, email_addresses)

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
            new_manifests = [filename for filename in files if (filename.endswith(".tt") and not begins_with_timestamp(filename))]

            for new_manifest in new_manifests:
                new_manifest_path = os.path.join(upload_folder, new_manifest)
                destination = matching[distribution_type]
                timestamp = datetime.datetime.now().strftime(STRFRTIME)
                timestamped_manifest_name = "%s.%s" % (timestamp, new_manifest)

                comment_filename = new_manifest.replace(".tt", ".txt")
                comment_filepath = os.path.join(upload_folder, new_manifest.replace(".tt", ".txt"))

                manifestOK = True
                allFilesAreOK = True
                content_folder_path = new_manifest_path.replace(".tt", tooltool.TOOLTOOL_PACKAGE_SUFFIX)
                digests = ()
                try:
                    digests = getDigests(new_manifest_path)
                except tooltool.InvalidManifest:
                    manifestOK = False

                if manifestOK:
                    # checking that ALL files mentioned in the manifest are in the upload folder, otherwise I cannot proceed copying
                    if not os.path.exists(content_folder_path) or not os.path.isdir(content_folder_path):
                        allFilesAreOK = False
                        log.error("Impossible to process manifest %s because content has not been uploaded to folder" % content_folder_path)
                    else:
                        for digest, algorithm in digests:
                            digest_path = os.path.join(content_folder_path, digest)
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
                            digest_path = os.path.join(content_folder_path, digest)
                            comment = None

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
                            renamingOK = True
                            for digest, _algorithm in digests:
                                try:
                                    os.rename(os.path.join(destination, "temp%s" % digest), os.path.join(destination, digest))
                                except:
                                    log.error("Impossible to rename file %s to %s;" % (os.path.join(destination, "temp%s" % digest), os.path.join(destination, digest)))
                                    renamingOK = False

                            if renamingOK:
                                for digest, _algorithm in digests:
                                    # update digest with new manifest dealing with it
                                    with open("%s.MANIFESTS" % digest, 'a') as file:
                                        stored_manifest_name = "%s.%s.%s" % (user, distribution_type, timestamped_manifest_name)
                                        file.write("%s\n" % stored_manifest_name)
                                # if renaming is not successful, there's probably some problem in the upload server

                                # keep a local copy of the processed manifest
                                shutil.copy(new_manifest_path, os.path.join(os.getcwd(), stored_manifest_name))

                                if os.path.exists(comment_filepath):
                                    shutil.copy(comment_filepath, os.path.join(os.getcwd(), "%s.%s.%s.%s" % (user, distribution_type, timestamp, comment_filename)))

                                #rename original comment file
                                os.rename(comment_filepath, os.path.join(upload_folder, "%s.%s" % (timestamp, comment_filename)))

                                # rename original manifest name
                                os.rename(new_manifest_path, os.path.join(upload_folder, timestamped_manifest_name))
                        else:
                            #TODO: cleanup removing copied files beginning with "temp"
                            pass

                if manifestOK and allFilesAreOK:
                    if copyOK:
                        if renamingOK:
                            # cleaning up source directory of copied files
                            shutil.rmtree(content_folder_path)
                            notifier.sendmail(user, "TOOLTOOL UPLOAD COMPLETED! Tooltool package %s has been correctly processed by the tooltool sync script!" % new_manifest, "")
                        else:
                            notifier.sendmail("", "INTERNAL ERROR - sync script could not rename files in package %s" % new_manifest, "")
                    else:
                        notifier.sendmail("", "INTERNAL ERROR - sync script could not copy files in package %s" % new_manifest, "")
                        # TODO: notify internal error both to uploader and to sync maintainer
                else:
                    # general cleanup: the uploader will need to re-upload the package
                    if os.path.exists(content_folder_path):
                        shutil.rmtree(content_folder_path)
                    os.remove(comment_filepath)
                    os.remove(new_manifest_path)
                    #TODO: notify error to user: a new upload needs to be made!
                    log.error("Manifest %s has NOT been processed and will need to be re-uploaded by the user" % new_manifest)
                    msg = "Dear tooltool user,\n\nThe upload of the tooltool package %s was unsuccessful because of the following reason:\n\n" % new_manifest
                    if not manifestOK:
                        msg = msg + "- The uploaded manifest was invalid and could not be correctly parsed.\n"
                    if not allFilesAreOK:
                        msg = msg + "- Some of the files mentioned in the manifest were either missing or their content was corrupted.\n"
                    msg = msg+"\nPlease try again with a new upload.\n\n"
                    msg = msg + "Kind regards,\n\nThe Tooltool sync script"
                    notifier.sendmail(user, "TOOLTOOL UPLOAD FAILURE! - the tooltool sync script could not process manifest %s" % new_manifest, msg)

if __name__ == "__main__":
    main()
