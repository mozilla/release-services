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

    def add_invalid_merge(self, merge_test):
        """
        Mark a bug with an invalid merged test
        """
        if merge_test.bugzilla_id not in self.merges:
            self.merges[merge_test.bugzilla_id] = []
        self.merges[merge_test.bugzilla_id].append(merge_test)

    def send(self):
        """
        Build and send report using Taskcluster notification service
        """
        # Skip sending when there are no failed merges
        if not self.merges:
            return

        # Build markdown output
        subject = 'Uplift bot detected some merge failures'
        mail = [
            '# Failed automated merge test',
            ''
        ]
        for bz_id, failures in self.merges.items():
            mail.append('## Bug [{0}](https://bugzil.la/{0})\n'.format(bz_id))
            mail += [
                ' * Merge failed on branch {}@{} for commit {} : {}'.format(merge_test.branch, merge_test.revision_parent, merge_test.revision, merge_test.message)  # noqa
                for merge_test in failures
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
