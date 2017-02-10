from shipit_bot_uplift import log
import taskcluster


logger = log.get_logger('shipit_bot')


class Report(object):
    """
    Build a report during bot execution
    and send it at the end through TC emails
    """

    def __init__(self, tc_options, emails):
        self.notify = taskcluster.Notify(tc_options)
        self.emails = emails
        self.merges = {}

    def add_invalid_merge(self, bugzilla_id, branch, revision, revision_parent):  # noqa
        """
        Mark a bug with an invalid merged test
        """
        if bugzilla_id not in self.merges:
            self.merges[bugzilla_id] = []
        self.merges[bugzilla_id].append((branch, revision, revision_parent))

    def send(self):
        """
        Build and send report using Taskcluster notification service
        """
        # Build markdown output
        subject = 'Uplift bot detected some merge failures'
        mail = [
            '# Failed automated merge test',
            ''
        ]
        for bz_id, failures in self.merges.items():
            mail.append('## Bug [{0}](https://bugzil.la/{0})\n'.format(bz_id))
            mail += [
                ' * Merge failed on branch {}@{} for commit {}'.format(branch, revision_parent, revision)  # noqa
                for branch, revision, revision_parent in failures
            ]
            mail.append('')  # newline
        mail_md = '\n'.join(mail)

        # Send mail report to every mail address
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': subject,
                'content': mail_md
            })
            logger.info('Sent report', to=email)
