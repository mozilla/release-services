import sys
import os
import unittest
import logging
import shutil
import tempfile
import copy
try: import simplejson as json
except ImportError: import json

# We want access to the module we are testing
sys.path.append('.')
import lookaside
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.sample_data = open('test_file.ogg')
        self.sample_algo = 'sha1'
        self.sample_hash = 'de3e3bbffd83c328ad7d9537ad2d03f68fc02e52'

    def test_hash_file(self):
        test_hash = lookaside.hash_file(self.sample_data, self.sample_algo)
        self.assertEqual(test_hash, self.sample_hash)

class BaseFileRecordTest(unittest.TestCase):
    def setUp(self):
        self.sample_file = 'test_file.ogg'
        self.sample_algo = 'sha1'
        self.sample_size = os.path.getsize(self.sample_file)
        with open(self.sample_file) as f:
            self.sample_hash = lookaside.hash_file(f, self.sample_algo)
        self.test_record = lookaside.FileRecord(
                filename=self.sample_file,
                size=self.sample_size,
                digest=self.sample_hash,
                algorithm=self.sample_algo
        )
        # using mkstemp to ensure that the filename generated
        # isn't actually on the system.
        (tmpfd, filename) = tempfile.mkstemp()
        os.close(tmpfd)
        os.remove(filename)
        if os.path.exists(filename):
            self.fail('did not remove %s' % filename)
        self.absent_file = filename

class FileRecordTests(BaseFileRecordTest):
    def test_FileRecord_present(self):
        # this test feels silly, but things are built on this
        # method, so probably best to test it
        self.assertTrue(self.test_record.present())
        self.test_record.filename = self.absent_file
        self.assertFalse(self.test_record.present())

    def test_FileRecord_validate_size(self):
        self.assertTrue(self.test_record.validate_size())
        self.test_record.size += 1
        self.assertFalse(self.test_record.validate_size())
        self.test_record.filename = self.absent_file
        self.assertRaises(lookaside.MissingFileException,self.test_record.validate_size)

    def test_FileRecord_validate_digest(self):
        self.assertTrue(self.test_record.validate_digest())
        self.test_record.digest = 'NotValidDigest'
        self.assertFalse(self.test_record.validate_digest())
        self.test_record.filename = self.absent_file
        self.assertRaises(lookaside.MissingFileException,self.test_record.validate_digest)

    def test_FileRecord_validate(self):
        self.assertTrue(self.test_record.validate())
        self.test_record.digest = 'NotValidDigest'
        self.assertFalse(self.test_record.validate())
        self.test_record.filename = self.absent_file
        self.assertRaises(lookaside.MissingFileException,self.test_record.validate)

class TestFileRecordJSONEncoder(BaseFileRecordTest):
    def test_default(self):
        encoder = lookaside.FileRecordJSONEncoder()
        dict_from_encoder = encoder.default(self.test_record)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(dict_from_encoder[i], self.test_record.__dict__[i])

    def test_unrelated_class(self):
        encoder = lookaside.FileRecordJSONEncoder()
        class Junk: pass
        self.assertRaises(
                lookaside.FileRecordJSONEncoderException,
                encoder.default,
                Junk()
        )

    def test_json_dumps(self):
        json_string = json.dumps(self.test_record, cls=lookaside.FileRecordJSONEncoder)
        dict_from_json = json.loads(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(dict_from_json[i], self.test_record.__dict__[i])

class FileRecordJSONDecoder(BaseFileRecordTest):
    def test_decode(self):
        json_string = json.dumps(self.test_record, cls=lookaside.FileRecordJSONEncoder)
        decoder = lookaside.FileRecordJSONDecoder()
        f=decoder.decode(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(getattr(f,i), self.test_record.__dict__[i])

    def test_decode_list(self):
        record_list = []
        for i in range(0,4):
            record = copy.deepcopy(self.test_record)
            record.filename = i
            record_list.append(record)
        json_string = json.dumps(record_list, cls=lookaside.FileRecordJSONEncoder)
        new_list = json.loads(json_string, cls=lookaside.FileRecordJSONDecoder)
        self.assertEquals(len(new_list), len(record_list))
        for record in range(0,len(record_list)):
            for i in ['filename', 'size', 'algorithm', 'digest']:
                self.assertEqual(getattr(record_list[record],i),
                                 getattr(new_list[record],i))





unittest.main()
