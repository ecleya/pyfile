import os
import unittest

from pyfileinfo import PyFileInfo, Json
from tests import DATA_ROOT


class TestJson(unittest.TestCase):
    def test_dict_json_file(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.json'))
        self.assertTrue(isinstance(file.instance, Json))

    def test_list_json_file(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'list.json'))
        self.assertTrue(isinstance(file.instance, Json))

    def test_is_json(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'list.json'))
        self.assertTrue(file.is_json())

        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.json'))
        self.assertTrue(file.is_json())

    def test_dict_json_access(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.json'))
        self.assertEqual(file['a'], 1)

    def test_list_json_access(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'list.json'))
        self.assertEqual(file[0], {"a": 1, "b": 2})
