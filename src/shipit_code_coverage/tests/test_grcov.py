# -*- coding: utf-8 -*-
from shipit_code_coverage import grcov
import json
import os
import click
import pytest


def test_report_invalid_output_format(grcov_artifact):
    with pytest.raises(click.exceptions.ClickException, message='`grcov` failed with code: 1.'):
        grcov.report([grcov_artifact], out_format='UNSUPPORTED')


def test_report_grcov_artifact(grcov_artifact):
    output = grcov.report([grcov_artifact], out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    assert report['repo_token'] == 'unused'
    assert report['service_name'] == 'TaskCluster'
    assert report['service_job_number'] == '1'
    assert report['git']['branch'] == 'master'
    assert report['git']['head']['id'] == 'unused'
    assert report['service_number'] == ''
    assert len(report['source_files']) == 1
    assert report['source_files'][0]['name'] == 'js/src/jit/BitSet.cpp'
    assert report['source_files'][0]['coverage'] == [42, 42]
    assert report['source_files'][0]['branches'] == []
    assert 'source_digest' in report['source_files'][0]
    assert 'functions' not in report['source_files'][0]


def test_report_grcov_artifact_coverallsplus(grcov_artifact):
    output = grcov.report([grcov_artifact], out_format='coveralls+')
    report = json.loads(output.decode('utf-8'))
    assert report['repo_token'] == 'unused'
    assert report['service_name'] == 'TaskCluster'
    assert report['service_job_number'] == '1'
    assert report['git']['branch'] == 'master'
    assert report['git']['head']['id'] == 'unused'
    assert report['service_number'] == ''
    assert len(report['source_files']) == 1
    assert report['source_files'][0]['name'] == 'js/src/jit/BitSet.cpp'
    assert report['source_files'][0]['coverage'] == [42, 42]
    assert report['source_files'][0]['branches'] == []
    assert 'source_digest' in report['source_files'][0]
    assert len(report['source_files'][0]['functions']) == 1
    assert report['source_files'][0]['functions'][0]['exec']
    assert report['source_files'][0]['functions'][0]['name'] == '_ZNK2js3jit6BitSet5emptyEv'
    assert report['source_files'][0]['functions'][0]['start'] == 1


def test_report_jsvm_artifact(jsvm_artifact):
    output = grcov.report([jsvm_artifact], out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    assert report['repo_token'] == 'unused'
    assert report['service_name'] == 'TaskCluster'
    assert report['service_job_number'] == '1'
    assert report['git']['branch'] == 'master'
    assert report['git']['head']['id'] == 'unused'
    assert report['service_number'] == ''
    assert len(report['source_files']) == 1
    assert report['source_files'][0]['name'] == 'toolkit/components/osfile/osfile.jsm'
    assert report['source_files'][0]['coverage'] == [42, 42]
    assert report['source_files'][0]['branches'] == []
    assert 'source_digest' in report['source_files'][0]
    assert 'functions' not in report['source_files'][0]


def test_report_multiple_artifacts(grcov_artifact, jsvm_artifact):
    output = grcov.report([grcov_artifact, jsvm_artifact], out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    assert report['repo_token'] == 'unused'
    assert report['service_name'] == 'TaskCluster'
    assert report['service_job_number'] == '1'
    assert report['git']['branch'] == 'master'
    assert report['git']['head']['id'] == 'unused'
    assert report['service_number'] == ''
    assert len(report['source_files']) == 2
    assert set(['toolkit/components/osfile/osfile.jsm', 'js/src/jit/BitSet.cpp']) == set([sf['name'] for sf in report['source_files']])


def test_report_source_dir(grcov_artifact, grcov_existing_file_artifact):
    output = grcov.report([grcov_existing_file_artifact], source_dir=os.getcwd(), out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    # When we pass the source directory to the report function, grcov ignores not-existing files.
    assert len(report['source_files']) == 1
    assert report['source_files'][0]['name'] == 'shipit_code_coverage/cli.py'
    # When we pass the source directory to grcov and the file exists, grcov can calculate its hash.
    assert report['source_files'][0]['source_digest'] == '1a1c4cac2d925795713415a7a00cec40'


def test_report_service_number(grcov_artifact):
    output = grcov.report([grcov_artifact], service_number='test', out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    assert report['service_number'] == 'test'


def test_report_commit_sha(grcov_artifact):
    output = grcov.report([grcov_artifact], commit_sha='test', out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    assert report['git']['head']['id'] == 'test'


def test_report_token(grcov_artifact):
    output = grcov.report([grcov_artifact], token='test', out_format='coveralls')
    report = json.loads(output.decode('utf-8'))
    assert report['repo_token'] == 'test'


def test_report_options(grcov_artifact, jsvm_artifact):
    output = grcov.report([grcov_artifact, jsvm_artifact], out_format='coveralls', options=['--ignore-dir', 'toolkit'])
    report = json.loads(output.decode('utf-8'))
    assert len(report['source_files']) == 1
    assert report['source_files'][0]['name'] == 'js/src/jit/BitSet.cpp'


def test_files_list(grcov_artifact, grcov_uncovered_artifact):
    files = grcov.files_list([grcov_artifact, grcov_uncovered_artifact])
    assert set(files) == set(['js/src/jit/BitSet.cpp'])


def test_files_list_source_dir(grcov_artifact, grcov_existing_file_artifact):
    files = grcov.files_list([grcov_artifact, grcov_existing_file_artifact], source_dir=os.getcwd())
    assert set(files) == set(['shipit_code_coverage/cli.py'])
