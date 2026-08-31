# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-28 10:20

@author: a002028

"""
import shapely
import fiona
import rasterio as rio
from rasterio import features
from rasterio.features import shapes, rasterize
import descartes
import numpy as np


def raster_reader(fid, include_meta=False):
    rst = rio.open(fid)
    array = rst.read()
    array = array[0].astype(int)
    if include_meta:
        meta = rst.meta.copy()
        meta.update(compress='lzw')
        return array, meta
    else:
        return array


if __name__ == "__main__":
    rst_path = 'C:/Utveckling/BAWS-vis/bawsvis/export/aggregation_2020.tiff'
    rst = rio.open(rst_path)
    array = rst.read()
    array = array[0]
    array = array.astype(int)
