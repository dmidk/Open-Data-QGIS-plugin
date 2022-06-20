# coding=utf-8
#__author__ = 'Author'
#__date__ = '2022-02-18'
#__copyright__ = 'Copyright 2022, DMI'

import unittest

from qgis.PyQt.QtGui import QDialogButtonBox, QDialog

from DMI_Open_Data_dialog import DMIOpenDataDialog

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class DMIOpenDataDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = DMIOpenDataDialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""

        button = self.dialog.button_box.button(QDialogButtonBox.Ok)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Accepted)

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        button = self.dialog.button_box.button(QDialogButtonBox.Cancel)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Rejected)

if __name__ == "__main__":
    suite = unittest.makeSuite(DMIOpenDataDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

