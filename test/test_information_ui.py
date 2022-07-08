import unittest
import os
from PyQt5 import uic

class TestSettingsUi(unittest.TestCase):
    def test_settings_ui_file_compiles(self):
        WIDGET, BASE = uic.loadUiType(
            os.path.join(os.path.dirname(__file__), '..', 'dmi_dialog_tabs', 'information', 'information.ui')
        )
        assert WIDGET is not None
        assert BASE is not None
