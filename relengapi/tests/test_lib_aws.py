# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import Queue
import json
import logging
import mock

from logging import handlers
from moto import mock_sqs
from nose.tools import assert_raises
from nose.tools import eq_
from relengapi.lib import aws
from relengapi.lib.testing.context import TestContext

test_context = TestContext(reuse_app=False)

aws_cfg = {
    'AWS': {
        'access_key_id': 'aa',
        'secret_access_key': 'ss',
    },
}


@test_context.specialize(config=aws_cfg)
def test_connect_to_s3(app):
    # for S3, boto doesn't support a 'region' argument to connect_s3, so we use
    # boto.s3.connect_to_region instead
    with mock.patch('boto.s3.connect_to_region', return_value='s3_conn') as ctr:
        eq_(app.aws.connect_to('s3', 'us-west-2'), 's3_conn')
        ctr.assert_called_with(
            aws_access_key_id='aa',
            aws_secret_access_key='ss',
            region_name='us-west-2')
    # connection is cached
    eq_(app.aws.connect_to('s3', 'us-west-2'), 's3_conn')


@test_context.specialize(config=aws_cfg)
def test_connect_to(app):
    with mock.patch('boto.connect_sqs', return_value='sqs_conn') as connect_sqs:
        eq_(app.aws.connect_to('sqs', 'us-east-1'), 'sqs_conn')
        connect_sqs.assert_called_with(
            aws_access_key_id='aa',
            aws_secret_access_key='ss',
            region=mock.ANY)
    # connection is cached
    eq_(app.aws.connect_to('sqs', 'us-east-1'), 'sqs_conn')


@mock_sqs
@test_context
def test_connect_to_no_creds(app):
    with mock.patch('boto.connect_sqs', return_value='sqs_conn') as connect_sqs:
        eq_(app.aws.connect_to('sqs', 'us-east-1'), 'sqs_conn')
        connect_sqs.assert_called_with(
            # the None here will cause boto to look in ~/.boto, etc.
            aws_access_key_id=None,
            aws_secret_access_key=None,
            region=mock.ANY)


@mock_sqs
@test_context
def test_connect_to_invalid_region(app):
    assert_raises(RuntimeError, lambda:
                  app.aws.connect_to('sqs', 'us-canada-17'))


@mock_sqs
@test_context.specialize(config=aws_cfg)
def test_get_sqs_queue_no_queue(app):
    assert_raises(RuntimeError, lambda:
                  app.aws.get_sqs_queue('us-east-1', 'missing'))


@mock_sqs
@test_context.specialize(config=aws_cfg)
def test_get_sqs_queue(app):
    conn = app.aws.connect_to('sqs', 'us-east-1')
    conn.create_queue('my-sqs-queue')
    queue = app.aws.get_sqs_queue('us-east-1', 'my-sqs-queue')
    # check it's a queue
    assert hasattr(queue, 'get_messages')
    # check caching
    assert app.aws.get_sqs_queue('us-east-1', 'my-sqs-queue') is queue


@mock_sqs
@test_context.specialize(config=aws_cfg)
def test_sqs_write(app):
    conn = app.aws.connect_to('sqs', 'us-east-1')
    queue = conn.create_queue('my-sqs-queue')
    app.aws.sqs_write('us-east-1', 'my-sqs-queue', {'a': 'b'})
    msgs = queue.get_messages()
    assert len(msgs) == 1
    eq_(json.loads(msgs[0].get_body()), {'a': 'b'})


@mock_sqs
@test_context
def test_sqs_listen_no_such_queue(app):
    log_buffer = handlers.BufferingHandler(100)
    logging.getLogger().addHandler(log_buffer)
    try:
        app.aws._listen_thd('us-east-1', 'no-such-queue', {}, lambda msg: None)
        assert any(
            'listening cancelled' in record.message for record in log_buffer.buffer)
    finally:
        logging.getLogger().removeHandler(log_buffer)


@mock_sqs
@test_context
def test_sqs_listen(app):
    log_buffer = handlers.BufferingHandler(100)

    logging.getLogger().addHandler(log_buffer)
    try:
        conn = app.aws.connect_to('sqs', 'us-east-1')
        conn.create_queue('my-sqs-queue')

        got_msgs = Queue.Queue()

        @app.aws.sqs_listen('us-east-1', 'my-sqs-queue')
        def listener(msg):
            body = json.loads(msg.get_body())
            if body == 'EXC':
                # this message won't loop back immediately because
                # its visibility timeout has not expired
                raise RuntimeError
            got_msgs.put(body)
            if body == 'BODY2':
                raise aws._StopListening

        threads = app.aws._spawn_sqs_listeners(_testing=True)
        try:
            app.aws.sqs_write('us-east-1', 'my-sqs-queue', 'BODY1')
            app.aws.sqs_write('us-east-1', 'my-sqs-queue', 'EXC')
            app.aws.sqs_write('us-east-1', 'my-sqs-queue', 'BODY2')

            eq_(got_msgs.get(), 'BODY1')
            eq_(got_msgs.get(), 'BODY2')

            # check that the exception was logged
            assert any(
                'while invoking' in record.message for record in log_buffer.buffer)

        finally:
            for th in threads:
                th.join()

        # NOTE: moto does not support changing message visibility, so there's no
        # good way to programmatically verify that messages are being deleted
    finally:
        logging.getLogger().removeHandler(log_buffer)
