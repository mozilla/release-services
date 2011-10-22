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


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
cf = logging.Formatter("%(pathname)s - %(levelname)s - %(message)s")
ch.setFormatter(cf)
log.addHandler(ch)
unittest.main()
