# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from cli_common import log
from rbtools.api.errors import APIError
from rbtools.api.client import RBClient

logger = log.get_logger(__name__)


def build_api_root(url, username, api_key):
    '''
    Helper to build an RBTools api root
    used by BatchReview
    '''
    logger.info('Authenticate on Mozreview', url=url, username=username)
    client = RBClient(url, save_cookies=False, allow_caching=False)
    login_resource = client.get_path(
        'extensions/mozreview.extension.MozReviewExtension/'
        'bugzilla-api-key-logins/'
    )
    login_resource.create(username=username, api_key=api_key)
    return client.get_root()


class BatchReview(object):
    '''Create a review and comments with a single API call

    Using BatchReview is much faster than creating a review and comments
    with individual API calls.
    '''

    def __init__(self, api_root, review_request_id, diff_revision,
                 max_comments=100):
        '''Initialize BatchReview

        The ``api_root`` is the result of calling get_root on a Reviewboard
        client.

        The ``review_request_id`` is the integer identifier of the review
        request on which to leave the review.

        The ``diff_revision`` is the integer identifier of the diff
        revision for which to leave the review.

        The ``max_comments`` provides a limit on the number of comments
        which can be made as part of the BatchReview.
        '''

        self.api_root = api_root
        self.review_request_id = review_request_id
        self.diff_revision = diff_revision
        self.max_comments = max_comments
        self.comments = []

        self._destfile_to_file = {}
        self._file_to_diffdata = {}

    def destfile_to_file(self, destfile):
        '''Map a path to a file object'''
        if not self._destfile_to_file:
            start = 0
            while True:
                files = self.api_root.get_files(
                    review_request_id=self.review_request_id,
                    diff_revision=self.diff_revision,
                    start=start)
                for f in files:
                    self._destfile_to_file[f.dest_file] = f
                start += files.num_items
                if files.num_items == 0 or start >= files.total_results:
                    break

        return self._destfile_to_file.get(destfile)

    def changed_lines_for_file(self, filename):
        '''Determine which lines changed in a file'''
        f = self.destfile_to_file(filename)
        diff_data = self._file_to_diffdata.setdefault(f, f.get_diff_data())

        chunks = diff_data.rsp['diff_data']['chunks']
        changed_lines = set()
        for chunk in chunks:
            if chunk['change'] not in ('insert', 'replace'):
                continue
            for line in chunk['lines']:
                changed_lines.add(int(line[4]))

        return changed_lines

    def translate_line_num(self, filename, line_num, original=False):
        '''Convert a file line number to a filediff line number.

        If original is True, will convert based on the original
        file numbers, instead of the patched.

        TODO: Convert to a faster search algorithm.
        '''
        f = self.destfile_to_file(filename)
        diff_data = self._file_to_diffdata.setdefault(f, f.get_diff_data())

        line_num_index = 4
        if original:
            line_num_index = 1

        for chunk in diff_data.chunks:
            for row in chunk.lines:
                if row[line_num_index] == line_num:
                    return row[0]

    def comment(self, filename, first_line, num_lines, text,
                issue_opened=True):
        '''Add a comment to the list of comments.'''

        f = self.destfile_to_file(filename)
        if f is None:
            logger.error('batchreview: could not comment on file: %s it does '
                         'not appear to be part of the commit.' %
                         filename)
            return
        translated_line_num = self.translate_line_num(filename, first_line)

        data = {
            'filediff_id': f.id,
            'first_line': translated_line_num,
            'num_lines': num_lines,
            'text': text,
            'issue_opened': issue_opened,
        }
        self.comments.append(data)

    def publish(self, body_top='', body_bottom='', ship_it=False):
        '''Publish the review to Reviewboard.'''

        # Truncate comments to the maximum permitted amount to avoid
        # overloading the review and freezing the browser.
        if len(self.comments) > self.max_comments:
            warning = ('WARNING: Number of comments exceeded maximum, showing '
                       '%d of %d.') % (self.max_comments, len(self.comments))
            body_top = '%s\n%s' % (body_top, warning)
            del self.comments[self.max_comments:]

        try:
            batch_reviews = self.api_root.get_extension(
                extension_name='mozreview.extension.MozReviewExtension'
                ).get_batch_reviews()

            batch_reviews.create(
                review_request_id=self.review_request_id,
                ship_it=ship_it,
                body_top=body_top,
                body_bottom=body_bottom,
                diff_comments=json.dumps(self.comments))
        except APIError as e:
            logger.error('batchreview: could not publish review: %s' % str(e))
            return False

        return True
