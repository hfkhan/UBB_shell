__author__ = 'hassaankhan'

import os
import shapefile

global basepath
basepath = os.path.split(__file__)[0]

global shapefile_folder
shapefile_folder = 'data/shapefiles'


def get_shapefile(filename):
    shp = shapefile.Reader(os.path.join(basepath, shapefile_folder, filename))
    shp_obj = shp.shapeRecords()
    return shp_obj
