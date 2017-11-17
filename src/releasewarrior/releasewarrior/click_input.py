import getpass
import click
import arrow

from releasewarrior.collections import InflightTask, PrerequisiteTask, Issue


def generate_inflight_task_from_input():
    position = click.prompt('After which existing task should this new task be run? Use ID',
                            type=int, default=1)
    description = click.prompt('Description of the inflight task', type=str)
    docs = click.prompt('Docs for this? Use a URL if possible', default="", type=str)
    return InflightTask(position, description, docs, resolved=False)


def generate_prereq_task_from_input():
    bug = click.prompt('Bug number if exists', type=str, default="none")
    description = click.prompt('Description of prerequisite task', type=str)
    deadline = click.prompt('When does this have to be completed', type=str,
                            default=arrow.now('US/Pacific').format("YYYY-MM-DD"))
    return PrerequisiteTask(bug, deadline, description, resolved=False)


def generate_inflight_issue_from_input():
    who = click.prompt('Who', type=str, default=getpass.getuser())
    bug = click.prompt('Bug number if exists', type=str, default="none")
    description = click.prompt('Description of issue', type=str)
    return Issue(who, bug, description, resolved=False, future_threat=True)


def is_future_threat_input():
    return click.prompt('Is this a future release threat?', type=bool)



