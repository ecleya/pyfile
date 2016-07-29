import os
import unittest

from pyfile import pyfile
from tests import DATA_ROOT


class TestFile(unittest.TestCase):
    def test_properties(self):
        file = pyfile(os.path.join(DATA_ROOT, 'dict.json'))
        self.assertEqual(file.path, os.path.join(DATA_ROOT, 'dict.json'))
        self.assertEqual(file.name, 'dict.json')
        self.assertEqual(file.body.path, DATA_ROOT)
        self.assertEqual(file.extension, '.json')

    def test_not_exists_file(self):
        self.assertRaises(FileNotFoundError, pyfile, os.path.join(DATA_ROOT, 'not exists.txt'))
