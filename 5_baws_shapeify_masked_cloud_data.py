#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-11-04 20:35

@author: johannes
"""
import os
from bawsvis.utils import generate_filepaths
from bawsvis.selection import only_selected
from bawsvis.data_handler import shapeify_clouds
import geopandas as gp
import rasterio as rio
from rasterio.features import shapes, rasterize
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time


if __name__ == "__main__":
    from bawsvis.paths import data_dir, repo_file

    # test_mask2.tiff = landmask?
    rst = rio.open(repo_file('test_mask2.tiff'))
    mask = rst.read()
    mask = mask[0].astype(int)

    files = only_selected(generate_filepaths(data_dir('corrected_geoms'),
                                             pattern='cyano_daymap',
                                             endswith='.tiff'))
    export_directory = data_dir('clouds')

    for fid in files:
        print(fid)
        cyano_data = rio.open(fid)
        cyano_data = cyano_data.read()
        cyano_data = cyano_data[0].astype(int)
        cyano_data = np.where(
            np.logical_and(cyano_data == 1, mask != 1),
            0, cyano_data
        )
        cyano_data = np.where(
            np.logical_and(cyano_data != 1, mask == 0),
            0, cyano_data
        )
        name = os.path.basename(fid).replace('.tiff', '.shp').replace(
            'cyano_daymap', 'clouds'
        )
        shapeify_clouds(
            cyano_data,
            export_path=os.path.join(export_directory, name)
        )
    # for year in (2019, 2020):
    #     directory = fr'C:\Temp\baws_reanalys\{year}'
    #     files = generate_filepaths(directory, pattern='cyano_daymap', endswith='.tiff')
    #     export_directory = r'C:\Temp\baws_reanalys\clipped_archive\corrected_geoms'
    #
    #     for fid in files:
    #         # if 'cyano_daymap_2019' in fid:
    #         #     continue
    #         print(fid)
    #         cyano_data = rio.open(fid)
    #         cyano_data = cyano_data.read()
    #         cyano_data = cyano_data[0].astype(int)
    #         cyano_data = np.where(
    #             np.logical_and(cyano_data == 1, mask != 1),
    #             0, cyano_data
    #         )
    #         cyano_data = np.where(
    #             np.logical_and(cyano_data != 1, mask == 0),
    #             0, cyano_data
    #         )
    #         name = os.path.basename(fid).replace('.tiff', '.shp')
    #         shapeify_clouds(
    #             cyano_data,
    #             export_path=os.path.join(export_directory, name)
    #         )
