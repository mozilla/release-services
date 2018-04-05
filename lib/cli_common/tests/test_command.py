# -*- coding: utf-8 -*-

import click
import pytest

import cli_common.command


def test_empty_command():
    for param in [[], '']:
        for func in ['run', 'run_check']:
            with pytest.raises(click.ClickException, message="Can\'t run an empty command."):
                getattr(cli_common.command, func)(param)
