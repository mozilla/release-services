import errno
import os
from datetime import datetime
import requests
import subprocess
import hglib

from cli_common.taskcluster import TaskclusterClient
from cli_common.log import get_logger

from shipit_code_coverage import taskcluster
from shipit_code_coverage import uploader
from shipit_code_coverage import coverage_by_dir


logger = get_logger(__name__)

COVERALLS_TOKEN_FIELD = 'SHIPIT_CODE_COVERAGE_COVERALLS_TOKEN'
CODECOV_TOKEN_FIELD = 'SHIPIT_CODE_COVERAGE_CODECOV_TOKEN'


class CodeCov(object):
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
        r = requests.get(url % mercurial_commit)

        return r.text.split(' ')[0]

    def generate_info(self, commit_sha, suite, coveralls_token):
        files = os.listdir('ccov-artifacts')
        ordered_files = []
        for fname in files:
            if not fname.endswith('.zip'):
                continue

            if 'gcno' in fname:
                ordered_files.insert(0, 'ccov-artifacts/' + fname)
            elif suite in fname:
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
          '--service-job-number', str(self.suites.index(suite) + 1),
          '--commit-sha', commit_sha,
          '--token', coveralls_token,
        ]
        cmd.extend(ordered_files)

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = p.communicate()

        if p.returncode != 0:
            raise Exception('Error while running grcov:\n' + err.decode('utf-8'))

        return output

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

    def run_command(self, cmd):
        """
        Run a command in the repo through subprocess
        """
        # Use gecko-env to run command
        cmd = ['gecko-env', ] + cmd

        # Run command with env
        logger.info('Running repo command', cmd=' '.join(cmd))
        proc = subprocess.Popen(cmd, cwd=self.repo_dir)
        exit = proc.wait()

        if exit != 0:
            raise Exception('Invalid exit code for command {}: {}'.format(cmd, exit))

    def build_files(self):
        with open(os.path.join(self.repo_dir, '.mozconfig'), 'w') as f:
            f.write('mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-firefox')

        self.run_command(['./mach', 'configure'])
        self.run_command(['./mach', 'build', 'pre-export'])
        self.run_command(['./mach', 'build', 'export'])

    def go(self):
        task_id = taskcluster.get_last_task()

        task_data = taskcluster.get_task_details(task_id)
        revision = task_data['payload']['env']['GECKO_HEAD_REV']
        logger.info('Revision %s' % revision)
        commit_sha = self.get_github_commit(revision)
        logger.info('GitHub revision %s' % commit_sha)

        self.download_coverage_artifacts(task_id)

        self.clone_mozilla_central(revision)
        self.build_files()

        coveralls_jobs = []

        # TODO: Process suites in parallel.
        # While we are uploading results for a suite, we can start to process the next one.
        for suite in self.suites:
            output = self.generate_info(commit_sha, suite, self.coveralls_token)

            print('suite generated ' + suite)

            coveralls_jobs.append(uploader.coveralls(output))
            uploader.codecov(output, commit_sha, [suite.replace('-', '_')], self.codecov_token)

        # Wait until the build has been injested by Coveralls.
        for coveralls_job in coveralls_jobs:
            uploader.coveralls_wait(coveralls_job)

        coverage_by_dir.generate(self.repo_dir)

    def __init__(self, cache_root, secrets, client_id=None, client_token=None):
        # List of test-suite, sorted alphabetically.
        # This way, the index of a suite in the array should be stable enough.
        self.suites = []

        assert os.path.isdir(cache_root), "Cache root {} is not a dir.".format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        tc_client = TaskclusterClient(client_id, client_token)

        required_fields = [COVERALLS_TOKEN_FIELD, CODECOV_TOKEN_FIELD]
        secrets = tc_client.get_secrets(secrets, required_fields)

        self.coveralls_token = secrets[COVERALLS_TOKEN_FIELD]
        self.codecov_token = secrets[CODECOV_TOKEN_FIELD]
