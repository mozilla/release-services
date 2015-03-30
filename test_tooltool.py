# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import BaseHTTPServer
import cStringIO
import contextlib
import copy
import hashlib
import json
import logging
import mock
import os
import os.path
import shutil
import sys
import tempfile
import threading
import tooltool
import unittest
import urllib2

from nose.tools import eq_


class TestDirMixin(object):

    def setUpTestDir(self):
        self.test_dir = os.path.abspath(tempfile.mkdtemp())
        self.__old_cwd = os.getcwd()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        os.chdir(self.test_dir)

    def tearDownTestDir(self):
        os.chdir(self.__old_cwd)
        shutil.rmtree(self.test_dir)


class BufferHandler(logging.Handler):

    def __init__(self, buffer):
        self.buffer = buffer
        logging.Handler.__init__(self)

    def emit(self, record):
        self.buffer.append((record.levelno, record.getMessage()))

    @classmethod
    @contextlib.contextmanager
    def capture(cls, logger_name):
        logger = logging.getLogger(logger_name)
        buffer = []
        handler = cls(buffer)
        logger.addHandler(handler)
        try:
            yield buffer
        finally:
            logger.removeHandler(handler)


class DigestTests(unittest.TestCase):

    def setUp(self):
        self.sample_data = open('test_file.ogg')
        self.sample_algo = 'sha1'
        self.sample_digest = 'de3e3bbffd83c328ad7d9537ad2d03f68fc02e52'

    def test_digest_file(self):
        test_digest = tooltool.digest_file(self.sample_data, self.sample_algo)
        # If this assertion fails, verify that test_file.ogg is an ogg file
        # of Linus Torvalds explaining how he pronounces 'Linux'
        self.assertEqual(test_digest, self.sample_digest)


class BaseFileRecordTest(unittest.TestCase):

    def setUp(self):
        self.sample_file = 'test_file.ogg'
        self.sample_algo = 'sha512'
        self.sample_size = os.path.getsize(self.sample_file)
        with open(self.sample_file) as f:
            self.sample_hash = tooltool.digest_file(f, self.sample_algo)
        self.test_record = tooltool.FileRecord(
            filename=self.sample_file,
            size=self.sample_size,
            digest=self.sample_hash,
            algorithm=self.sample_algo
        )
        self.test_record_json = {
            'filename': self.sample_file,
            'algorithm': self.sample_algo,
            'digest': self.sample_hash,
            'size': self.sample_size,
        }
        # using mkstemp to ensure that the filename generated
        # isn't actually on the system.
        (tmpfd, filename) = tempfile.mkstemp()
        os.close(tmpfd)
        os.remove(filename)
        if os.path.exists(filename):
            self.fail('did not remove %s' % filename)
        self.absent_file = filename


class BaseFileRecordListTest(BaseFileRecordTest):

    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.record_list = []
        for i in range(0, 4):
            record = copy.deepcopy(self.test_record)
            record.algorithm = i
            self.record_list.append(record)


class BaseManifestTest(TestDirMixin, BaseFileRecordTest):

    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.setUpTestDir()
        self.sample_manifest = tooltool.Manifest([self.test_record])
        self.sample_manifest_file = 'manifest.tt'
        with open(self.sample_manifest_file, 'w') as tmpfile:
            self.sample_manifest.dump(tmpfile, fmt='json')

    def tearDown(self):
        self.tearDownTestDir()


class TestFileRecord(BaseFileRecordTest):

    def test_create_with_posix_path_info(self):
        self.assertRaises(tooltool.ExceptionWithFilename, lambda:
                          tooltool.FileRecord('abc/def', 10, 'abcd', 'alpha'))

    def test_create_with_windows_path_info(self):
        self.assertRaises(tooltool.ExceptionWithFilename, lambda:
                          tooltool.FileRecord(r'abc\def', 10, 'abcd', 'alpha'))

    def test_present(self):
        # this test feels silly, but things are built on this
        # method, so probably best to test it
        self.assertTrue(self.test_record.present())

    def test_absent(self):
        self.test_record.filename = self.absent_file
        self.assertFalse(self.test_record.present())

    def test_valid_size(self):
        self.assertTrue(self.test_record.validate_size())

    def test_invalid_size(self):
        self.test_record.size += 1
        self.assertFalse(self.test_record.validate_size())

    def test_size_of_missing_file(self):
        self.test_record.filename = self.absent_file
        self.assertRaises(
            tooltool.MissingFileException, self.test_record.validate_size)

    def test_valid_digest(self):
        self.assertTrue(self.test_record.validate_digest())

    def test_invalid_digest(self):
        self.test_record.digest = 'NotValidDigest'
        self.assertFalse(self.test_record.validate_digest())

    def test_digest_of_missing_file(self):
        self.test_record.filename = self.absent_file
        self.assertRaises(
            tooltool.MissingFileException, self.test_record.validate_digest)

    def test_overall_valid(self):
        self.assertTrue(self.test_record.validate())

    def test_overall_invalid_size(self):
        self.test_record.size = 3
        self.assertFalse(self.test_record.validate())

    def test_overall_invalid_digest(self):
        self.test_record.digest = 'NotValidDigest'
        self.assertFalse(self.test_record.validate())

    def test_overall_invalid_missing_file(self):
        self.test_record.filename = self.absent_file
        self.assertRaises(
            tooltool.MissingFileException, self.test_record.validate)

    def test_equality(self):
        test_record2 = copy.deepcopy(self.test_record)
        self.assertEqual(self.test_record, test_record2)
        self.assertEqual(self.test_record, self.test_record)

    def test_equality_validity(self):
        test_record2 = copy.deepcopy(self.test_record)
        self.test_record.visibility = True
        test_record2.visibility = False
        self.assertNotEqual(self.test_record, test_record2)

    def test_inequality(self):
        for i in ['filename', 'size', 'algorithm', 'digest']:
            test_record2 = copy.deepcopy(self.test_record)
            test_record2.__dict__[i] = 'wrong!'
            self.assertNotEqual(self.test_record, test_record2)

    def test_repr(self):
        a = eval(repr(self.test_record))
        self.assertEqual(str(a), str(self.test_record))
        self.assertEqual(a, self.test_record)

    def test_create_file_record(self):
        fr = tooltool.create_file_record(self.sample_file, self.sample_algo)
        self.assertEqual(self.test_record, fr)

    def test_describe_absent(self):
        self.test_record.filename = self.absent_file
        self.assertEqual("'%s' is absent" %
                         self.absent_file, self.test_record.describe())

    def test_describe_present_valid(self):
        self.assertEqual("'%s' is present and valid" % self.test_record.filename,
                         self.test_record.describe())

    def test_describe_present_invalid(self):
        self.test_record.size = 4
        self.test_record.digest = 'NotValidDigest'
        self.assertEqual("'%s' is present and invalid" % self.test_record.filename,
                         self.test_record.describe())


