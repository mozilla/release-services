# -*- coding: utf-8 -*-
from shipit_pulse_listener.hook import Hook
from datetime import timedelta


def test_parse_deadline():
    hook = Hook('gid', 'hid')
    assert hook.parse_deadline('1 second') == timedelta(seconds=1)
    assert hook.parse_deadline('2 seconds') == timedelta(seconds=2)
    assert hook.parse_deadline('1 minute') == timedelta(minutes=1)
    assert hook.parse_deadline('2 minutes') == timedelta(minutes=2)
    assert hook.parse_deadline('1 hour') == timedelta(minutes=60)
    assert hook.parse_deadline('2 hours') == timedelta(minutes=120)
    assert hook.parse_deadline('1 day') == timedelta(days=1)
    assert hook.parse_deadline('2 days') == timedelta(days=2)
