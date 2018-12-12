# -*- coding: utf-8 -*-
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def test_amend(repository):
    '''
    Test amending last commit message using regexes
    '''

    # Check initial tip
    tip = repository.client.tip()
    assert tip.rev == b'4'
    assert tip.desc == b'commit #4'

    # Rename tip with regexes
    rev, commit = repository.amend(', amending test.')
    assert rev == 4

    # Check new tip
    tip = repository.client.tip()
    assert tip.rev == b'4'
    assert tip.desc == b'commit #4, amending test.'


def test_regex_identify():
    '''
    Test the regex used to parse identify() outpuy
    '''
    from uplift_bot.mercurial import REGEX_IDENTIFY

    def _check(identify, result):
        output = REGEX_IDENTIFY.match(identify)
        assert result == (output and output.groups())

    _check(
        'deadbeef (dummy-test) tip\n',
        ('deadbeef', 'dummy-test', 'tip'),
    )

    _check(
        '7980e4a53ef7 (uplift-beta-1413643) tip beta\n',
        ('7980e4a53ef7', 'uplift-beta-1413643', 'beta'),
    )

    _check(
        '7980e4a53ef7 (uplift-beta-1413643) beta\n',
        ('7980e4a53ef7', 'uplift-beta-1413643', 'beta'),
    )

    _check(
        'de336078d36b tip esr52\n',
        ('de336078d36b', 'tip', 'esr52'),
    )