class TestFileRecordJSONCodecs(BaseFileRecordListTest):

    def test_default(self):
        encoder = tooltool.FileRecordJSONEncoder()
        dict_from_encoder = encoder.default(self.test_record)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(
                dict_from_encoder[i], self.test_record.__dict__[i])

    def test_default_list(self):
        encoder = tooltool.FileRecordJSONEncoder()
        new_list = encoder.default(self.record_list)
        for record in range(0, len(self.record_list)):
            self.assertEqual(new_list[record],
                             encoder.default(self.record_list[record]))

    def test_unrelated_class(self):
        encoder = tooltool.FileRecordJSONEncoder()

        class Junk:
            pass
        self.assertRaises(
            tooltool.FileRecordJSONEncoderException,
            encoder.default,
            Junk()
        )

    def test_list_with_unrelated_class(self):
        encoder = tooltool.FileRecordJSONEncoder()

        class Junk:
            pass
        self.assertRaises(
            tooltool.FileRecordJSONEncoderException,
            encoder.default,
            [self.test_record, Junk(), self.test_record],
        )

    def test_decode(self):
        json_string = json.dumps(
            self.test_record, cls=tooltool.FileRecordJSONEncoder)
        decoder = tooltool.FileRecordJSONDecoder()
        f = decoder.decode(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest', 'visibility']:
            self.assertEqual(getattr(f, i), self.test_record.__dict__[i])

    def test_decode_visibility(self):
        self.test_record.visibility = True
        json_string = json.dumps(
            self.test_record, cls=tooltool.FileRecordJSONEncoder)
        decoder = tooltool.FileRecordJSONDecoder()
        f = decoder.decode(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest', 'visibility']:
            self.assertEqual(getattr(f, i), self.test_record.__dict__[i])

    def test_decode_dict_not_filerecord(self):
        decoder = tooltool.FileRecordJSONDecoder()
        eq_(decoder.decode('{"filename": "foo.txt"}'), {'filename': 'foo.txt'})

    def test_json_dumps(self):
        json_string = json.dumps(
            self.test_record, cls=tooltool.FileRecordJSONEncoder)
        dict_from_json = json.loads(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(dict_from_json[i], self.test_record.__dict__[i])

    def test_json_dumps_with_unpack(self):
        self.test_record.unpack = True
        json_string = json.dumps(
            self.test_record, cls=tooltool.FileRecordJSONEncoder)
        from_json = json.loads(json_string,
                               cls=tooltool.FileRecordJSONDecoder)
        for i in ['filename', 'size', 'algorithm', 'digest', 'unpack']:
            self.assertEqual(getattr(from_json, i), getattr(self.test_record, i), i)

    def test_decode_list(self):
        json_string = json.dumps(
            self.record_list, cls=tooltool.FileRecordJSONEncoder)
        new_list = json.loads(json_string, cls=tooltool.FileRecordJSONDecoder)
        self.assertEquals(len(new_list), len(self.record_list))
        for record in range(0, len(self.record_list)):
            self.assertEqual(new_list[record], self.record_list[record])


class TestManifest(BaseFileRecordTest):

    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.other_sample_file = 'other-%s' % self.sample_file
        if os.path.exists(self.other_sample_file):
            os.remove(self.other_sample_file)
        shutil.copyfile(self.sample_file, self.other_sample_file)
        self.other_test_record = copy.deepcopy(self.test_record)
        self.other_test_record.filename = self.other_sample_file
        self.test_manifest = tooltool.Manifest(
            [self.test_record, self.other_test_record])

    def tearDown(self):
        try:
            os.remove(self.other_sample_file)
        except OSError:
            pass

    def test_present(self):
        self.assertTrue(self.test_manifest.present())

    def test_absent(self):
        os.remove(self.other_sample_file)
        self.assertFalse(self.test_manifest.present())

    def test_validate_sizes(self):
        self.assertTrue(self.test_manifest.validate_sizes())

    def test_incorrect_size(self):
        self.test_manifest.file_records[1].size = 1
        self.assertFalse(self.test_manifest.validate_sizes())

    def test_validate_digest(self):
        self.assertTrue(self.test_manifest.validate_digests())

    def test_validate(self):
        self.assertTrue(self.test_manifest.validate())

    def test_incorrect_digest(self):
        self.test_manifest.file_records[1].digest = 'wrong'
        self.assertFalse(self.test_manifest.validate_digests())

    def test_equality_same_object(self):
        self.assertEqual(self.test_manifest, self.test_manifest)

    def test_equality_copy(self):
        a_copy = copy.copy(self.test_manifest)
        self.assertEqual(self.test_manifest, a_copy)

    def test_equality_deepcopy(self):
        a_deepcopy = copy.deepcopy(self.test_manifest)
        self.assertEqual(self.test_manifest, a_deepcopy)

    def test_equality_copy_method(self):
        a_copy = self.test_manifest.copy()
        self.assertEqual(self.test_manifest, a_copy)

    def test_equality_unrelated(self):
        one = tooltool.Manifest([self.test_record, self.other_test_record])
        two = tooltool.Manifest([self.test_record, self.other_test_record])
        self.assertEqual(one, two)

    def test_equality_different_order(self):
        one = tooltool.Manifest([self.test_record, self.other_test_record])
        two = tooltool.Manifest([self.other_test_record, self.test_record])
        self.assertEqual(one, two)

    def test_inequality_different_count(self):
        one = tooltool.Manifest([self.other_test_record])
        two = tooltool.Manifest([self.test_record, self.other_test_record])
        self.assertNotEqual(one, two)

    def test_inequality_different_records(self):
        one = tooltool.Manifest([self.test_record])
        two = tooltool.Manifest([self.other_test_record])
        self.assertNotEqual(one, two)

    def test_json_dump(self):
        tmp_manifest = tempfile.TemporaryFile()
        self.test_manifest.dump(tmp_manifest, fmt='json')
        tmp_manifest.seek(0)
        new_manifest = tooltool.Manifest()
        new_manifest.load(tmp_manifest, fmt='json')
        self.assertEqual(new_manifest, self.test_manifest)

    def test_json_dumps(self):
        s = self.test_manifest.dumps(fmt='json')
        new_manifest = tooltool.Manifest()
        new_manifest.loads(s, fmt='json')
        self.assertEqual(new_manifest, self.test_manifest)

    def test_load_empty_json_file(self):
        empty = tempfile.TemporaryFile()
        manifest = tooltool.Manifest()
        self.assertRaises(tooltool.InvalidManifest,
                          manifest.load, empty, fmt='json')

    def test_load_empty_json_string(self):
        empty = ''
        manifest = tooltool.Manifest()
        self.assertRaises(tooltool.InvalidManifest,
                          manifest.loads, empty, fmt='json')


class TestManifestOperations(BaseManifestTest):

    def test_open_manifest(self):
        manifest = tooltool.open_manifest(self.sample_manifest_file)
        eq_(manifest.file_records[0].filename, 'test_file.ogg')

    def test_open_manifest_missing(self):
        self.assertRaises(tooltool.InvalidManifest, lambda:
                          tooltool.open_manifest('no-such-file'))


def test_execute():
    assert tooltool.execute('echo foo; echo bar')


def test_execute_fails():
    assert not tooltool.execute('false')


def call_main(*args):
    try:
        old_stderr = sys.stderr
        sys.stderr = sys.stdout
        try:
            return tooltool.main(list(args), _skip_logging=True)
        except SystemExit, e:
            return "exit %d" % e.code
    finally:
        sys.stderr = old_stderr


def test_main_help():
    eq_(call_main('tooltool', '--help'), "exit 0")


def test_main_no_command():
    eq_(call_main('tooltool'), "exit 2")


def test_main_bad_command():
    eq_(call_main('tooltool', 'foo'), 1)


def test_main_bad_algorithm():
    eq_(call_main('tooltool', '--algorithm', 'sha13', 'fetch'), 'exit 2')


def test_command_list():
    with mock.patch('tooltool.list_manifest') as list_manifest:
        eq_(call_main('tooltool', 'list', '--manifest', 'foo.tt'), 0)
        list_manifest.assert_called_with('foo.tt')


def test_command_validate():
    with mock.patch('tooltool.validate_manifest') as validate_manifest:
        eq_(call_main('tooltool', 'validate'), 0)
        validate_manifest.assert_called_with('manifest.tt')


def test_command_add():
    with mock.patch('tooltool.add_files') as add_files:
        eq_(call_main('tooltool', 'add', 'a', 'b'), 0)
        add_files.assert_called_with('manifest.tt', 'sha512', ['a', 'b'], None)


def test_command_add_visibility_internal():
    with mock.patch('tooltool.add_files') as add_files:
        eq_(call_main('tooltool', 'add', '--visibility', 'internal', 'a', 'b'), 0)
        add_files.assert_called_with('manifest.tt', 'sha512', ['a', 'b'], 'internal')


def test_command_add_visibility_public():
    with mock.patch('tooltool.add_files') as add_files:
        eq_(call_main('tooltool', 'add', '--visibility', 'public', 'a', 'b'), 0)
        add_files.assert_called_with('manifest.tt', 'sha512', ['a', 'b'], 'public')


def test_command_purge_no_folder():
    with mock.patch('tooltool.purge') as purge:
        eq_(call_main('tooltool', 'purge'), 1)
        assert not purge.called


def test_command_purge():
    with mock.patch('tooltool.purge') as purge:
        eq_(call_main('tooltool', 'purge', '--cache', 'foo'), 1)
        purge.assert_called_with(folder='foo', gigs=0)


def test_command_purge_size():
    with mock.patch('tooltool.purge') as purge:
        eq_(call_main('tooltool', 'purge', '--size', '10', '--cache', 'foo'), 1)
        purge.assert_called_with(folder='foo', gigs=10)


def test_command_fetch_no_url():
    with mock.patch('tooltool.fetch_files') as fetch_files:
        eq_(call_main('tooltool', 'fetch'), 0)
        fetch_files.assert_called_with('manifest.tt',
                                       ['https://api.pub.build.mozilla.org/tooltool/'],
                                       [], cache_folder=None, auth_file=None,
                                       region=None)


def test_command_fetch():
    with mock.patch('tooltool.fetch_files') as fetch_files:
        eq_(call_main('tooltool', 'fetch', 'a', 'b', '--url', 'http://foo'), 0)
        fetch_files.assert_called_with('manifest.tt', ['http://foo'], ['a', 'b'],
                                       cache_folder=None, auth_file=None,
                                       region=None)


def test_command_fetch_region():
    with mock.patch('tooltool.fetch_files') as fetch_files:
        eq_(call_main('tooltool', 'fetch', 'a', 'b', '--url', 'http://foo',
                      '--region', 'us-east-1'), 0)
        fetch_files.assert_called_with('manifest.tt', ['http://foo'], ['a', 'b'],
                                       cache_folder=None, auth_file=None,
                                       region='us-east-1')


def test_command_fetch_auth_file():
    # mock can't patch os.path.expanduser, because it looks for path.expanduser
    # in the os module
    old_expanduser = os.path.expanduser
    os.path.expanduser = mock.Mock()
    try:
        with mock.patch('tooltool.fetch_files') as fetch_files:
            os.path.expanduser.side_effect = lambda path: path.replace("~", "HOME")
            eq_(call_main('tooltool', 'fetch', 'a', 'b', '--url', 'http://foo',
                          '--authentication-file', '~/.tooltool-token'), 0)
            fetch_files.assert_called_with('manifest.tt', ['http://foo'],
                                           ['a', 'b'], cache_folder=None,
                                           auth_file="HOME/.tooltool-token",
                                           region=None)
    finally:
        os.path.expanduser = old_expanduser


def test_command_upload():
    with mock.patch('tooltool.upload') as upload:
        eq_(call_main('tooltool', 'upload', '--url', 'http://foo',
                      '--message', 'msg'), 0)
        upload.assert_called_with('manifest.tt', 'msg', ['http://foo'], None, None)


def test_command_upload_region():
    with mock.patch('tooltool.upload') as upload:
        eq_(call_main('tooltool', 'upload', '--url', 'http://foo',
                      '--message', 'msg', '--region=us-west-3'), 0)
        upload.assert_called_with('manifest.tt', 'msg', ['http://foo'], None, 'us-west-3')


def test_command_upload_no_message():
    with mock.patch('tooltool.upload') as upload:
        eq_(call_main('tooltool', 'upload', '--url', 'http://foo'), 1)
        assert not upload.called


def test_command_upload_no_url():
    with mock.patch('tooltool.upload') as upload:
        eq_(call_main('tooltool', 'upload', '--message', 'msg'), 0)
        upload.assert_called_with('manifest.tt', 'msg',
                                  ['https://api.pub.build.mozilla.org/tooltool/'],
                                  None, None)


class UploadTests(TestDirMixin, unittest.TestCase):

    class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

        """A mini webserver for uploading.  This implements both the RelengAPI
        bits (POST and GET) and the S3 bits (PUT)."""

        test_case = None

        def log_request(self, code=None, size=None):
            logging.getLogger('fake_web').info("%s %s" % (self.path, code))

        def verify_auth(self):
            token = self.test_case.server_config.get('exp_auth_token')
            if token:
                if self.headers.get('Authorization') != 'Bearer %s' % token:
                    self.send_response(403, "Forbidden")
                    self.send_header('content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write("go away")
                    self.wfile.close()
                    return False
            return True

        def do_POST(self):
            cfg = self.test_case.server_config
            if '?region=' in self.path:
                self.path, self.test_case.server_got_region = self.path.split('?')
            eq_(self.path, '/tooltool/upload')
            eq_(self.headers['content-type'], 'application/json')
            if not self.verify_auth():
                return
            body = json.loads(self.rfile.read(int(self.headers['content-length'])))
            self.test_case.server_requests.setdefault('POST', []).append(copy.deepcopy(body))
            eq_(body['message'], 'hi mom')

            files_on_server = cfg.get('files_on_server', [])
            for filename, file in body['files'].items():
                if filename not in files_on_server:
                    file['put_url'] = self.test_case.s3url('/sha512/' + file['digest'])

            if cfg.get('post_fails'):
                self.send_response(409, 'Exploded')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                json.dump({'error': {'name': 'uhoh', 'description': 'failed'}}, self.wfile)
            else:
                self.send_response(200, 'OK')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                json.dump({'result': body}, self.wfile)
            self.wfile.close()

        def do_PUT(self):  # S3 upload
            cfg = self.test_case.server_config
            assert self.path.startswith('/sha512/'), self.path
            eq_(self.headers['content-type'], 'application/octet-stream')
            data = self.rfile.read(int(self.headers['content-length']))
            digest = hashlib.sha512(data).hexdigest()
            self.test_case.server_requests.setdefault('PUT', []).append(digest)
            assert self.path.endswith(digest)
            if digest in cfg.get('upload_failures', []):
                self.send_response(500, 'NOPE')
            else:
                self.send_response(200, 'OK')
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.close()

        def do_GET(self):  # notify
            cfg = self.test_case.server_config
            assert self.path.startswith('/tooltool/upload/complete/sha512/')
            if not self.verify_auth():
                return
            digest = self.path[-128:]
            self.test_case.server_requests.setdefault('GET', []).append(digest)
            if cfg.get('get_fails'):
                self.send_response(500, 'NOPE')
            elif cfg.get('get_409s'):
                self.send_response(409, 'Conflict')
                self.send_header('X-Retry-After', '10')
                del cfg['get_409s']  # succeed on retry
            else:
                self.send_response(200, 'OK')
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.close()

    def setUp(self):
        self.setUpTestDir()

    def start_server(self):
        self.server_config = {}
        self.server_requests = {}
        UploadTests.Handler.test_case = self
        self.httpd = BaseHTTPServer.HTTPServer(("127.0.0.1", 0), UploadTests.Handler)
        self.http_port = self.httpd.server_port
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = 1
        self.server_thread.start()

        open("testfile.txt", 'w').write("FILE DATA")
        self.digest = hashlib.sha512('FILE DATA').hexdigest()

    def tearDown(self):
        if hasattr(self, 'httpd'):
            self.httpd.shutdown()
            self.server_thread.join()
        self.tearDownTestDir()

    def add_file(self, filename, on_server=False, upload_fails=False,
                 visibility='internal'):
        data = os.urandom(1024)
        open(filename, "w").write(data)
        digest = hashlib.sha512(data).hexdigest()
        tooltool.add_files('manifest.tt', 'sha512', [filename], visibility)
        if on_server:
            self.server_config.setdefault('files_on_server', []).append(filename)
        if upload_fails:
            self.server_config.setdefault('upload_failures', []).append(digest)
        return digest

    def mkurl(self, path):
        return 'http://127.0.0.1:%d/tooltool/%s' % (self.http_port, path)

    def s3url(self, path):
        return 'http://127.0.0.1:%d%s' % (self.http_port, path)

    def test_upload_success(self):
        """An upload with two files, one of which is on the server already,
        succeeds"""
        self.start_server()
        foo_digest = self.add_file("foo.txt", on_server=True)
        bar_digest = self.add_file("bar.txt", on_server=False)
        assert tooltool.upload('manifest.tt', 'hi mom', [self.mkurl('')], None, None)
        self.server_requests['POST'].sort()
        eq_(self.server_requests, {
            'POST': [{
                'files': {
                    'foo.txt': {
                        'digest': foo_digest,
                        'algorithm': 'sha512',
                        'visibility': 'internal',
                        'size': 1024,
                    },
                    'bar.txt': {
                        'digest': bar_digest,
                        'algorithm': 'sha512',
                        'visibility': 'internal',
                        'size': 1024,
                    },
                },
                'message': 'hi mom',
            }],
            'PUT': [bar_digest],
            'GET': [bar_digest],
        })

    def test_upload_success_auth(self):
        """An upload with authentication information succeeds when the server expects
        authentication."""
        self.start_server()
        foo_digest = self.add_file("foo.txt", on_server=True)
        self.server_config['exp_auth_token'] = token = 'abcABC'
        open("auth", "w").write(token)
        assert tooltool.upload('manifest.tt', 'hi mom', [self.mkurl('')], 'auth', None)
        eq_(self.server_requests, {
            'POST': [{
                'files': {
                    'foo.txt': {
                        'digest': foo_digest,
                        'algorithm': 'sha512',
                        'visibility': 'internal',
                        'size': 1024,
                    },
                },
                'message': 'hi mom',
            }],
        })

    def test_upload_success_region(self):
        """An upload with a region specified results in a POST with that region in
        the URL."""
        self.start_server()
        self.add_file("foo.txt", on_server=True)
        assert tooltool.upload('manifest.tt', 'hi mom', [self.mkurl('')], None, 'us-west-1')
        eq_(self.server_got_region, 'region=us-west-1')

    def test_upload_failure_auth(self):
        """An upload with incorrect authentication information fails"""
        self.start_server()
        self.add_file("foo.txt", on_server=True)
        self.server_config['exp_auth_token'] = 'abcABC'
        open("auth", "w").write('not-the-token')
        assert not tooltool.upload('manifest.tt', 'hi mom', [self.mkurl('')], 'auth', None)

    def test_upload_s3_fails(self):
        """When an S3 upload fails, the upload fails and no notification takes
        place."""
        self.start_server()
        foo_digest = self.add_file("foo.txt", upload_fails=True)
        assert not tooltool.upload('manifest.tt', 'hi mom', [self.mkurl('')], None, None)
        eq_(self.server_requests, {
            'POST': [{
                'files': {
                    'foo.txt': {
                        'digest': foo_digest,
                        'algorithm': 'sha512',
                        'visibility': 'internal',
                        'size': 1024,
                    },
                },
                'message': 'hi mom',
            }],
            'PUT': [foo_digest],
        })

    def test_upload_send_batch_fails(self):
        """When the upload request to RelengAPI fails, upload fails."""
        self.start_server()
        self.server_config['post_fails'] = True
        foo_digest = self.add_file("foo.txt", upload_fails=True)
        assert not tooltool.upload('manifest.tt', 'hi mom', [self.mkurl('')], None, None)
        eq_(self.server_requests, {
            'POST': [{
                'files': {
                    'foo.txt': {
                        'digest': foo_digest,
                        'algorithm': 'sha512',
                        'visibility': 'internal',
                        'size': 1024,
                    },
                },
                'message': 'hi mom',
            }],
        })

    def test_no_manifest(self):
        """When given a manifest that doesn't exist, upload fails."""
        assert not tooltool.upload('nosuch.tt', 'hi mom', ['http://'], None, None)

    def test_manifest_without_visibility(self):
        """When given a manifest with a file record without visibility, upload fails."""
        self.add_file("foo.txt", visibility=None)
        assert not tooltool.upload('manifest.tt', 'hi mom', ['http://'], None, None)

    def test_invalid_manifest(self):
        """When given a manifest that doesn't validate, upload fails"""
        self.add_file("foo.txt")
        open("foo.txt", "w").write('bogus')
        assert not tooltool.upload('manifest.tt', 'hi mom', ['http://'], None, None)

    def test_send_batch_success(self):
        self.start_server()
        batch = {'message': 'hi mom', 'files': {}}
        eq_(tooltool._send_batch(self.mkurl(''), None, batch, None), batch)
        eq_(self.server_requests, {'POST': [batch]})

    def test_send_batch_region(self):
        self.start_server()
        batch = {'message': 'hi mom', 'files': {}}
        eq_(tooltool._send_batch(self.mkurl(''), None, batch, 'us-south-1'), batch)
        eq_(self.server_requests, {'POST': [batch]})
        eq_(self.server_got_region, 'region=us-south-1')

    def test_send_batch_failure(self):
        self.start_server()
        self.server_config['post_fails'] = True
        batch = {'message': 'hi mom', 'files': {}}
        eq_(tooltool._send_batch(self.mkurl(''), None, batch, None), None)
        eq_(self.server_requests, {'POST': [batch]})

    def test_s3_upload(self):
        self.start_server()
        file = {'put_url': self.s3url('/sha512/' + self.digest)}
        tooltool._s3_upload('testfile.txt', file)
        eq_(self.server_requests, {'PUT': [self.digest]})
        assert file['upload_ok']

    def test_s3_upload_fails(self):
        self.start_server()
        self.server_config['upload_failures'] = [self.digest]
        file = {'put_url': self.s3url('/sha512/' + self.digest)}
        tooltool._s3_upload('testfile.txt', file)
        eq_(self.server_requests, {'PUT': [self.digest]})
        assert not file['upload_ok'], file
        assert 'upload_exception' in file, file

    def test_notify_upload(self):
        self.start_server()
        file = {'algorithm': 'sha512', 'digest': self.digest}
        tooltool._notify_upload_complete(self.mkurl(''), None, file)
        eq_(self.server_requests, {'GET': [self.digest]})

    def test_notify_upload_wait(self):
        self.start_server()
        self.server_config['get_409s'] = True
        file = {'algorithm': 'sha512', 'digest': self.digest}
        with mock.patch('time.sleep') as fake_sleep:
            tooltool._notify_upload_complete(self.mkurl(''), None, file)
        fake_sleep.assert_called_with(10)
        eq_(self.server_requests, {'GET': [self.digest, self.digest]})  # two reqs

    def test_notify_upload_fails(self):
        self.start_server()
        self.server_config['get_fails'] = True
        file = {'algorithm': 'sha512', 'digest': self.digest}
        with BufferHandler.capture('tooltool') as logged:
            tooltool._notify_upload_complete(self.mkurl(''), None, file)
        eq_(self.server_requests, {'GET': [self.digest]})
        eq_(logged, [(logging.ERROR, 'Error making RelengAPI request:')])

    def test_notify_upload_exception(self):
        self.start_server()
        self.server_config['get_fails'] = True
        file = {'algorithm': 'sha512', 'digest': self.digest}
        with BufferHandler.capture('tooltool') as logged:
            with mock.patch('urllib2.urlopen') as urlopen:
                urlopen.side_effect = RuntimeError('oh noes')
                tooltool._notify_upload_complete(self.mkurl(''), None, file)
        eq_(self.server_requests, {})
        eq_(logged[0],
            (logging.ERROR, 'While notifying server of upload completion:'))


def test_log_api_error_generic():
    with BufferHandler.capture('tooltool') as logged:
        tooltool._log_api_error(RuntimeError('uhoh'))
    eq_(logged, [(logging.ERROR, 'Error making RelengAPI request:')])


def test_log_api_error_api_error():
    with BufferHandler.capture('tooltool') as logged:
        fp = cStringIO.StringIO(json.dumps(
            {'error': {'name': 'Bad Request', 'description': 'Nice try'}}))
        exc = urllib2.HTTPError("http://a", 400, "Bad Request",
                                {'content-type': 'application/json'},
                                fp)
        tooltool._log_api_error(exc)
    eq_(logged, [(logging.ERROR, 'Bad Request: Nice try')])


class FetchTests(TestDirMixin, unittest.TestCase):

    _server_files = ['one', 'two', 'three']
    server_files_by_hash = dict((hashlib.sha512(v).hexdigest(), v)
                                for v in _server_files)
    server_corrupt = False
    urls = ['http://a', 'http://2']

    def setUp(self):
        self.setUpTestDir()
        self.cache_dir = os.path.abspath('cache')

    def tearDown(self):
        self.tearDownTestDir()

    def fake_fetch_file(self, urls, file_record, auth_file=None, region=None):
        eq_(urls, self.urls)
        if file_record.digest in self.server_files_by_hash:
            if self.server_corrupt:
                content = 'XXX'
            else:
                content = self.server_files_by_hash[file_record.digest]
            fd, temp_path = tempfile.mkstemp(dir=self.test_dir)
            os.write(fd, content)
            os.close(fd)
            return os.path.split(temp_path)[1]
        else:
            return None

    def add_file_to_dir(self, file, corrupt=False):
        content = 'X' * len(file) if corrupt else file
        open(os.path.join(self.test_dir, "file-" + file), "w").write(content)

    def add_file_to_cache(self, file, corrupt=False):
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
        digest = hashlib.sha512(file).hexdigest()
        content = 'X' * len(file) if corrupt else file
        open(os.path.join(self.cache_dir, digest), "w").write(content)

    def make_manifest(self, filename, *files, **kwargs):
        unpack = kwargs.pop('unpack', False)
        manifest = []
        for file in files:
            manifest.append({
                'filename': 'file-' + file,
                'size': len(file),
                'algorithm': 'sha512',
                'digest': hashlib.sha512(file).hexdigest(),
                'unpack': unpack,
            })
        json.dump(manifest, open(filename, "w"))

    def assert_files(self, *files):
        eq_(sorted([f for f in os.listdir(self.test_dir)
                    if f != 'cache' and not f.endswith('.tt')]),
            sorted(['file-' + f for f in files]))
        for f in files:
            eq_(open('file-' + f).read(), f)

    def assert_cached_files(self, *files):
        if not files and not os.path.exists(self.cache_dir):
            return
        hashes = [hashlib.sha512(f).hexdigest() for f in files]
        eq_(sorted(os.listdir(self.cache_dir)), sorted(hashes))
        for f, h in zip(files, hashes):
            eq_(open(os.path.join(self.cache_dir, h)).read(), f)

    # tests

    def test_no_manifest(self):
        """If the given manifest isn't present, fetch_files fails"""
        eq_(tooltool.fetch_files('not-present.tt', self.urls), False)

    def test_all_present(self):
        """When all expected files are present, fetch_files does not fetch anything"""
        self.add_file_to_dir('one')
        self.add_file_to_dir('two')
        self.make_manifest('manifest.tt', 'one', 'two')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = RuntimeError
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                True)
        self.assert_files('one', 'two')
        self.assert_cached_files()

    def test_all_cached(self):
        """When all expected files are in the cache, fetch_files copies but
        does not fetch"""
        self.add_file_to_cache('one')
        self.add_file_to_cache('two')
        self.make_manifest('manifest.tt', 'one', 'two')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = RuntimeError
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                True)
        self.assert_files('one', 'two')
        self.assert_cached_files('one', 'two')

    def test_all_missing(self):
        """When all expected files are not found, they are fetched."""
        self.make_manifest('manifest.tt', 'one', 'two')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                True)
        self.assert_files('one', 'two')
        self.assert_cached_files('one', 'two')

    def test_missing_not_on_server(self):
        """When the file is missing everywhere including the server, fetch fails"""
        self.make_manifest('manifest.tt', 'ninetynine')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                False)
        self.assert_files()
        self.assert_cached_files()

    def test_missing_corrupt_on_server(self):
        """When the file is missing everywhere and coorrupt the server, fetch fails"""
        self.make_manifest('manifest.tt', 'one')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            self.server_corrupt = True
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                False)
        self.assert_files()
        self.assert_cached_files()

    def test_local_corrupt_but_cached(self):
        """When the local files are corrupt but the cache is OK, the cache is used"""
        self.add_file_to_dir('one', corrupt=True)
        self.add_file_to_cache('one')
        self.make_manifest('manifest.tt', 'one')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = RuntimeError
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                True)
        self.assert_files('one')
        self.assert_cached_files('one')

    def test_local_missing_cache_corrupt(self):
        """When the local files are missing  and the cache is corrupt, fetch"""
        self.add_file_to_cache('one', corrupt=True)
        self.make_manifest('manifest.tt', 'one')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                True)
        self.assert_files('one')
        self.assert_cached_files('one')

    def test_missing_unwritable_cache(self):
        """If fetch downloads files but can't write to the cache, it still succeeds"""
        self.make_manifest('manifest.tt', 'one')
        os.mkdir(self.cache_dir, 0o500)
        try:
            with mock.patch('tooltool.fetch_file') as fetch_file:
                fetch_file.side_effect = self.fake_fetch_file
                eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                    True)
            self.assert_files('one')
            self.assert_cached_files()
        finally:
            os.chmod(self.cache_dir, 0o700)

    def test_mixed(self):
        """fetch creates a dir containing the right files given a mix of file states"""
        self.add_file_to_dir('one', corrupt=True)
        self.add_file_to_cache('two', corrupt=True)
        self.add_file_to_dir('four')
        self.add_file_to_cache('five')
        self.make_manifest('manifest.tt', 'one', 'two', 'three', 'four', 'five')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache'),
                True)
        self.assert_files('one', 'two', 'three', 'four', 'five')
        self.assert_cached_files('one', 'two', 'three', 'five')

    def test_region_arg(self):
        """A region argument passed to fetch_files gets passed on to fetch_file"""
        self.make_manifest('manifest.tt', 'one')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls, cache_folder='cache',
                                     region='ca-north-2'),
                True)
            fetch_file.assert_called_with(self.urls, mock.ANY, auth_file=None,
                                          region='ca-north-2')
        self.assert_files('one')
        self.assert_cached_files('one')

    def test_file_list(self):
        """fetch only fetches the files requested in the file list"""
        self.add_file_to_dir('one')
        self.add_file_to_cache('five')
        self.make_manifest('manifest.tt', 'one', 'five', 'nine')
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            eq_(tooltool.fetch_files('manifest.tt', self.urls,
                                     cache_folder='cache',
                                     filenames=['five']),
                True)
        self.assert_files('one', 'five')
        self.assert_cached_files('five')

    def test_unpack(self):
        """When asked to unpack files, fetch calls untar_file."""
        self.add_file_to_dir('four')
        self.add_file_to_cache('five')
        self.make_manifest('manifest.tt', 'three', 'four', 'five', unpack=True)
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            with mock.patch('tooltool.untar_file') as untar_file:
                eq_(tooltool.fetch_files('manifest.tt', self.urls,
                                         cache_folder='cache'),
                    True)
                untar_file.assert_has_calls([
                    mock.call('file-three'),
                    mock.call('file-four'),
                    mock.call('file-five'),
                ], any_order=True)
        self.assert_files('three', 'four', 'five')
        self.assert_cached_files('three', 'five')

    def test_unpack_fails(self):
        """When asked to unpack files, and the unpack fails, fetch fails."""
        self.make_manifest('manifest.tt', 'one', unpack=True)
        with mock.patch('tooltool.fetch_file') as fetch_file:
            fetch_file.side_effect = self.fake_fetch_file
            with mock.patch('tooltool.untar_file') as untar_file:
                untar_file.side_effect = lambda f: False
                eq_(tooltool.fetch_files('manifest.tt', self.urls,
                                         cache_folder='cache'),
                    False)
                untar_file.assert_called_with('file-one')
        self.assert_files('one')

    def try_untar_file(self, filename):
        os.mkdir('basename')
        open("basename/LEFTOVER.txt", "w").write("rm me")
        self.failUnless(tooltool.untar_file(filename))
        self.failUnless(os.path.exists('basename'))
        self.failUnless(os.path.exists('basename/README.txt'))
        self.failIf(os.path.exists('basename/LEFTOVER.txt'))

    def setup_tarball(self, tar_cmd):
        os.mkdir('basename')
        open("basename/README.txt", "w").write("in tarball")
        os.system(tar_cmd)
        shutil.rmtree('basename')

    def test_untar_file_uncompressed(self):
        self.setup_tarball('tar -cf basename.tar basename')
        self.try_untar_file('basename.tar')

    def test_untar_file_gz(self):
        self.setup_tarball('tar -czf basename.tar.gz basename')
        self.try_untar_file('basename.tar.gz')

    def test_untar_file_xz(self):
        self.setup_tarball('tar -cJf basename.tar.xz basename')
        self.try_untar_file('basename.tar.xz')

    def test_untar_file_bz2(self):
        self.setup_tarball('tar -cjf basename.tar.bz2 basename')
        self.try_untar_file('basename.tar.bz2')

    def test_untar_file_invalid_xz(self):
        self.setup_tarball('echo BOGUS > basename.tar.xz')
        self.assertFalse(tooltool.untar_file('basename.tar.xz'))

    def test_untar_file_not_tarfile(self):
        open('basename.tar.shrink', 'w').write('not a tarfile')
        self.assertFalse(tooltool.untar_file('basename.tar.shrink'))


