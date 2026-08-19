# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-31 13:07

@author: a002028

"""
from bawsvis.utils import generate_filepaths, recursive_dict_update
from bawsvis.session import Session
from bawsvis.data_handler import get_daily_stats, get_weekly_stats


if __name__ == "__main__":
    from bawsvis.paths import data_dir

    # Set path to data directory (shapefiles regenerated from rasters, script 4)
    s = Session(data_path=data_dir('shapeified'))

    # If we want to save data to a specific location, we set the export path here.
    s.setting.set_export_directory(path=data_dir('stats'))

    from bawsvis.utils import discover_years

    for year in discover_years(s.data_path, pattern='cyano_daymap_',
                               endswith='.shp'):

        # Generate filepaths (daily)
        generator = generate_filepaths(s.data_path,
                                    pattern=f'cyano_daymap_{year}',
                                    endswith='.shp')

        # Loop through the file-generator and aggregate the data.
        stats_daily = get_daily_stats(generator)

        # Generate filepaths (weekly)
        generator = generate_filepaths(s.data_path, 
                                    pattern=f'cyano_weekmap_{year}', 
                                    endswith='.shp')

        # Loop through the file-generator and aggregate the data.
        stats_weekly = get_weekly_stats(generator)

        stats = recursive_dict_update(stats_daily, stats_weekly)

        # # Export the table in json file.
        s.export_data(data=stats,
                    file_name=f'stats_{year}.json',
                    writer='json')
