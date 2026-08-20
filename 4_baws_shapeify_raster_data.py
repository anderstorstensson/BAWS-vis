# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-01 08:45

@author: a002028

"""
from bawsvis.utils import generate_filepaths
from bawsvis.selection import only_selected
from bawsvis.session import Session
from bawsvis.data_handler import shapeify, shapeify_weekly
from bawsvis.paths import data_dir


if __name__ == "__main__":
    # Set path to data directory
    s = Session(data_path=data_dir('corrected_geoms'))

    # If we want to save data to a specific location, we set the export path here.
    s.setting.set_export_directory(path=data_dir('shapeified'))

    # Generate filepaths (restricted to BAWS_YEARS if set)
    generator = only_selected(generate_filepaths(
        s.data_path,
        pattern='cyano',
        endswith='.tiff'
    ))

    # Loop through the file-generator and shapeify raster data.
    for rst_path in generator:
        print(rst_path)
        shapeify(rst_path, export_path=s.setting.export_directory)
        # shapeify_weekly(rst_path, export_path=s.setting.export_directory)
