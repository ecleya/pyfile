import os
import unittest

from pyfileinfo import PyFileInfo, YAML
from tests import DATA_ROOT


class TestJSON(unittest.TestCase):
    def test_dict_yaml_file(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.yml'))
        self.assertTrue(isinstance(file.instance, YAML))

    def test_list_yaml_file(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'list.yml'))
        self.assertTrue(isinstance(file.instance, YAML))

    def test_is_yaml(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'list.yml'))
        self.assertTrue(file.is_yaml())

        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.yml'))
        self.assertTrue(file.is_yaml())

    def test_yaml_act_like_dict(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'dict.yml'))
        self.assertEqual(file['women'], ['Mary Smith', 'Susan Williams'])

    def test_yaml_act_like_list(self):
        file = PyFileInfo(os.path.join(DATA_ROOT, 'list.yml'))
        self.assertEqual(file[0], {'age': 33, 'name': 'John Smith'})
