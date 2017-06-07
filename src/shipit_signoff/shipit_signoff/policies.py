# -*- coding: utf-8 -*-
import copy

from shipit_signoff.util import is_key_present_in_list_of_dicts


class UnauthorizedUserError(Exception):
    def __init__(self, email, group_name, policy):
        super().__init__('{} (in group "{}") is not allowed to sign off policy {}'.format(email, group_name, policy))


class NoSignoffLeftError(Exception):
    def __init__(self, email, group_name, policy, missing_signoffs):
        super().__init__('{} (in group "{}") cannot signoff policy {}. Missing signoff are: {}'.format(email, group_name, policy, missing_signoffs))


def check_whether_policy_can_be_signed(email, group_name, policy, existing_signatures):
    is_user_allowed_to_sign = any((
        _is_group_defined_in_policy(group_name, policy),
        _is_email_defined_in_policy(email, policy)
    ))

    if not is_user_allowed_to_sign:
        raise UnauthorizedUserError(email, group_name, policy)

    can_user_still_sign = any((
        _are_there_signoffs_left_for_group(group_name, policy, existing_signatures),
        _are_there_signoffs_left_for_email(email, policy, existing_signatures),
    ))

    if not can_user_still_sign:
        missing_signoffs = _calculate_missing_signoffs(policy, existing_signatures)
        raise NoSignoffLeftError(email, group_name, policy, missing_signoffs)


def _is_group_defined_in_policy(group_name, policy):
    return is_key_present_in_list_of_dicts(key=group_name, list_of_dicts=policy)


def _is_email_defined_in_policy(email, policy):
    return is_key_present_in_list_of_dicts(key=email, list_of_dicts=policy)


def _are_there_signoffs_left_for_group(group_name, policy, existing_signatures):
    return _are_there_signoffs_left_for_key(key=group_name, policy=policy, existing_signatures=existing_signatures)


def _are_there_signoffs_left_for_email(email, policy, existing_signatures):
    return _are_there_signoffs_left_for_key(key=email, policy=policy, existing_signatures=existing_signatures)


def _are_there_signoffs_left_for_key(key, policy, existing_signatures):
    missing_signoffs = _calculate_missing_signoffs(policy, existing_signatures)
    return any(signoff_condition.get(key, -1) > 0 for signoff_condition in missing_signoffs)


def is_sign_off_policy_met(policy, existing_signatures):
    missing_signoffs = _calculate_missing_signoffs(policy, existing_signatures)
    return any(_is_signoff_condition_met(condition) for condition in missing_signoffs)


def _is_signoff_condition_met(signoff_condition):
    return all(number_of_signoffs == 0 for number_of_signoffs in signoff_condition.values())


def _calculate_missing_signoffs(policy, existing_signatures):
    missing_signoffs = copy.deepcopy(policy)

    for signature in existing_signatures:
        for email_or_group in (signature.group, signature.email):
            for signoff_condition in missing_signoffs:
                number_of_signoffs = signoff_condition.get(email_or_group, None)
                if number_of_signoffs is not None:
                    if number_of_signoffs <= 0:
                        # TODO use finer error
                        raise Exception('Too many decrement!')
                    signoff_condition[email_or_group] = number_of_signoffs - 1

    return missing_signoffs
