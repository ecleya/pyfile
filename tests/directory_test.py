import unittest

from pyfile import pyfile
from tests import DATA_ROOT


class TestDirectory(unittest.TestCase):
    def test_files(self):
        file = pyfile(DATA_ROOT)
        self.assertEqual(len(file.files()), 1)
