import errno
import os
from datetime import datetime
import requests
import hglib

from cli_common.log import get_logger
from cli_common.command import run_check

from shipit_code_coverage import coverage_by_dir, taskcluster, uploader, utils


logger = get_logger(__name__)


class CodeCov(object):

    def __init__(self, cache_root, coveralls_token, codecov_token):
        # List of test-suite, sorted alphabetically.
        # This way, the index of a suite in the array should be stable enough.
        self.suites = []

        assert os.path.isdir(cache_root), "Cache root {} is not a dir.".format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        self.coveralls_token = coveralls_token
        self.codecov_token = codecov_token

    def download_coverage_artifacts(self, build_task_id):
        try:
            os.mkdir('ccov-artifacts')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        task_data = taskcluster.get_task_details(build_task_id)

        artifacts = taskcluster.get_task_artifacts(build_task_id)
        for artifact in artifacts:
            if 'target.code-coverage-gcno.zip' in artifact['name']:
                taskcluster.download_artifact(build_task_id, '', artifact)

        all_suites = set()

        tasks = taskcluster.get_tasks_in_group(task_data['taskGroupId'])
        test_tasks = [t for t in tasks if taskcluster.is_coverage_task(t)]
        for test_task in test_tasks:
            suite_name = taskcluster.get_suite_name(test_task)
            all_suites.add(suite_name)
            test_task_id = test_task['status']['taskId']
            artifacts = taskcluster.get_task_artifacts(test_task_id)
            for artifact in artifacts:
                if 'code-coverage-gcda.zip' in artifact['name']:
                    taskcluster.download_artifact(test_task_id, suite_name, artifact)

        self.suites = list(all_suites)
        self.suites.sort()

    def get_github_commit(self, mercurial_commit):
        url = 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/%s'

        def get_commit():
            r = requests.get(url % mercurial_commit)

            if r.status_code == requests.codes.ok:
                return r.text.split(' ')[0]

            return None

        ret = utils.wait_until(get_commit)
        if ret is None:
            raise Exception('Mercurial commit is not available yet on mozilla/gecko-dev.')
        return ret

    def generate_info(self, commit_sha, coveralls_token, suite=None):
        files = os.listdir('ccov-artifacts')
        ordered_files = []
        for fname in files:
            if not fname.endswith('.zip'):
                continue

            if 'gcno' in fname:
                ordered_files.insert(0, 'ccov-artifacts/' + fname)
            elif suite is None or suite in fname:
                ordered_files.append('ccov-artifacts/' + fname)

        cmd = [
          'grcov',
          '-z',
          '-t', 'coveralls',
          '-s', self.repo_dir,
          '-p', '/home/worker/workspace/build/src/',
          '--ignore-dir', 'gcc',
          '--ignore-not-existing',
          '--service-name', 'TaskCluster',
          '--service-number', datetime.today().strftime('%Y%m%d'),
          '--commit-sha', commit_sha,
          '--token', coveralls_token,
        ]

        if suite is not None:
            cmd.extend(['--service-job-number', str(self.suites.index(suite) + 1)])
        else:
            cmd.extend(['--service-job-number', '1'])

        cmd.extend(ordered_files)

        return run_check(cmd, cwd=os.getcwd())

    def clone_mozilla_central(self, revision):
        shared_dir = self.repo_dir + '-shared'
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    'https://hg.mozilla.org/mozilla-central',
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    branch=b'tip')

        cmd.insert(0, hglib.HGPATH)
        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        hg = hglib.open(self.repo_dir)

        hg.update(rev=revision, clean=True)

    def build_files(self):
        with open(os.path.join(self.repo_dir, '.mozconfig'), 'w') as f:
            f.write('mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-firefox')

        run_check(['gecko-env', './mach', 'configure'], cwd=self.repo_dir)
        run_check(['gecko-env', './mach', 'build', 'pre-export'], cwd=self.repo_dir)
        run_check(['gecko-env', './mach', 'build', 'export'], cwd=self.repo_dir)

    def go(self):
        task_id = taskcluster.get_last_task()

        task_data = taskcluster.get_task_details(task_id)
        revision = task_data['payload']['env']['GECKO_HEAD_REV']
        logger.info('Mercurial revision', revision=revision)

        self.download_coverage_artifacts(task_id)

        self.clone_mozilla_central(revision)
        self.build_files()

        commit_sha = self.get_github_commit(revision)
        logger.info('GitHub revision', revision=commit_sha)

        coveralls_jobs = []

        # TODO: Process suites in parallel.
        # While we are uploading results for a suite, we can start to process the next one.
        # TODO: Reenable when Coveralls and/or Codecov will be able to properly handle the load.
        '''for suite in self.suites:
            output = self.generate_info(commit_sha, self.coveralls_token, suite)

            logger.info('Suite report generated', suite=suite)

            coveralls_jobs.append(uploader.coveralls(output))
            uploader.codecov(output, commit_sha, self.codecov_token, [suite.replace('-', '_')])'''

        output = self.generate_info(commit_sha, self.coveralls_token)
        logger.info('Report generated successfully')

        coveralls_jobs.append(uploader.coveralls(output))
        uploader.codecov(output, commit_sha, self.codecov_token)

        logger.info('Waiting for build to be injested by Coveralls...')
        # Wait until the build has been injested by Coveralls.
        if all([uploader.coveralls_wait(job_url) for job_url in coveralls_jobs]):
            logger.info('Build injested by coveralls')
        else:
            logger.info('Coveralls took too much time to injest data.')

        coverage_by_dir.generate(self.repo_dir)