class FetchFileTests(BaseFileRecordTest):

    def fake_urlopen(self, mock, data, exp_size=4096, exp_auth_file=None):
        self.url_data = data

        def fake_read(url, size):
            eq_(size, exp_size)
            remaining = data[url]
            rv, remaining = remaining[:size], remaining[size:]
            data[url] = remaining
            return rv

        def urlopen(url, auth_file):
            eq_(auth_file, exp_auth_file)
            if url not in data:
                raise urllib2.URLError("bogus url")
            m = mock.Mock()
            m.read = lambda size: fake_read(url, size)
            return m
        mock.side_effect = urlopen

    def test_fetch_file(self):
        with mock.patch('tooltool._urlopen') as _urlopen:
            # the first URL doesn't match, so this loops twice
            self.fake_urlopen(_urlopen, {'http://b/sha512/' + self.sample_hash: 'abcd'})
            filename = tooltool.fetch_file(['http://a', 'http://b'], self.test_record)
            assert filename
            eq_(open(filename).read(), 'abcd')
            os.unlink(filename)

    def test_fetch_file_region(self):
        with mock.patch('tooltool._urlopen') as _urlopen:
            self.fake_urlopen(
                _urlopen, {'http://a/sha512/%s?region=us-west-1' % self.sample_hash: 'abcd'})
            filename = tooltool.fetch_file(['http://a'], self.test_record, region='us-west-1')
            assert filename
            eq_(open(filename).read(), 'abcd')
            os.unlink(filename)

    def test_fetch_file_size(self):
        with mock.patch('tooltool._urlopen') as _urlopen:
            # the first URL doesn't match, so this loops twice
            self.fake_urlopen(
                _urlopen, {'http://b/sha512/' + self.sample_hash: 'abcd'}, exp_size=1024)
            filename = tooltool.fetch_file(
                ['http://a', 'http://b'], self.test_record, grabchunk=1024)
            assert filename
            eq_(open(filename).read(), 'abcd')
            os.unlink(filename)

    def test_fetch_file_auth_file(self):
        with mock.patch('tooltool._urlopen') as _urlopen:
            # the first URL doesn't match, so this loops twice
            self.fake_urlopen(_urlopen, {'http://b/sha512/' + self.sample_hash: 'abcd'},
                              exp_auth_file='auth')
            filename = tooltool.fetch_file(
                ['http://a', 'http://b'], self.test_record, auth_file='auth')
            assert filename
            eq_(open(filename).read(), 'abcd')
            os.unlink(filename)

    def test_fetch_file_fails(self):
        with mock.patch('tooltool._urlopen') as _urlopen:
            self.fake_urlopen(_urlopen, {})
            filename = tooltool.fetch_file(['http://a'], self.test_record)
            assert filename is None


