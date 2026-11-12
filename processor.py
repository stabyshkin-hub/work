"""Geoprocessing operations for the Clip Reproject QGIS plugin."""

import os

import processing
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer


class Processor:
    """Process shapefiles independently of the plugin dialog."""

    @staticmethod
    def process(params):
        """Clip all SHP layers by a boundary and reproject them. Return output count."""
        osm_folder = params["osm_folder"]
        adm_file = params["adm_file"]
        field_name = params["field_name"]
        field_value = params["field_value"]
        epsg_text = params["epsg_text"]
        output_folder = params["output_folder"]

        if not all((osm_folder, adm_file, epsg_text, output_folder)):
            raise ValueError("Заполните все обязательные поля.")
        if not os.path.isdir(osm_folder):
            raise ValueError("Папка входных данных не найдена.")
        if not os.path.isfile(adm_file):
            raise ValueError("Файл административных границ не найден.")

        try:
            epsg = int(epsg_text)
        except ValueError as error:
            raise ValueError("EPSG-код должен быть целым числом.") from error

        target_crs = QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
        if not target_crs.isValid():
            raise ValueError("Указан некорректный EPSG-код.")

        adm_layer = QgsVectorLayer(adm_file, "administrative_boundary", "ogr")
        if not adm_layer.isValid():
            raise ValueError("Не удалось открыть файл административных границ.")

        if field_name and field_value:
            if field_name not in [field.name() for field in adm_layer.fields()]:
                raise ValueError(f"В слое границ нет поля '{field_name}'.")
            escaped_field = field_name.replace('"', '""')
            escaped_value = field_value.replace("'", "''")
            adm_layer.selectByExpression(f"\"{escaped_field}\" = '{escaped_value}'")
            if adm_layer.selectedFeatureCount() == 0:
                raise ValueError("По заданному значению территория не найдена.")
        else:
            adm_layer.selectAll()

        selected = processing.run(
            "native:saveselectedfeatures",
            {"INPUT": adm_layer, "OUTPUT": "TEMPORARY_OUTPUT"},
        )["OUTPUT"]

        os.makedirs(output_folder, exist_ok=True)
        processed_count = 0

        for file_name in os.listdir(osm_folder):
            if not file_name.lower().endswith(".shp"):
                continue

            input_path = os.path.join(osm_folder, file_name)
            layer = QgsVectorLayer(input_path, file_name, "ogr")
            if not layer.isValid():
                continue

            base_name = os.path.splitext(file_name)[0]
            final_path = os.path.join(output_folder, f"{base_name}_gsk2011.gpkg")
            Processor._remove_project_layers(final_path)

            clipped = processing.run(
                "native:clip",
                {"INPUT": layer, "OVERLAY": selected, "OUTPUT": "TEMPORARY_OUTPUT"},
            )["OUTPUT"]
            processing.run(
                "native:reprojectlayer",
                {"INPUT": clipped, "TARGET_CRS": target_crs, "OUTPUT": final_path},
            )

            result_layer = QgsVectorLayer(final_path, f"{base_name}_gsk2011", "ogr")
            if result_layer.isValid():
                QgsProject.instance().addMapLayer(result_layer)
            processed_count += 1

        return processed_count

    @staticmethod
    def _remove_project_layers(path):
        """Remove project layers that read from ``path`` so the file can be overwritten.

        A layer from a previous run keeps the GeoPackage open, which blocks
        overwriting it (on Windows) and would add a duplicate layer to the project.
        """
        target = os.path.normcase(os.path.abspath(path))
        project = QgsProject.instance()
        layer_ids = [
            layer_id
            for layer_id, layer in project.mapLayers().items()
            if os.path.normcase(os.path.abspath(layer.source().split("|")[0])) == target
        ]
        if layer_ids:
            project.removeMapLayers(layer_ids)
