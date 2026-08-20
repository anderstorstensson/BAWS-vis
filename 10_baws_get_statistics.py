"""
Created on 2021-09-02 15:58
@author: johannes
"""
from bawsvis.utils import generate_filepaths
from bawsvis.session import Session
from bawsvis.writers.dictionary import json_writer
from bawsvis.readers.dictionary import json_reader
from bawsvis.data_handler import get_area
import geopandas as gp
import os
from pathlib import Path


if __name__ == "__main__":
    from bawsvis.paths import data_dir

    # Set path to data directory (shapefiles regenerated from rasters, script 4)
    s = Session(data_path=data_dir('shapeified'))

    # Stats json files live in the stats directory.
    s.setting.set_export_directory(path=data_dir('stats'))

    from bawsvis.utils import discover_years

    for year in discover_years(s.data_path, pattern='cyano_daymap_',
                               endswith='.shp', selected=True):

        # Generate filepaths
        generator = generate_filepaths(s.data_path,
                                    pattern=f'cyano_daymap_{year}',
                                    endswith='.shp')

        stat_path = os.path.join(
            s.setting.export_directory, f'stats_{year}.json')
        if not os.path.exists(stat_path):
            print(f'Skipping {year}: {stat_path} not found (run script 9 first)')
            continue
        stat = json_reader(stat_path)

        # Loop through the file-generator extract statistics..
        for day_path in generator:
            print(day_path)
            # if 'cyano_daymap' in day_path:
            #     continue
            day_frame = gp.read_file(day_path)
            # week_path = Path(day_path).parent.joinpath(
            #     Path(day_path).name.replace('_daymap_', '_weekmap_')
            # )
            # week_frame = gp.read_file(week_path)
            date_tag = os.path.basename(day_path).split('.')[0].split('_')[-1]
            stat[date_tag]["daily_bloom_area"] = get_area(day_frame.loc[day_frame['class'].isin([2, 3]), :])
            stat[date_tag]["surface_area"] = get_area(day_frame.loc[day_frame['class'] == 3, :])
            stat[date_tag]["subsurface_area"] = get_area(day_frame.loc[day_frame['class'] == 2, :])
            # stat[date_tag]["weekly_bloom_area"] = get_area(week_frame)

            # stat[date_tag] = {
            #     "daily_bloom_area": get_area(day_frame.loc[day_frame['class'].isin([2, 3]), :]),
            #     "surface_area": get_area(day_frame.loc[day_frame['class'] == 3, :]),
            #     "subsurface_area": get_area(day_frame.loc[day_frame['class'] == 2, :]),
            #     "weekly_bloom_area": get_area(week_frame)
            # }

        out_file_path = os.path.join(s.setting.export_directory,
                                    f'stats_{year}_2.json')
        json_writer(out_file_path, stat)
