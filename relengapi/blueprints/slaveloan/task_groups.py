# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from celery import chain
from celery import group as group_

from relengapi.blueprints.slaveloan import slave_mappings
from relengapi.blueprints.slaveloan import tasks


def group(*args, **kwargs):
    """Celery fails to chain two disparate groups together

    e.g. it starts groupB before groupA has finished in:
    groupA = group(...)
    groupB = group(...)
    all_tasks = chain(groupA, groupB)

    By chaining a group with a `do nothing` task we can achieve the desired affect
    This function replaces our use of group for simplicity
    c.f. http://stackoverflow.com/questions/15123772/
    """
    return chain(group_(*args, **kwargs),
                 tasks.dummy_task.si())


def generate_loan(slavetype, loanid):
    return chain(
        # Could add user to VPN earlier, here if automated.
        tasks.bmo_file_loan_bug.si(loanid=loanid, slavetype=slavetype),
        prep_machine_info(loanid=loanid, slavetype=slavetype),
        clean_secrets(loanid=loanid, slavetype=slavetype),
        notify_loan_done(loanid=loanid, slavetype=slavetype)
    )


def prep_machine_info(slavetype, loanid):
    if slave_mappings.is_aws_serviceable(slavetype):
        return chain(
            manual_action(loanid=loanid, action_name="create_aws_system"),
            manual_action(loanid=loanid, action_name="add_to_vpn"),
            tasks.choose_aws_machine.si(loanid=loanid, loan_class=slavetype),
            group(
                tasks.fixup_machine.s(loanid=loanid),
                tasks.bmo_set_tracking_bug.s(loanid=loanid),
            )
        )
    else:
        return chain(
            tasks.choose_inhouse_machine.si(loanid=loanid, loan_class=slavetype),
            group(
                tasks.fixup_machine.s(loanid=loanid),
                tasks.bmo_set_tracking_bug.s(loanid=loanid),
                disable_machine_from_buildbot(slavetype, loanid),
            ),
            group(
                manual_action(loanid=loanid, action_name="add_to_vpn"),
                gpo_switch(loanid=loanid, slavetype=slavetype),
            ),
        )


def disable_machine_from_buildbot(slavetype, loanid):
    """ This celery grouping is for our need to disable a slave from taking buildbot jobs.

    AWS Loans should spinup without buildbot running/enabled, while inhouse
    needs to disable from slavealloc and make sure we're shut down

    Returns either a celery task, or a celery chain of actions.
    Expects previous celery task to return to it a machine name [not qualified by DNS]
    """
    if slave_mappings.is_aws_serviceable(slavetype):
        return tasks.dummy_task.si()
    else:
        return chain(
            tasks.slavealloc_disable.s(loanid=loanid),
            tasks.start_disable_slave.s(loanid=loanid),
            tasks.waitfor_disable_slave.s(loanid=loanid)
        )


def manual_action(loanid, action_name):
    return chain(
        tasks.register_action_needed.si(loanid=loanid, action_name=action_name),
        tasks.waitfor_action.s(loanid=loanid)
    )


def gpo_switch(loanid, slavetype):
    if slave_mappings.needs_gpo(slavetype):
        # return chain(
        #     tasks.bmo_file_gpo_bug.si(loanid=loanid),
        #     tasks.bmo_waitfor_bug.si(loanid=loanid)
        # )
        return manual_action(loanid=loanid, action_name="gpo_switch")
    else:
        return tasks.dummy_task.si()


def clean_secrets(loanid, slavetype):
    # tasks.clean_secrets.si(loanid=loanid)
    if not slave_mappings.needs_gpo(slavetype):
        return manual_action(loanid=loanid, action_name="clean_secrets")
    else:
        # gpo does the secret cleaning for us
        return tasks.dummy_task.si()


def notify_loan_done(loanid, slavetype):
    return chain(
        manual_action(loanid=loanid, action_name="notify_complete"),
        tasks.mark_loan_status.si(loanid=loanid, status="ACTIVE")
    )
    # return group(
    #     tasks.update_loan_bug_with_details.si(loanid=loanid),
    #     tasks.email_loan_details.si(loanid=loanid)
    # )
