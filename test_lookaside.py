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
        self.sample_digest = 'de3e3bbffd83c328ad7d9537ad2d03f68fc02e52'

    def test_digest_file(self):
        test_digest = lookaside.digest_file(self.sample_data, self.sample_algo)
        self.assertEqual(test_digest, self.sample_digest)

#Ugh, I've managed to have a few different test naming schemes already :(
#TODO: clean this up!

class BaseFileRecordTest(unittest.TestCase):
    def setUp(self):
        self.sample_file = 'test_file.ogg'
        self.sample_algo = 'sha1'
        self.sample_size = os.path.getsize(self.sample_file)
        with open(self.sample_file) as f:
            self.sample_hash = lookaside.digest_file(f, self.sample_algo)
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

class BaseFileRecordListTest(BaseFileRecordTest):
    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.record_list = []
        for i in range(0,4):
            record = copy.deepcopy(self.test_record)
            record.algorithm = i
            self.record_list.append(record)


class TestFileRecord(BaseFileRecordTest):
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
        self.assertRaises(lookaside.MissingFileException,self.test_record.validate_size)

    def test_valid_digest(self):
        self.assertTrue(self.test_record.validate_digest())

    def test_invalid_digest(self):
        self.test_record.digest = 'NotValidDigest'
        self.assertFalse(self.test_record.validate_digest())

    def test_digest_of_missing_file(self):
        self.test_record.filename = self.absent_file
        self.assertRaises(lookaside.MissingFileException,self.test_record.validate_digest)

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
        self.assertRaises(lookaside.MissingFileException,self.test_record.validate)

    def test_equality(self):
        test_record2 = copy.deepcopy(self.test_record)
        self.assertEqual(self.test_record, test_record2)
        self.assertEqual(self.test_record, self.test_record)

    def test_inequality(self):
        for i in ['filename', 'size', 'algorithm', 'digest']:
            test_record2 = copy.deepcopy(self.test_record)
            test_record2.__dict__[i] = 'wrong!'
            self.assertNotEqual(self.test_record, test_record2)

    def test_repr(self):
        a = eval(repr(self.test_record))
        self.assertEqual(str(a), str(self.test_record))
        #TODO: Figure out why things aren't working here
        #self.assertEqual(a, self.test_record)

