# -*- coding: utf-8 -*-

import pytest


def test_empty_command():
    import click
    import cli_common.command

    for param in [[], '']:
        for func in ['run', 'run_check']:
            with pytest.raises(click.ClickException, message="Can\'t run an empty command."):
                getattr(cli_common.command, func)(param)


@pytest.mark.parametrize('text, secrets, expected', [
    ('some secret', ['secret'], 'some XXX'),
    (b'some secret', ['secret'], b'some XXX'),
    ('some', [None], 'some'),
    (b'some', [None], b'some'),
])
def test_hide_secrets(text, secrets, expected):
    import cli_common.command
    assert cli_common.command.hide_secrets(text, secrets) == expected
