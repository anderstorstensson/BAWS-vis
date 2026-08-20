#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-11-01 11:15

@author: johannes
"""
from bawsvis.utils import generate_filepaths
from bawsvis.selection import only_selected
from bawsvis.session import Session
from bawsvis.data_handler import correct_shapefile
from bawsvis.data_handler import ExteriorLog
from bawsvis.paths import data_dir


if __name__ == "__main__":
    # Set path to data directory
    s = Session(data_path=data_dir('daymaps'))

    # If we want to save data to a specific location, we set the export path here.
    s.setting.set_export_directory(path=data_dir('corrected_geoms'))

    # Init log. Purpose: save info about multipolygon exterior geometries.
    ExteriorLog()

    # Generate filepaths (restricted to BAWS_YEARS if set)
    generator = only_selected(
        generate_filepaths(s.data_path, pattern='cyano_daymap_', endswith='.shp'))

    for fid in generator:
        print(fid)
        correct_shapefile(fid, export_path=s.setting.export_directory)
