import unittest
import os
from PyQt5 import uic

class TestDMIDialogUi(unittest.TestCase):
    def test_DMI_Open_Data_dialog_base_ui_file_compiles(self):
        WIDGET, BASE = uic.loadUiType(
            os.path.join(os.path.dirname(__file__), '..', 'DMI_Open_Data_dialog_base.ui')
        )
        assert WIDGET is not None
        assert BASE is not None
