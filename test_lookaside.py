import sys
import os
import unittest
import logging
import shutil
import tempfile

# We want access to the module we are testing
sys.path.append('.')
import lookaside
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class Hashing(unittest.TestCase):
    def setUp(self):
        self.sample_data = open('test_file.ogg')
        self.sample_algo = 'sha1'
        self.sample_hash = 'de3e3bbffd83c328ad7d9537ad2d03f68fc02e52'

    def test_hash_file(self):
        test_hash = lookaside.hash_file(self.sample_data, self.sample_algo)
        self.assertEqual(test_hash, self.sample_hash)

class TestFileRecord(unittest.TestCase):
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



log = logging.getLogger(__name__)
aside_log = logging.getLogger(lookaside.__name__)
log.setLevel(logging.DEBUG)
aside_log.setLevel(logging.WARN)
ch = logging.StreamHandler()
cf = logging.Formatter("%(pathname)s - %(levelname)s - %(message)s")
ch.setFormatter(cf)
log.addHandler(ch)
aside_log.addHandler(ch)
unittest.main()
