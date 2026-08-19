# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-06-17 15:44
@author: johannes
"""
from bawsvis.data_handler import get_shapes_from_raster, get_geodataframe
import pandas as pd
import numpy as np
import geopandas as gp
import rasterio as rio
import matplotlib.pyplot as plt
from bawsvis.utils import generate_filepaths
from bawsvis.session import Session


if __name__ == "__main__":
    from bawsvis.paths import data_dir

    # Set path to data directory
    s = Session(data_path=data_dir('aggregates'))

    stats = {
        'year': [],
        'total_area': [],
        'duration': [],
        'extent': [],
        'intensity': [],
    }
    
    year = 2023
    # for year in range(2002, 2023):

    # Generate filepaths
    generator = generate_filepaths(s.data_path, endswith=f'{year}.shp')

    for fid in generator:
        print(fid)
        gf = gp.read_file(fid)
        year = fid.split('_')[-1].replace('.shp', '')

        total_area = gf.area.sum() / 1000000.
        print(total_area)
        area_days = []
        for n in gf['class'].unique():
            boolean = gf['class'] == n
            area_days.append(gf.loc[boolean, :].area.sum() / 1000000. * n)

        # TODO Test properly if it produces wanted values
        if total_area > 0:
            T = sum(area_days) / float(total_area)
            A = sum(area_days) / float(sum(gf['class'].unique()))
        else:
            print("T = ", sum(area_days), "/", float(total_area), "A = ", sum(area_days), "/", float(sum(gf['class'].unique())))
            T = 0
            A = 0
        I = T * A

        stats['year'].append(year)
        stats['total_area'].append(int(round(total_area, 0)))
        stats['duration'].append(round(T, 1))
        stats['extent'].append(int(round(A, 0)))
        stats['intensity'].append(int(round(I, 0)))

    df_stats = pd.DataFrame(stats)
    df_stats.to_excel(
        data_dir('stats') / f'annual_stats_norm_{year}.xlsx',
        sheet_name='data',
        index=None,
    )

# if __name__ == "__main__":
#     file_path = 'C:/Utveckling/BAWS-vis/bawsvis/export/stats_all.json'
#     data = pandas_reader(file_path)
#     data = data.transpose()
#
#     data.index = [pd.Timestamp(str(c)) for c in data.index]
#
#     annual_stats = {
#         'year': [],
#         'start_bloom': [],
#         'end_bloom': [],
#         'max_day_area_bloom': [],
#         'total_area_bloom': [],  # from tot tiff
#         'start_surface_accumulation': [],
#         'max_day_area_surface_accumulation': [],
#         'total_area_surface_accumulation': [],  # from tot tiff
#     }
#
#     for year in data.index.year.unique():
#         boolean_year = data.index.year == year
#         annual_stats['year'].append(year)
#
#         boolean = boolean_year & (data['daily_bloom_area'] > 0)
#         annual_stats['start_bloom'].append(pd.Timestamp(data.index[boolean].values[0]).strftime('%Y-%m-%d'))
#         annual_stats['end_bloom'].append(pd.Timestamp(data.index[boolean].values[-1]).strftime('%Y-%m-%d'))
#         annual_stats['max_day_area_bloom'].append(data.loc[boolean, 'daily_bloom_area'].max())
#
#         boolean = boolean_year & (data['surface_area'] > 0)
#         annual_stats['start_surface_accumulation'].append(pd.Timestamp(data.index[boolean].values[0]).strftime('%Y-%m-%d'))
#         annual_stats['max_day_area_surface_accumulation'].append(data.loc[boolean, 'surface_area'].max())
#
#         rst = rio.open('C:/Utveckling/BAWS-vis/bawsvis/export/aggregation_only_surface_{}.tiff'.format(year))
#         array = rst.read()
#         array = np.where(array[0].astype(int) > 0, 1, 0)
#         shape_list = get_shapes_from_raster(array)
#         gf = get_geodataframe(shape_list)
#         annual_stats['total_area_surface_accumulation'].append(int(gf.area.sum() / 1000000.))
#
#         rst = rio.open('C:/Utveckling/BAWS-vis/bawsvis/export/aggregation_{}.tiff'.format(year))
#         array = rst.read()
#         array = np.where(array[0].astype(int) > 0, 1, 0)
#         shape_list = get_shapes_from_raster(array)
#         gf = get_geodataframe(shape_list)
#         annual_stats['total_area_bloom'].append(int(gf.area.sum() / 1000000.))
#
#     df_annual = pd.DataFrame(annual_stats)
#     df_annual.to_excel(
#         'annual_stats.xlsx',
#         sheet_name='data',
#         header=True,
#         index=None,
#     )
