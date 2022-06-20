# coding=utf-8
#__author__ = 'Author'
#__date__ = '2022-02-18'
#__copyright__ = 'Copyright 2022, DMI'

import unittest

from qgis.PyQt.QtGui import QIcon



class DMIOpenDataDialogTest(unittest.TestCase):
    """Test rerources work."""

    def setUp(self):
        """Runs before each test."""
        pass

    def tearDown(self):
        """Runs after each test."""
        pass

    def test_icon_png(self):
        """Test we can click OK."""
        path = ':/plugins/DMIOpenData/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())

if __name__ == "__main__":
    suite = unittest.makeSuite(DMIOpenDataResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)



