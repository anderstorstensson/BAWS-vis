# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-28 11:00

@author: a002028

"""
import numpy as np
import rasterio as rio


def raster_writer(name, array, raster_meta):
    # Multi-season aggregations exceed uint8 (e.g. 342 bloom days over
    # 2002-2026); widen the dtype instead of silently wrapping values.
    array = np.asarray(array)
    dtype = np.uint8 if array.max() <= np.iinfo(np.uint8).max else np.uint16
    meta = {**raster_meta, 'dtype': np.dtype(dtype).name}
    with rio.open(name, 'w+', **meta) as out:
        out.write(array.astype(dtype), 1)