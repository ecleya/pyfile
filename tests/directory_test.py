# -*- coding: utf-8 -*-

import os
import unittest

from pyfileinfo import PyFileInfo, Directory
from tests import DATA_ROOT


class TestDirectory(unittest.TestCase):
    def test_directory(self):
        directory = PyFileInfo(DATA_ROOT)
        self.assertTrue(isinstance(directory.instance, Directory))

    def test_is_directory(self):
        directory = PyFileInfo(DATA_ROOT)
        self.assertTrue(directory.is_directory())

    def test_files_in(self):
        file = PyFileInfo(DATA_ROOT)
        self.assertEqual(len(list(file.files_in())), 9)

    def test_recursive_files_in(self):
        file = PyFileInfo(DATA_ROOT)
        self.assertEqual(len(list(file.files_in(recursive=True))), 15)

    def test_hidden_file(self):
        file = PyFileInfo(DATA_ROOT)
        self.assertEqual(len(list(file.files_in(include_hidden_file=True))), 10)

    def test_size(self):
        file = PyFileInfo(os.path.join(DATA_ROOT))
        self.assertEqual(file.size, 128149)
