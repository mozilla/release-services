# -*- coding: utf-8 -*-

from cli_common import command
import click
import pytest


def test_empty_command():
    for param in [[], '']:
        for func in ['run', 'run_check']:
            with pytest.raises(click.ClickException, message="Can\'t run an empty command."):
                getattr(command, func)(param)
