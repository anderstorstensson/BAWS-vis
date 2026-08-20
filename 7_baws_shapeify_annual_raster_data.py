# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-01 08:45

@author: a002028
"""
import os
from bawsvis.utils import generate_filepaths
from bawsvis.session import Session
from bawsvis.data_handler import shapeify_annual


if __name__ == "__main__":
    from bawsvis.paths import data_dir
    from bawsvis.utils import discover_years

    # Create the Session object
    s = Session()

    # Set path to data path
    data_path = data_dir('aggregates')

    # If we want to save data to a specific location, we set the export path here.
    s.setting.set_export_directory(path=data_path)

    # Loop through the years present and shapeify each annual aggregate.
    for year in discover_years(data_path, pattern='aggregation_',
                               endswith='.tiff'):
        rst_path = os.path.join(data_path, f'aggregation_{year}.tiff')
        shapeify_annual(rst_path, export_path=s.setting.export_directory)

        # # Monthly aggregate
        # for month in range (6, 9):
        #     rst_path = os.path.join(data_path, fr'aggregation_{year}0{month}.tiff')
        #     shapeify_annual(rst_path, export_path=s.setting.export_directory)

# if __name__ == "__main__":
#     # Set path to data directory
#     data_path = r'C:\Temp\baws_reanalys\aggragated_archive'
#
#     # Create the Session object
#     s = Session(data_path=data_path)
#
#     # If we want to save data to a specific location, we set the export path here.
#     s.setting.set_export_directory(path=data_path)
#
#     for year in range(2002, 2021):
#         rst_path = os.path.join(data_path, fr'aggregation_{year}.tiff')
#         shapeify_annual(rst_path, export_path=s.setting.export_directory)
