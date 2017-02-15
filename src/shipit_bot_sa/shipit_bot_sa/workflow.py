import base64
import re
import json
from urllib.request import urlopen
from bot_common.pulse import create_consumer, run_consumer
from bot_common.taskcluster import TaskclusterClient
from libmozdata import bugzilla

import asyncio

MOZREVIEW_URL_PATTERN = 'https://reviewboard.mozilla.org/r/([0-9]+)/'

import pdb


class PulseWorkflow(object):
    """
    Main bot workflow
    """
    def __init__(self, secrets_path, client_id=None, access_token=None):

        # Fetch pulse credentials from TC secrets
        self.tc = TaskclusterClient(client_id, access_token)
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

        # Show we got something
        print("Trying to match a mozreview with Id: {}".format(bugzilla_id))

        # Analyse the attachment of the bug
        fields = ['id', 'data', 'is_obsolete', 'creation_time', 'content_type']
        bugzilla.Bugzilla(
            bugzilla_id,
            attachmenthandler=self.attachmenthandler,
            attachment_include_fields=fields
        ).get_data()

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    def commenthandler(self, data, bugid):
        bug = {
            'id': bugid,
            'comments': data['comments'],
        }

        commits, _ = patchanalysis.get_commits_for_bug(bug)

        if len(commits):
            print(commits)
        else:
            print("No patches found")

    def attachmenthandler(self, attachments, bugid):
        bug = {
            'id': bugid,
            'attachments': attachments
        }

        for attachment in bug['attachments']:
            data = None

            if attachment['content_type'] == 'text/x-review-board-request' and attachment['is_obsolete'] == 0:  # noqa

                mozreview_url = base64.b64decode(attachment['data']).decode('utf-8')  # noqa

                review_num = re.search(MOZREVIEW_URL_PATTERN, mozreview_url).group(1)  # noqa
                diff_url = 'https://reviewboard.mozilla.org/r/{}/diff/raw/'.format(review_num)  # noqa

                response = urlopen(diff_url)
                data = response.read().decode('ascii', 'ignore')

                # Print the patch diff
                print(data)
