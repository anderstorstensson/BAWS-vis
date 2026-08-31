# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-07-01 08:58
@author: johannes
"""
import rasterio as rio
import numpy as np
from bawsvis.utils import generate_filepaths
from bawsvis.selection import only_selected


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
    from bawsvis.paths import data_dir, repo_file

    mask, meta = raster_reader(
        repo_file('raster_landmask_baws1000_sweref99tm.tiff'), include_meta=True)

    files = only_selected(generate_filepaths(
        data_dir('corrected_geoms'),
        pattern='cyano_daymap',
        endswith='.tiff',
    ))
    for fid in files:
        print(fid)
        cyano_day = raster_reader(fid)

        indexer = np.logical_and(
            np.logical_or(cyano_day == 2, cyano_day == 3),
            mask == 0
        )

        cyano_day = np.where(indexer, 0, cyano_day)

        with rio.open(fid, 'w', **meta) as dst:
            dst.write(cyano_day.astype(rio.uint8), 1)
        dst.close()
