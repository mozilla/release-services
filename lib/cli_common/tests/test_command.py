# -*- coding: utf-8 -*-

import cli_common.command
import click
import pytest


def test_empty_command():
    for param in [[], '']:
        for func in ['run', 'run_check']:
            with pytest.raises(click.ClickException, message="Can\'t run an empty command."):
                getattr(cli_common.command, func)(param)
