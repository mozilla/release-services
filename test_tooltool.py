# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import json
import os
import shutil
import tempfile
import unittest

import tooltool


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

# Ugh, I've managed to have a few different test naming schemes already :(
# TODO: clean this up!


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

    def test_inequality(self):
        for i in ['filename', 'size', 'algorithm', 'digest']:
            test_record2 = copy.deepcopy(self.test_record)
            test_record2.__dict__[i] = 'wrong!'
            self.assertNotEqual(self.test_record, test_record2)

    def test_repr(self):
        a = eval(repr(self.test_record))
        self.assertEqual(str(a), str(self.test_record))
        # TODO: Figure out why things aren't working here
        #self.assertEqual(a, self.test_record)

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
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(getattr(f, i), self.test_record.__dict__[i])

    def test_json_dumps(self):
        json_string = json.dumps(
            self.test_record, cls=tooltool.FileRecordJSONEncoder)
        dict_from_json = json.loads(json_string)
        for i in ['filename', 'size', 'algorithm', 'digest']:
            self.assertEqual(dict_from_json[i], self.test_record.__dict__[i])

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

    def test_incorrect_digest(self):
        self.test_manifest.file_records[1].digest = 'wrong'
        self.assertFalse(self.test_manifest.validate_digests())

    def test_equality_same_object(self):
        self.assertEqual(self.test_manifest, self.test_manifest)

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


class TestManifestOperations(BaseFileRecordTest):

    def setUp(self):
        BaseFileRecordTest.setUp(self)
        self.sample_manifest = tooltool.Manifest([self.test_record])
        self.sample_manifest_file = '.testmanifest'
        self.test_dir = 'test-dir'
        self.startingwd = os.getcwd()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.mkdir(self.test_dir)
        with open(os.path.join(self.test_dir, self.sample_manifest_file), 'w') as tmpfile:
            self.sample_manifest.dump(tmpfile, fmt='json')

    def tearDown(self):
        os.chdir(self.startingwd)
        shutil.rmtree(self.test_dir)
