# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = "kalmykovstepan4@gmail.com"
__date__ = "2026-09-28"
__copyright__ = "Copyright 2026, KalmikovStepan"

import os
import tempfile
import unittest
from unittest import mock

from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from utilities import get_qgis_app

from clip_reproject_dialog import ClipReprojectDialog

QGIS_APP = get_qgis_app()

if Qgis.QGIS_VERSION_INT >= 40000:
    OK_BUTTON = QDialogButtonBox.StandardButton.Ok
    CANCEL_BUTTON = QDialogButtonBox.StandardButton.Cancel
    ACCEPTED = QDialog.DialogCode.Accepted
    REJECTED = QDialog.DialogCode.Rejected
else:
    OK_BUTTON = QDialogButtonBox.Ok
    CANCEL_BUTTON = QDialogButtonBox.Cancel
    ACCEPTED = QDialog.Accepted
    REJECTED = QDialog.Rejected


class ClipReprojectDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = ClipReprojectDialog(None)
        self.tmp = tempfile.TemporaryDirectory()
        self.osm_dir = os.path.join(self.tmp.name, "osm")
        os.makedirs(self.osm_dir)
        self.adm_file = os.path.join(self.tmp.name, "boundary.shp")
        open(self.adm_file, "w").close()
        # Validation errors open a modal QMessageBox; replace it so tests don't block.
        patcher = mock.patch("clip_reproject_dialog.QtWidgets.QMessageBox.warning")
        self.warning = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None
        self.tmp.cleanup()

    def fill_valid_inputs(self):
        """Fill the dialog with values that pass validation."""
        self.dialog.osm_path.setFilePath(self.osm_dir)
        self.dialog.adm_shp.setFilePath(self.adm_file)
        self.dialog.epsg_code.setText("4326")
        self.dialog.result_path.setFilePath(os.path.join(self.tmp.name, "out"))

    def test_dialog_ok(self):
        """Test we can click OK when the input is valid."""
        self.fill_valid_inputs()
        self.dialog.button_box.button(OK_BUTTON).click()
        self.assertEqual(self.dialog.result(), ACCEPTED)
        self.warning.assert_not_called()

    def test_dialog_ok_empty_input(self):
        """Test OK with empty fields shows an error and keeps the dialog open."""
        self.dialog.button_box.button(OK_BUTTON).click()
        self.assertNotEqual(self.dialog.result(), ACCEPTED)
        self.warning.assert_called_once()

    def test_validate_epsg(self):
        """Test a non-numeric EPSG code is rejected."""
        self.fill_valid_inputs()
        self.dialog.epsg_code.setText("abc")
        self.assertEqual(self.dialog.validate_inputs(), "EPSG-код должен быть целым числом.")

    def test_validate_filter_pair(self):
        """Test the filter needs both a field and a value."""
        self.fill_valid_inputs()
        self.dialog.field_name.setText("name")
        self.assertEqual(
            self.dialog.validate_inputs(),
            "Для фильтра территории заполните и поле, и значение.",
        )

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        self.dialog.button_box.button(CANCEL_BUTTON).click()
        self.assertEqual(self.dialog.result(), REJECTED)


if __name__ == "__main__":
    suite = unittest.makeSuite(ClipReprojectDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
