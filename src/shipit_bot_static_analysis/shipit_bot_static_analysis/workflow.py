import base64
import re
import json
import warnings
import whatthepatch
import hglib
from urllib.request import urlopen
from cli_common.pulse import create_consumer, run_consumer
from cli_common.taskcluster import TaskclusterClient
from libmozdata import bugzilla

MOZREVIEW_URL_PATTERN = 'https://reviewboard.mozilla.org/r/([0-9]+)/'
REPO_DIR = ''


class PulseWorkflow(object):
    """
    Main bot workflow
    """
    def __init__(self, secrets_path, client_id=None, access_token=None):

        # Fetch pulse credentials from TC secrets
        self.tc = TaskclusterClient(client_id, access_token)

        # Save History and Attachment
        self.bug = {}

        # Mercurial repository
        self.repo = hglib.open(REPO_DIR)

        secrets = self.tc.get_secret(secrets_path)
        required = ('PULSE_USER', 'PULSE_PASSWORD', 'PULSE_QUEUE')
        for req in required:
            if req not in secrets:
                raise Exception('Missing value {} in Taskcluster secret value {}'.format(req, secrets_path))  # noqa

        # Use pulse consumer from bot_common
        self.consumer = create_consumer(
            secrets['PULSE_USER'],
            secrets['PULSE_PASSWORD'],
            secrets['PULSE_QUEUE'],
            secrets.get('PULSE_TOPIC', '#'),
            self.got_message
        )

    def run(self):
        run_consumer(self.consumer)

    async def got_message(self, channel, body, envelope, properties):
        """
        Pulse consumer callback
        """
        assert isinstance(body, bytes), \
            'Body is not in bytes'

        # Extract bugzilla id
        body = json.loads(body.decode('utf-8'))
        if 'payload' not in body:
            raise Exception('Missing payload in body')
        bugzilla_id = body['payload'].get('id')
        if not bugzilla_id:
            raise Exception('Missing bugzilla id')

        # Analyse the attachment of the bug
        fields = ['id', 'data', 'is_obsolete', 'creation_time',
                  'content_type']

        self.bug['id'] = bugzilla_id

        bugzilla.Bugzilla(
            bugzilla_id,
            historyhandler=self.historyHandler,
            attachmenthandler=self.attachmenthandler,
            attachment_include_fields=fields
        ).get_data().wait()

        self.analyzebug()

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    def historyHandler(self, found_bug):
        self.bug['history'] = found_bug['history']

    def attachmenthandler(self, attachments, bugid):
        self.bug['attachments'] = attachments

    def commenthandler(self, data, bugid):
        bug = {
            'id': bugid,
            'comments': data['comments'],
        }

        commits, _ = bugzilla.patchanalysis.get_commits_for_bug(bug)

    def analyzebug(self):
        attachmentId = 0
        attachmentData = None

        if len(self.bug['history']) < 1:
            warnings.warn("Bug: {} - History is empty!".format(self.bug['id']))
            return

        # begin with the history to see if the latest comment it's a attachment
        for changes in self.bug['history'][-1]['changes']:
            if 'attachment_id' in changes:
                attachmentId = changes['attachment_id']

        if attachmentId > 0:
            for attachment in self.bug['attachments']:
                if attachment['content_type'] == \
                        'text/x-review-board-request' and attachment[
                    'is_obsolete'] == 0 and attachment['id'] == attachmentId:  # noqa

                    mozreview_url = base64.b64decode(attachment['data']).decode('utf-8')  # noqa

                    review_num = re.search(MOZREVIEW_URL_PATTERN, mozreview_url).group(1)  # noqa
                    diff_url = 'https://reviewboard.mozilla.org/r/{}/diff/raw/'.format(review_num)  # noqa

                    response = urlopen(diff_url)
                    attachmentData = response.read().decode('ascii', 'ignore')

                    paths_list = []
                    for diff in whatthepatch.parse_patch(attachmentData):
                        old_path = (diff.header.old_path[2:]
                                    if diff.header.old_path.startswith('a/')
                                    else diff.header.old_path)
                        new_path = (diff.header.new_path[2:]
                                    if diff.header.new_path.startswith('b/')
                                    else diff.header.new_path)

                        # Pushing the new path to the list that's going to be
                        # used to pass it to the clang-tiy as argument
                        paths_list.append(new_path)
                        print(old_path)

            self.applypatch(attachmentData, paths_list)

    def applypatch(self, patch, patchFiles):

        # First revert everything and update
        result = self.repo.update(clean=True)

        # if result['updated']:
        #    print("{} Files Updated", format(result['updated']))

        return result
