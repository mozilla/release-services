# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tarfile
import requests
import io
import os
import cli_common.utils


def setup(job_name='linux64-infer', revision='latest',
          artifact='public/build/infer.tar.xz'):
    '''
    Setup Taskcluster infer build for static-analysis
    Defaults values are from https://dxr.mozilla.org/mozilla-central/source/taskcluster/ci/toolchain/linux.yml
    - Download the artifact from latest Taskcluster build
    - Extracts it into the MOZBUILD_STATE_PATH as expected by mach
    '''
    NAMESPACE = 'gecko.cache.level-1.toolchains.v2.{}.{}'
    import taskcluster
    index = taskcluster.Index(
        {'credentials': {'clientId': os.getenv('TASKCLUSTER_CLIENT_ID'),
                         'accessToken': os.getenv('TASKCLUSTER_ACCESS_TOKEN')}}
    )
    if job_name == 'linux64-infer':
        job_names = ['linux64-infer', 'linux64-android-sdk-linux-repack',
                     'linux64-android-ndk-linux-repack']
        artifacts = ['public/build/infer.tar.xz',
                     'project/gecko/android-sdk/android-sdk-linux.tar.xz',
                     'project/gecko/android-ndk/android-ndk.tar.xz']
        for i in range(len(job_names)):
            namespace = NAMESPACE.format(job_names[i], revision)
            artifact_url = index.buildSignedUrl('findArtifactFromTask',
                                                indexPath=namespace,
                                                name=artifacts[i])
            target = os.path.join(
                os.environ['MOZBUILD_STATE_PATH'],
                os.path.basename(artifacts[i]).split('.')[0],
            )
            cli_common.utils.retry(lambda: download(artifact_url, target))


def download(artifact_url, target):
    # Download Taskcluster archive
    resp = requests.get(artifact_url, stream=True)
    resp.raise_for_status()

    # Extract archive into destination
    with tarfile.open(fileobj=io.BytesIO(resp.content)) as tar:
        tar.extractall(target)
