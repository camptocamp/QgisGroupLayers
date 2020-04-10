from qgis.core import QgsMapLayerType
from qgis.core import QgsWkbTypes
from qgis.core import QgsRasterLayer

# group by providerType

groupHierarchy = {
    "groupCriteria": "type",
    "values": {
        "vector": {
            "value": QgsMapLayerType.VectorLayer,
            "groupCriteria": "geometryType",
            "values": {
                "point": {
                    "value": QgsWkbTypes.PointGeometry
                },
                "line": {
                    "value": QgsWkbTypes.LineGeometry
                },
                "polygon": {
                    "value": QgsWkbTypes.PolygonGeometry
                },
            }
        },
        "raster": {
            "value": QgsMapLayerType.RasterLayer,
            "groupCriteria": "rasterType",
            "values": {
                "gray": {
                     "value": QgsRasterLayer.GrayOrUndefined
                },
                "palette": {
                     "value": QgsRasterLayer.Palette
                },
                "multiband": {
                     "value": QgsRasterLayer.Multiband
                },
                "color": {
                     "value": QgsRasterLayer.ColorLayer
                },
            }
        },
        "plugin": {
            "value": QgsMapLayerType.PluginLayer,
        },
        "mesh": {
            "value": QgsMapLayerType.MeshLayer,
        },
        # vector tile unavailable below 3.14
        # "vector tile": {
        #     "value": QgsMapLayerType.VectorTileLayer,
        # },
    }
}