class TestFileRecordJSONCodecs(BaseFileRecordListTest):
    def test_default(self):
        encoder = lookaside.FileRecordJSONEncoder()
        dict_from_encoder = encoder.default(self.test_record)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(dict_from_encoder[i], self.test_record.__dict__[i])

    def test_default_list(self):
        encoder = lookaside.FileRecordJSONEncoder()
        new_list = encoder.default(self.record_list)
        for record in range(0,len(self.record_list)):
            self.assertEqual(new_list[record],
                             encoder.default(self.record_list[record]))

    def test_unrelated_class(self):
        encoder = lookaside.FileRecordJSONEncoder()
        class Junk: pass
        self.assertRaises(
                lookaside.FileRecordJSONEncoderException,
                encoder.default,
                Junk()
        )

    def test_list_with_unrelated_class(self):
        encoder = lookaside.FileRecordJSONEncoder()
        class Junk: pass
        self.assertRaises(
                lookaside.FileRecordJSONEncoderException,
                encoder.default,
                [self.test_record, Junk(), self.test_record],
        )

    def test_decode(self):
        json_string = json.dumps(self.test_record, cls=lookaside.FileRecordJSONEncoder)
        decoder = lookaside.FileRecordJSONDecoder()
        f=decoder.decode(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(getattr(f,i), self.test_record.__dict__[i])

    def test_json_dumps(self):
        json_string = json.dumps(self.test_record, cls=lookaside.FileRecordJSONEncoder)
        dict_from_json = json.loads(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(dict_from_json[i], self.test_record.__dict__[i])

    def test_decode_list(self):
        json_string = json.dumps(self.record_list, cls=lookaside.FileRecordJSONEncoder)
        new_list = json.loads(json_string, cls=lookaside.FileRecordJSONDecoder)
        self.assertEquals(len(new_list), len(self.record_list))
        for record in range(0,len(self.record_list)):
            self.assertEqual(new_list[record], self.record_list[record])



class TestAsideFile(BaseFileRecordTest):
    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.other_sample_file = 'other-%s' % self.sample_file
        if os.path.exists(self.other_sample_file):
            os.remove(self.other_sample_file)
        shutil.copyfile(self.sample_file, self.other_sample_file)
        self.other_test_record = copy.deepcopy(self.test_record)
        self.other_test_record.filename = self.other_sample_file
        self.test_aside = lookaside.AsideFile([self.test_record, self.other_test_record])

    def test_present(self):
        self.assertTrue(self.test_aside.present())

    def test_absent(self):
        os.remove(self.other_sample_file)
        self.assertFalse(self.test_aside.present())

    def test_validate_sizes(self):
        self.assertTrue(self.test_aside.validate_sizes())

    def test_incorrect_size(self):
        self.test_aside.file_records[1].size = 1
        self.assertFalse(self.test_aside.validate_sizes())

    def test_validate_digest(self):
        self.assertTrue(self.test_aside.validate_digests())

    def test_incorrect_digest(self):
        self.test_aside.file_records[1].digest = 'wrong'
        self.assertFalse(self.test_aside.validate_digests())

    def test_equality_same_object(self):
        self.assertEqual(self.test_aside, self.test_aside)

    def test_equality_deepcopy(self):
        a_deepcopy = copy.deepcopy(self.test_aside)
        self.assertEqual(self.test_aside,a_deepcopy)

    def test_equality_copy_method(self):
        a_copy = self.test_aside.copy()
        self.assertEqual(self.test_aside,a_copy)

    def test_equality_unrelated(self):
        one = lookaside.AsideFile([self.test_record, self.other_test_record])
        two = lookaside.AsideFile([self.test_record, self.other_test_record])
        self.assertEqual(one,two)

    def test_json_file(self):
        tmpaside = tempfile.TemporaryFile()
        self.test_aside.dump(tmpaside, fmt='json')
        tmpaside.seek(0)
        new_aside = lookaside.AsideFile()
        new_aside.load(tmpaside, fmt='json')
        self.assertEqual(new_aside, self.test_aside)

    def test_json_file(self):
        s = self.test_aside.dumps(fmt='json')
        new_aside = lookaside.AsideFile()
        new_aside.loads(s, fmt='json')
        self.assertEqual(new_aside, self.test_aside)

class TestAsideFileOperations(BaseFileRecordTest):
    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.sample_aside = lookaside.AsideFile([self.test_record])
        self.sample_aside_file = '.testaside'
        self.test_dir = 'test-dir'
        self.startingwd = os.getcwd()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.mkdir(self.test_dir)
        with open(os.path.join(self.test_dir, self.sample_aside_file), 'w') as tmpfile:
            self.sample_aside.dump(tmpfile, fmt='json')

    def tearDown(self):
        os.chdir(self.startingwd)
        shutil.rmtree(self.test_dir)

    def create_test_dirs(self, root, dirnames):
        """In root, create and pupulate dirs named dirnames.
        I blow away and recreate the root.  I return the list
        of aside files copied"""
        if os.path.exists(root): shutil.rmtree(root)
        os.mkdir(root)
        rv = []
        for (loc, copyfiles) in dirnames:
            copydir = os.path.join(root, loc)
            os.mkdir(copydir)
            if copyfiles:
                shutil.copy(self.sample_aside_file, copydir)
                shutil.copy(self.sample_aside.file_records[0].filename, copydir)
                rv.append(os.path.join(copydir, self.sample_aside_file))
        return rv




    def test_sample_aside(self):
        self.assertTrue(self.sample_aside.validate())

    def test_find_single_aside(self):
        f=lookaside.find_aside_files([self.test_dir], aside_filename=self.sample_aside_file)
        expected = os.path.join(self.test_dir, self.sample_aside_file)
        self.assertEqual(f, [expected])

    def test_find_aside_recursively(self):
        expected = self.create_test_dirs(self.test_dir, [('a', True), ('b', True)])
        f=lookaside.find_aside_files(
                [self.test_dir],
                aside_filename=self.sample_aside_file,
                recurse=True)
        self.assertEqual(f, expected)

    def test_find_aside_missing(self):
        expected = self.create_test_dirs(self.test_dir,
                [('a', True), ('b', False), (os.path.join('b','c'), True)])
        f=lookaside.find_aside_files(
                [self.test_dir],
                aside_filename=self.sample_aside_file,
                recurse=True)
        self.assertEqual(f, expected)




log = logging.getLogger(lookaside.__name__)
log.setLevel(logging.ERROR)
log.addHandler(logging.StreamHandler())

unittest.main()
