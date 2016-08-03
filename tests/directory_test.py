import unittest

from pyfile import pyfile, Directory
from tests import DATA_ROOT


class TestDirectory(unittest.TestCase):
    def test_directory(self):
        directory = pyfile(DATA_ROOT)
        self.assertTrue(isinstance(directory, Directory))

    def test_files(self):
        file = pyfile(DATA_ROOT)
        self.assertEqual(len(file.files()), 3)
