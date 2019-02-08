# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tarfile
import requests
import io
import os
import cli_common.utils
from cli_common.command import run_check
from cli_common.log import get_logger
from static_analysis_bot import AnalysisException
from static_analysis_bot.config import settings


logger = get_logger(__name__)


def setup(
    product='static-analysis',
    job_name='linux64-clang-tidy',
    revision='latest',
    artifact='public/build/clang-tidy.tar.xz',
    repository='autoland',
):
    try:
        run_check(['gecko-env', './mach', 'artifact', 'toolchain',
                   '--from-build', 'linux64-clang-tidy'], cwd=settings.repo_dir)
    except Exception as ex:
        logger.warn('Artifact downloader for clang-tidy using mach failed with: {}'.format(str(ex)))
        '''
        In case artifact downloader failed when using 'mach' we try to do the setup manually.
        Defaults values are from https://dxr.mozilla.org/mozilla-central/source/taskcluster/ci/toolchain/linux.yml
        - Download the artifact from latest Taskcluster build
        - Extracts it into the MOZBUILD_STATE_PATH as expected by mach
        '''
        namespace = 'gecko.v2.{}.{}.{}.{}'.format(repository, revision, product, job_name)
        artifact_url = 'https://index.taskcluster.net/v1/task/{}/artifacts/{}'.format(namespace, artifact)

        # Mach expects clang binaries in this specific root dir
        target = os.path.join(
            os.environ['MOZBUILD_STATE_PATH'],
            'clang-tools',
        )

        def _download():
            # Download Taskcluster archive
            resp = requests.get(artifact_url, stream=True)
            if not resp.ok:
                raise AnalysisException('artifact', 'Download failed {}'.format(artifact_url))

            # Extract archive into destination
            with tarfile.open(fileobj=io.BytesIO(resp.content)) as tar:
                tar.extractall(target)

        # Retry several times the download process
        cli_common.utils.retry(_download)
