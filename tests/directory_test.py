import os
import unittest

from pyfile import pyfile, Directory
from tests import DATA_ROOT


class TestDirectory(unittest.TestCase):
    def test_directory(self):
        directory = pyfile(DATA_ROOT)
        self.assertTrue(isinstance(directory, Directory))

    def test_is_directory(self):
        directory = pyfile(DATA_ROOT)
        self.assertTrue(directory.is_directory())

    def test_files(self):
        file = pyfile(DATA_ROOT)
        self.assertEqual(len(list(file.files())), 6)

    def test_walk(self):
        file = pyfile(DATA_ROOT)
        self.assertEqual(len(list(file.walk())), 12)

    def test_size(self):
        file = pyfile(os.path.join(DATA_ROOT))
        self.assertEqual(file.size, 128007)
