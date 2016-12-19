import os
import unittest

from pyfileinfo import PyFileInfo, Image
from tests import DATA_ROOT


class TestImage(unittest.TestCase):
    def test_image(self):
        image = PyFileInfo(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertTrue(isinstance(image.instance, Image))

    def test_is_image(self):
        image = PyFileInfo(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertTrue(image.is_image())

    def test_image_properties(self):
        image = PyFileInfo(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertEqual(image.width, 5)
        self.assertEqual(image.height, 5)