def test_urlopen_no_auth_file():
    with mock.patch("urllib2.urlopen") as urlopen:
        tooltool._urlopen("url")
        urlopen.assert_called_with("url")


def test_touch():
    open("testfile", "w")
    os.utime("testfile", (0, 0))
    tooltool.touch("testfile")
    assert os.stat("testfile").st_mtime > 0
    os.unlink("testfile")


def test_touch_doesnt_exit():
    assert not os.path.exists("testfile")
    tooltool.touch("testfile")
    assert not os.path.exists("testfile")


class PurgeTests(TestDirMixin, unittest.TestCase):

    def setUp(self):
        self.setUpTestDir()

    def tearDown(self):
        self.tearDownTestDir()

    def fake_freespace(self, p):
        # A fake 10G drive, with each file = 1G
        eq_(p, self.test_dir)
        return 1024 ** 3 * (10 - len(os.listdir(self.test_dir)))

    def add_files(self, *files):
        now = 1426127031
        # add files, with ordered mtime
        for f in files:
            path = os.path.join(self.test_dir, f)
            open(path, "w")
            os.utime(path, (now, now))
            now += 10

    def test_purge_fails(self):
        path = os.path.join(self.test_dir, 'sticky')
        open(path, 'w')
        os.chmod(self.test_dir, 0o500)  # prevent delete
        try:
            tooltool.purge(self.test_dir, 0)
            eq_(os.listdir(self.test_dir), ['sticky'])
        finally:
            os.chmod(self.test_dir, 0o700)

    def test_purge_nonfile_not_deleted(self):
        path = os.path.join(self.test_dir, 'somedir')
        os.mkdir(path)
        tooltool.purge(self.test_dir, 0)
        eq_(os.listdir(self.test_dir), ['somedir'])

    def test_purge_nonzero(self):
        # six files means six gigs consumed, so we'll delete two
        self.add_files("one", "two", "three", "four", "five", "six")
        with mock.patch('tooltool.freespace') as freespace:
            freespace.side_effect = self.fake_freespace
            tooltool.purge(self.test_dir, 6)
        eq_(sorted(os.listdir(self.test_dir)),
            sorted(['three', 'four', 'five', 'six']))

    def test_purge_no_need(self):
        self.add_files("one", "two")
        with mock.patch('tooltool.freespace') as freespace:
            freespace.side_effect = self.fake_freespace
            tooltool.purge(self.test_dir, 4)
        eq_(sorted(os.listdir(self.test_dir)),
            sorted(['one', 'two']))

    def test_purge_zero(self):
        self.add_files("one", "two", "three")
        tooltool.purge(self.test_dir, 0)
        eq_(os.listdir(self.test_dir), [])

    def test_freespace(self):
        # we can't set up a dedicated partition for this test, so just assume
        # the disk isn't full (other tests assume this too, really)
        assert tooltool.freespace(self.test_dir) > 0


