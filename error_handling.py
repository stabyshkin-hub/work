"""Error handling and logging for the QGIS plugin."""

import traceback

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import QMessageBox

LOG_TAG = "Clip Reproject"


def log_message(message, level=Qgis.Info):
    """Write a message to the QGIS log."""
    QgsMessageLog.logMessage(message, LOG_TAG, level=level)


def execute_with_feedback(parent, operation, params):
    """Execute processing with logging and user feedback."""
    log_message("Начало обработки данных.")

    try:
        result = operation(params)
    except (ValueError, FileNotFoundError) as error:
        log_message(str(error), Qgis.Warning)
        QMessageBox.warning(parent, "Ошибка данных", str(error))
        return None
    except Exception as error:
        log_message(traceback.format_exc(), Qgis.Critical)
        QMessageBox.critical(
            parent,
            "Ошибка обработки",
            f"Не удалось выполнить обработку: {error}",
        )
        return None

    log_message("Обработка завершена.")
    return result
