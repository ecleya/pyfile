import os
import unittest

from pyfile import pyfile, Image
from tests import DATA_ROOT


class TestImage(unittest.TestCase):
    def test_image(self):
        image = pyfile(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertTrue(isinstance(image, Image))

    def test_image_properties(self):
        image = pyfile(os.path.join(DATA_ROOT, '5x5.jpg'))
        self.assertEqual(image.width, 5)
        self.assertEqual(image.height, 5)