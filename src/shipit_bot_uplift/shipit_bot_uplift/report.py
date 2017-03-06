from shipit_bot_uplift import log
import taskcluster
import operator
import itertools


logger = log.get_logger('shipit_bot')


class Report(object):
    """
    Build a report during bot execution
    and send it at the end through TC emails
    """

    def __init__(self, tc_options, emails):
        self.notify = taskcluster.Notify(tc_options)
        self.emails = emails
        self.merges = set()
        logger.info('Report notifications', emails=self.emails)

    def add_invalid_merge(self, merge_test):
        """
        Mark a bug with an invalid merged test
        """
        self.merges.add(merge_test)

    def send(self):
        """
        Build and send report using Taskcluster notification service
        """
        # Skip sending when there are no failed merges
        if not self.merges:
            logger.info('Nothing to report.')
            return

        def _str(x):
            return isinstance(x, bytes) and x.decode('utf-8') or x

        # Build markdown output
        # Sorting failed merge tests by bugzilla id & branch
        subject = 'Uplift bot detected some merge failures'
        mail = [
            '# Failed automated merge test',
            ''
        ]
        cmp_func = operator.attrgetter('bugzilla_id', 'branch')
        merges = sorted(self.merges, key=cmp_func)
        merges = itertools.groupby(merges, key=cmp_func)
        for keys, failures in merges:
            bz_id, branch = keys
            mail.append('## Bug [{0}](https://bugzil.la/{0}) - Uplift to {1}\n'.format(bz_id, _str(branch)))  # noqa
            for merge_test in failures:
                mail += [
                    ' * Merge failed for commit `{}` (parent `{}`)'.format(
                        _str(merge_test.revision),
                        _str(merge_test.revision_parent)
                    ),
                    '```\n{}```'.format(merge_test.message)
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
