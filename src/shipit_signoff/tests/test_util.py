# -*- coding: utf-8 -*-
import pytest

from shipit_signoff.util import is_key_present_in_list_of_dicts


@pytest.mark.parametrize('key, list_of_dicts', (
    ('a_key', [{'a_key': 'a_value'}]),
    ('a_key', [{'other_key': 'other_value'}, {'a_key': 'some_other_value'}]),
    ('a_key', [{'other_key': 'other_value'}, {'a_key': 'some_other_value', 'another_different_key': 'value'}]),
    ('a_duplicated_key', [{'a_duplicated_key': 'a_value'}, {'a_duplicated_key': 'some_other_value'}]),
))
def test_is_key_present_in_list_of_dicts(key, list_of_dicts):
    assert is_key_present_in_list_of_dicts(key, list_of_dicts)


@pytest.mark.parametrize('key, list_of_dicts', (
    ('non_existing_key', [{}]),
    ('non_existing_key', [{'a_key': 'a_value'}]),
    ('non_existing_key', [{'a_key': 'a_value'}, {'another_key': 'another_value'}]),
))
def test_not_is_key_present_in_list_of_dicts(key, list_of_dicts):
    assert not is_key_present_in_list_of_dicts(key, list_of_dicts)
