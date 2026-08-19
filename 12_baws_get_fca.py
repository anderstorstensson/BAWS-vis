#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-11-17 10:43

@author: johannes
"""
from bawsvis.utils import generate_filepaths
from bawsvis.session import Session
from bawsvis.writers.dictionary import json_writer
from bawsvis.readers.dictionary import json_reader
from bawsvis.data_handler import get_area
import geopandas as gp
import os


if __name__ == "__main__":
    from bawsvis.paths import data_dir

    # Set path to data directory (shapefiles regenerated from rasters, script 4)
    data_path = data_dir('shapeified')
    s = Session(data_path=data_path)

    # Stats json files live in the stats directory.
    s.setting.set_export_directory(path=data_dir('stats'))

    from bawsvis.utils import discover_years

    for year in discover_years(data_path, pattern='cyano_daymap_',
                               endswith='.shp'):
        files = generate_filepaths(data_path, pattern=f'cyano_daymap_{year}',
                                endswith='.shp')
        stat_path = os.path.join(
            s.setting.export_directory, f'stats_{year}_2.json')
        if not os.path.exists(stat_path):
            print(f'Skipping {year}: {stat_path} not found (run scripts 10-11 first)')
            continue
        stat = json_reader(stat_path)

        for fid in files:
            print(fid)
            gf = gp.read_file(fid)
            date = fid.split('_')[-1].replace('.shp', '')

            # If the cloud polygons are clipped to the valid cyano area.
            # boolean_cloud = gf['class'] == 1
            # if boolean_cloud.any():
            #     valid_area = 359429. - (gf[boolean_cloud].area.sum() / 1000000.)
            # else:
            #     valid_area = 359429.

            valid_area = 359429. - stat[date]['cloud_area']

            boolean_bloom = gf['class'].isin((2, 3))
            if boolean_bloom.any():
                fca = (gf[boolean_bloom].area.sum() / 1000000.) / valid_area
            else:
                fca = 0.

            stat[date]['fca'] = fca

        out_file_path = os.path.join(
            s.setting.export_directory, f'stats_{year}_2.json')
        json_writer(out_file_path, stat)