class AddFiles(BaseManifestTest):

    def assert_manifest(self, exp_manifest, manifest=None):
        got_manifest = json.load(open(manifest or self.sample_manifest_file))
        got_manifest.sort(key=lambda f: f['digest'])
        exp_manifest.sort(key=lambda f: f['digest'])
        eq_(got_manifest, exp_manifest)

    def make_file(self, filename="a_file"):
        data = os.urandom(100)
        open(filename, "w").write(data)
        return {
            'filename': filename,
            'algorithm': 'sha512',
            'digest': hashlib.sha512(data).hexdigest(),
            'size': len(data)
        }

    def test_append(self):
        """Adding a new file to an existing manifest results in a manifest with
        two files"""
        file_json = self.make_file()
        assert tooltool.add_files('manifest.tt', 'sha512', [file_json['filename']], None)
        self.assert_manifest([self.test_record_json, file_json])

    def test_append_internal(self):
        """Adding a new file to an existing manifest results in a manifest with
        two files, with the visibility set on the new one"""
        file_json = self.make_file()
        file_json['visibility'] = 'internal'
        assert tooltool.add_files('manifest.tt', 'sha512', [file_json['filename']], 'internal')
        self.assert_manifest([self.test_record_json, file_json])

    def test_append_public(self):
        """Adding a new file to an existing manifest results in a manifest with
        two files, with the visibility set on the new one"""
        file_json = self.make_file()
        file_json['visibility'] = 'public'
        assert tooltool.add_files('manifest.tt', 'sha512', [file_json['filename']], 'public')
        self.assert_manifest([self.test_record_json, file_json])

    def test_new_manifest(self):
        """Adding a new file to a new manifest results in a manifest with one
        file"""
        file_json = self.make_file()
        assert tooltool.add_files('new_manifest.tt', 'sha512', [file_json['filename']], None)
        self.assert_manifest([file_json], manifest='new_manifest.tt')

    def test_file_already_exists(self):
        """Adding a file to a manifest that is already in that manifest fails"""
        assert not tooltool.add_files('manifest.tt', 'sha512',
                                      [os.path.join(os.path.dirname(__file__),
                                                    self.sample_file)], None)
        self.assert_manifest([self.test_record_json])

    def test_filename_already_exists(self):
        """Adding a file to a manifest that has the same name as an existing
        file fails"""
        self.make_file(self.sample_file)
        assert not tooltool.add_files('manifest.tt', 'sha512',
                                      [self.sample_file], None)
        self.assert_manifest([self.test_record_json])


