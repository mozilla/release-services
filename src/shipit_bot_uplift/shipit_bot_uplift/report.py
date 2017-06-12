from cli_common.log import get_logger
from cli_common.taskcluster import get_service
import operator
import itertools


logger = get_logger(__name__)


class Report(object):
    """
    Build a report during bot execution
    and send it at the end through TC emails
    """

    def __init__(self, emails):
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

        def _commit_report(revision, result):
            fail_fmt = ' * Merge failed for commit `{}` (parent `{}`)\n\n```\n{}```'  # noqa
            default_fmt = ' * Merge {} for commit `{}`'
            if result.status == 'failed':
                return fail_fmt.format(
                    _str(revision),
                    _str(result.parent),
                    result.message,
                )

            else:
                return default_fmt.format(result.status, _str(revision))

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
                    _commit_report(revision, result)
                    for revision, result in merge_test.results.items()
                ]
            mail.append('')  # newline
        mail_md = '\n'.join(mail)

        # Send mail report to every mail address
        notify = get_service('notify')
        for email in self.emails:
            notify.email({
                'address': email,
                'subject': subject,
                'content': mail_md,
                'template': 'fullscreen',
            })
            logger.info('Sent report', to=email)
