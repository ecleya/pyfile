# -*- coding: utf-8 -*-

import os
import unittest

from pyfileinfo import PyFileInfo
from tests import DATA_ROOT


class TestFile(unittest.TestCase):
    def test_properties(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.json'))
        self.assertEqual(file.path, os.path.join(DATA_ROOT, 'dict.json'))
        self.assertEqual(file.name, 'dict.json')
        self.assertEqual(file.body.path, DATA_ROOT)
        self.assertEqual(file.extension, '.json')

    def test_not_exists_file(self):
        file = PyFileInfo('not exists.txt')
        self.assertFalse(file.is_exists())

    def test_equality_same_path(self):
        file1 = PyFileInfo(os.path.join(DATA_ROOT, 'text_files', 'original.txt'))
        file2 = PyFileInfo(os.path.join(DATA_ROOT, 'text_files', 'original.txt'))

        self.assertTrue(file1 == file2)
        self.assertTrue(file1 == os.path.join(DATA_ROOT, 'text_files', 'original.txt'))

    def test_equality_same_file(self):
        file1 = PyFileInfo(os.path.join(DATA_ROOT, 'text_files', 'original.txt'))
        file2 = PyFileInfo(os.path.join(DATA_ROOT, 'text_files', 'same.txt'))

        self.assertTrue(file1 == file2)
        self.assertTrue(file1 == os.path.join(DATA_ROOT, 'text_files', 'same.txt'))

    def test_equality_different_file(self):
        file1 = PyFileInfo(os.path.join(DATA_ROOT, 'text_files', 'original.txt'))
        file2 = PyFileInfo(os.path.join(DATA_ROOT, 'text_files', 'diff.txt'))

        self.assertTrue(file1 != file2)
        self.assertTrue(file1 != os.path.join(DATA_ROOT, 'text_files', 'diff_size.txt'))

    def test_md5(self):
        md5 = PyFileInfo(os.path.join(DATA_ROOT, 'md5_bc67678e92933a5f1c60ac5a7f65f9bb'))
        self.assertEqual(md5.md5, 'bc67678e92933a5f1c60ac5a7f65f9bb')
