# -*- coding: utf-8 -*-

import shutil

from code_coverage_bot.utils import run_check


def test_mercurial():
    '''
    Test mercurial versions & extensions
    '''
    assert shutil.which('hg'), 'Missing mercurial'

    # Check mercurial version
    output = run_check(['hg', 'version', '-T', '{ver}'])
    assert output.decode('utf-8').startswith('4.8')

    # Check needed extensions
    output = run_check(['hg', 'version', '-T', '{extensions}'])
    extensions = output.decode('utf-8').split('\n')
    assert 'hgmo' in extensions
    assert 'pushlog' in extensions
    assert 'robustcheckout' in extensions


def test_grcov():
    '''
    Test grcov is available on the system
    '''
    assert shutil.which('grcov'), 'Missing grcov'


def test_genhtml():
    '''
    Test genhtml is available on the system
    '''
    assert shutil.which('genhtml'), 'Missing genhtml'
