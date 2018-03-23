# -*- coding: utf-8 -*-

import pytest

import click
from cli_common import command


def test_empty_command():
    for param in [[], '']:
        for func in ['run', 'run_check']:
            with pytest.raises(click.ClickException, message="Can\'t run an empty command."):
                getattr(command, func)(param)
