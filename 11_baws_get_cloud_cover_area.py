#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-11-05 09:22

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

    # Set path to data directory
    s = Session(data_path=data_dir('clouds'))

    # Stats json files live in the stats directory.
    s.setting.set_export_directory(path=data_dir('stats'))

    from bawsvis.utils import discover_years

    for year in discover_years(s.data_path, pattern='clouds_',
                               endswith='.shp'):
        # Generate filepaths
        generator = generate_filepaths(s.data_path,
                                    pattern=f'clouds_{year}',
                                    endswith='.shp')

        stat_path = os.path.join(
            s.setting.export_directory, f'stats_{year}_2.json')
        if not os.path.exists(stat_path):
            print(f'Skipping {year}: {stat_path} not found (run script 10 first)')
            continue
        stat = json_reader(stat_path)

        # Loop through the file-generator extract statistics..
        for day_path in generator:
            print(day_path)
            day_frame = gp.read_file(day_path)
            date_tag = os.path.basename(day_path).split('.')[0].split('_')[-1]
            stat[date_tag]["cloud_area"] = get_area(
                day_frame.loc[day_frame['class'] == 1, :])

        out_file_path = os.path.join(
            s.setting.export_directory, f'stats_{year}_2.json')
        json_writer(out_file_path, stat)