class ValidateManifest(BaseManifestTest):

    def test_validate_exists(self):
        sample_file_src = os.path.join(os.path.dirname(__file__), self.sample_file)
        shutil.copyfile(sample_file_src, self.sample_file)
        assert tooltool.validate_manifest('manifest.tt')

    def test_validate_missing_files(self):
        assert not tooltool.validate_manifest('manifest.tt')

    def test_validate_invalid_files(self):
        open(self.sample_file, "w").write("BOGUS")
        assert not tooltool.validate_manifest('manifest.tt')

    def test_validate_invalid_manifest(self):
        open('manifest.tt', "w").write("BOGUS")
        assert not tooltool.validate_manifest('manifest.tt')


class ListManifest(BaseManifestTest):

    def test_list(self):
        # add two files
        open("foo.txt", "w").write("FOO!")
        open("bar.txt", "w").write("BAR!")
        tooltool.add_files('manifest.tt', 'sha512', ['foo.txt', 'bar.txt'], None)
        open("bar.txt", "w").write("bar is invalid")
        old_stdout = sys.stdout
        sys.stdout = cStringIO.StringIO()
        try:
            assert tooltool.list_manifest('manifest.tt')
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
        eq_(sorted(output.strip().split('\n')), sorted([
            '-\t-\ttest_file.ogg',
            'P\t-\tbar.txt',
            'P\tV\tfoo.txt',
        ]))

    def test_list_invalid_manifest(self):
        open("manifest.tt", "w").write("BOGUS")
        assert not tooltool.list_manifest("manifest.tt")
