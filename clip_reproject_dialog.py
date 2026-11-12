# -*- coding: utf-8 -*-
"""Dialog and input validation for the Clip Reproject QGIS plugin."""

import os

from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt import QtWidgets, uic

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "clip_reproject_dialog_base.ui"),
    from_imports=True,
    import_from="clip_reproject",
)


class ClipReprojectDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog that checks user input before accepting the form."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def validate_inputs(self):
        """Return an error message, or an empty string for valid input."""
        osm_folder = self.osm_path.filePath().strip()
        adm_file = self.adm_shp.filePath().strip()
        field_name = self.field_name.text().strip()
        field_value = self.field_value.text().strip()
        epsg_text = self.epsg_code.text().strip()
        output_folder = self.result_path.filePath().strip()

        if not all((osm_folder, adm_file, epsg_text, output_folder)):
            return "Заполните обязательные поля."
        if not os.path.isdir(osm_folder):
            return "Папка с исходными данными не существует."
        if not os.path.isfile(adm_file):
            return "Файл административных границ не найден."
        if (field_name and not field_value) or (field_value and not field_name):
            return "Для фильтра территории заполните и поле, и значение."
        try:
            epsg = int(epsg_text)
        except ValueError:
            return "EPSG-код должен быть целым числом."
        if not QgsCoordinateReferenceSystem(f"EPSG:{epsg}").isValid():
            return "Указан некорректный EPSG-код."
        if os.path.exists(output_folder) and not os.path.isdir(output_folder):
            return "Путь результата указывает на файл, а не на папку."
        return ""

    def accept(self):
        """Prevent closing the dialog until the entered values are valid."""
        error = self.validate_inputs()
        if error:
            QtWidgets.QMessageBox.warning(self, "Ошибка ввода", error)
            return
        super().accept()
