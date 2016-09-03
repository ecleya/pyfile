import os
import unittest

from pyfile import pyfile, Image
from tests import DATA_ROOT


class TestImage(unittest.TestCase):
    def test_image(self):
        image = pyfile(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertTrue(isinstance(image, Image))

    def test_is_image(self):
        image = pyfile(os.path.join(DATA_ROOT, '5x5.jpg'))
        print(type(image))
        print(image.is_image)
        self.assertTrue(image.is_image())

    def test_image_properties(self):
        image = pyfile(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertEqual(image.width, 5)
        self.assertEqual(image.height, 5)