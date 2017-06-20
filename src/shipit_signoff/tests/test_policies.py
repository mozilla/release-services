# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock

from shipit_signoff.policies import (
    UnauthorizedUserError, NoSignoffLeftError, check_whether_policy_can_be_signed,
    _is_group_defined_in_policy, _is_email_defined_in_policy, _are_there_signoffs_left_for_group,
    _are_there_signoffs_left_for_email, is_sign_off_policy_met, _is_signoff_condition_met,
    _calculate_missing_signoffs, _has_user_signed_policy, NoSignaturePresentError,
    check_whether_policy_can_be_unsigned)


@pytest.mark.parametrize('email, group_name, policy, existing_signatures', (
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 1}],
        [],
    ),
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        'a-relman@m.c',
        'relman',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng'), MagicMock(email='another-releng@m.c', group='releng')],
    ),
    (
        'super-admin@m.c',
        'non-important',
        [{'releng': 2, 'relman': 1}, {'super-admin@m.c': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng'), MagicMock(email='another-releng@m.c', group='releng')],
    ),
))
def test_check_whether_policy_can_be_signed(email, group_name, policy, existing_signatures):
    check_whether_policy_can_be_signed(email, group_name, policy, existing_signatures)


@pytest.mark.parametrize('email, group_name, policy, existing_signatures, expected_exception', (
    (
        'a-valid-releng@m.c',
        'releng',
        [{'relman': 1, 'qe': 1}],
        [],
        UnauthorizedUserError,
    ),
    (
        'qe@m.c',
        'qe',
        [{'releng': 2}, {'relman': 1}],
        [],
        UnauthorizedUserError,
    ),
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 1, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
        NoSignoffLeftError,
    ),
))
def test_error_check_whether_policy_can_be_signed(email, group_name, policy, existing_signatures, expected_exception):
    with pytest.raises(expected_exception):
        check_whether_policy_can_be_signed(email, group_name, policy, existing_signatures)


@pytest.mark.parametrize('group, policy', (
    ('releng', [{'releng': 1}]),
    ('releng', [{'relman': 1}, {'releng': 2}]),
    ('releng', [{'releng': 2}, {'releng': 1, 'relman': 1}]),
    ('releng', [{'super-admin@m.c': 1}, {'releng': 1, 'relman': 1}]),
))
def test_is_group_defined_in_policy(group, policy):
    assert _is_group_defined_in_policy(group, policy)


@pytest.mark.parametrize('group, policy', (
    ('releng', [{}]),
    ('releng', [{'relman': 1}]),
    ('releng', [{'relman': 1}, {'qe': 1}]),
    ('releng', [{'relman': 1}, {'super-admin@m.c': 1}]),
))
def test_not_is_group_defined_in_policy(group, policy):
    assert not _is_email_defined_in_policy(group, policy)


@pytest.mark.parametrize('email, policy', (
    ('super-admin@m.c', [{'super-admin@m.c': 1}]),
    ('super-admin@m.c', [{'super-admin@m.c': 1}, {'releng': 2}]),
    ('super-admin@m.c', [{'releng': 2}, {'super-admin@m.c': 1, 'relman': 1}]),
))
def test_is_email_defined_in_policy(email, policy):
    assert _is_email_defined_in_policy(email, policy)


@pytest.mark.parametrize('email, policy', (
    ('a-valid-releng@m.c', [{}]),
    ('a-valid-releng@m.c', [{'relman': 1}, {'super-admin@m.c': 1}]),
    ('a-valid-releng@m.c', [{'releng': 1}]),
    ('a-valid-releng@m.c', [{'relman': 1}, {'releng': 2}]),
    ('a-valid-releng@m.c', [{'releng': 2}, {'releng': 1, 'relman': 1}]),
))
def test_not_is_email_defined_in_policy(email, policy):
    assert not _is_group_defined_in_policy(email, policy)


@pytest.mark.parametrize('group_name, policy, existing_signatures', (
    (
        'releng',
        [{'releng': 1}],
        [],
    ),
    (
        'releng',
        [{'relman': 1}, {'releng': 2}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        'releng',
        [{'releng': 2}, {'releng': 1, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
))
def test_are_there_signoffs_left_for_group(group_name, policy, existing_signatures):
    assert _are_there_signoffs_left_for_group(group_name, policy, existing_signatures)


@pytest.mark.parametrize('group_name, policy, existing_signatures', (
    (
        'releng',
        [{}],
        []
    ),
    (
        'releng',
        [{'relman': 1}, {'super-admin@m.c': 1}],
        []
    ),
    (
        'releng',
        [{'relman': 1}, {'releng': 0}],
        []
    ),
    (
        'releng',
        [{'releng': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
))
def test_not_are_there_signoffs_left_for_group(group_name, policy, existing_signatures):
    assert not _are_there_signoffs_left_for_group(group_name, policy, existing_signatures)


@pytest.mark.parametrize('email, policy, existing_signatures', (
    (
        'super-admin@m.c',
        [{'releng': 1, 'super-admin@m.c': 1}],
        [],
    ),
))
def test_are_there_signoffs_left_for_email(email, policy, existing_signatures):
    assert _are_there_signoffs_left_for_email(email, policy, existing_signatures)


@pytest.mark.parametrize('email, policy, existing_signatures', (
    (
        'super-admin@m.c',
        [{}],
        []
    ),
    (
        'super-admin@m.c',
        [{'relman': 1}],
        []
    ),
    (
        'super-admin@m.c',
        [{'relman': 1}, {'super-admin@m.c': 0}],
        []
    ),
    (
        'super-admin@m.c',
        [{'releng': 1}, {'super-admin@m.c': 1}],
        [MagicMock(email='super-admin@m.c', group='non-important')],
    ),
))
def test_not_are_there_signoffs_left_for_email(email, policy, existing_signatures):
    assert not _are_there_signoffs_left_for_email(email, policy, existing_signatures)


@pytest.mark.parametrize('policy, existing_signatures', (
    (
        [{}],
        [MagicMock(email='not-important@m.c', group='not-important')],
    ),
    (
        [{'releng': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        [{'releng': 2}, {'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng'), MagicMock(email='a-relman@m.c', group='relman')],
    ),
    (
        [{'releng': 2}, {'super-admin@m.c': 1}],
        [MagicMock(email='super-admin@m.c', group='relman')],
    ),
))
def test_is_sign_off_policy_met(policy, existing_signatures):
    assert is_sign_off_policy_met(policy, existing_signatures)


@pytest.mark.parametrize('policy, existing_signatures', (
    (
        [{'relman': 1}, {'qe': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        [{'releng': 2}, {'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
))
def test_not_is_sign_off_policy_met(policy, existing_signatures):
    assert not is_sign_off_policy_met(policy, existing_signatures)


@pytest.mark.parametrize('signoff_condition', (
    {},
    {'releng': 0},
    {'releng': 0, 'relman': 0},
))
def test_is_signoff_condition_met(signoff_condition):
    assert _is_signoff_condition_met(signoff_condition)


@pytest.mark.parametrize('signoff_condition', (
    {'releng': 1},
    {'releng': 1, 'relman': 0},
))
def test_not_is_signoff_condition_met(signoff_condition):
    assert not _is_signoff_condition_met(signoff_condition)


@pytest.mark.parametrize('policy, existing_signatures, expected', (
    (
        [{}],
        [MagicMock(email='not-important@m.c', group='not-important')],
        [{}],
    ),
    (
        [{'releng': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
        [{'releng': 0}],
    ),
    (
        [{'relman': 1}, {'qe': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
        [{'relman': 1}, {'qe': 1}],
    ),
    (
        [{'releng': 2}, {'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
        [{'releng': 1}, {'relman': 1}],
    ),
    (
        [{'releng': 2}, {'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng'), MagicMock(email='a-relman@m.c', group='relman')],
        [{'releng': 1}, {'relman': 0}],
    ),
    (
        [{'releng': 2}, {'super-admin@m.c': 1}],
        [MagicMock(email='super-admin@m.c', group='relman')],
        [{'releng': 2}, {'super-admin@m.c': 0}],
    ),
))
def test_calculate_missing_signoffs(policy, existing_signatures, expected):
    assert _calculate_missing_signoffs(policy, existing_signatures) == expected


@pytest.mark.parametrize('policy, existing_signatures', (
    (
        [{'releng': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng'), MagicMock(email='another-releng@m.c', group='releng')],
    ),
))
def test_calculate_missing_signoffs_wrong_decrement(policy, existing_signatures):
    with pytest.raises(Exception):
        _calculate_missing_signoffs(policy, existing_signatures)


@pytest.mark.parametrize('email, group_name, policy, existing_signatures', (
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
))
def test_has_user_signed_policy(email, group_name, policy, existing_signatures):
    assert _has_user_signed_policy(email, group_name, policy, existing_signatures)


@pytest.mark.parametrize('email, group_name, policy, existing_signatures', (
    (
        'a-valid-relman@m.c',
        'relman',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 2, 'relman': 1}],
        [],
    ),
    (
        'a-valid-releng@m.c',
        'relman',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        'a-valid-releng@m.c',
        'relman',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-relman@m.c', group='relman')],
    ),
))
def test_not_has_user_signed_policy(email, group_name, policy, existing_signatures):
    assert not _has_user_signed_policy(email, group_name, policy, existing_signatures)


@pytest.mark.parametrize('email, group_name, policy, existing_signatures', (
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 2, 'relman': 1}],
        [MagicMock(email='a-valid-releng@m.c', group='releng')],
    ),
    (
        'super-admin@m.c',
        'non-important',
        [{'releng': 2, 'relman': 1}, {'super-admin@m.c': 1, 'super-admin-two@m.c': 1}],
        [MagicMock(email='super-admin@m.c', group='releng'), MagicMock(email='another-releng@m.c', group='releng')],
    ),
))
def test_check_whether_policy_can_be_unsigned(email, group_name, policy, existing_signatures):
    check_whether_policy_can_be_unsigned(email, group_name, policy, existing_signatures)


@pytest.mark.parametrize('email, group_name, policy, existing_signatures, expected_exception', (
    (
        'a-valid-releng@m.c',
        'releng',
        [{'relman': 1, 'qe': 1}],
        [],
        UnauthorizedUserError,
    ),
    (
        'a-valid-releng@m.c',
        'releng',
        [{'releng': 1, 'relman': 1}],
        [],
        NoSignaturePresentError,
    ),
))
def test_error_check_whether_policy_can_be_unsigned(email, group_name, policy, existing_signatures, expected_exception):
    with pytest.raises(expected_exception):
        check_whether_policy_can_be_unsigned(email, group_name, policy, existing_signatures)
