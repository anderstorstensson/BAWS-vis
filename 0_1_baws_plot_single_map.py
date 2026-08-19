# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-31 11:27

@author: a002028

"""
from bawsvis.session import Session
from bawsvis.readers.raster import raster_reader
from bawsvis.plotting import PlotMap, PlotWhiteMap
import os
import numpy as np


if __name__ == "__main__":

    from bawsvis.paths import data_dir

    s = Session()

    # Use the most recent all-years aggregation matrix from script 6.
    candidates = sorted(data_dir('aggregates').glob('aggregation_*.txt'))
    if not candidates:
        raise SystemExit('No aggregation_*.txt found; run script 6 first')
    file = candidates[-1]

    # data, meta = raster_reader(file, include_meta=True)
    data = np.loadtxt(file)

    # map_frame = {'lat_min': 52., 'lat_max': 66.,
    #              'lon_min': 7., 'lon_max': 37.5}
    map_frame = {'lat_min': 53.5, 'lat_max': 65.,
                    'lon_min': 9.2, 'lon_max': 35.}

    plot = PlotWhiteMap(data_mat=data.astype(float),
                        lat_mat=s.setting.latitude_array,
                        lon_mat=s.setting.longitude_array,
                        cbar_label='Antal dagar med blomning',
                        cmap_step=50,
                        max_tick=300,
                        # cmap_step=5,
                        # max_tick=30,
                        min_tick=0,
                        map_frame=map_frame,
                        resolution='f',
                        # text=str('year'),
                        )

    plot._draw_map()
    plot._draw_mesh(p_color=True)
    plot.hide_axis()
    plot._save_figure(os.path.join(data_dir('figures'), file.stem + '.png'))

        # break

    # data, meta = raster_reader(r'C:\Utveckling\TESTING\BAWS_interkalibrering\intercalibration.tiff',
    #                            include_meta=True)
    # map_frame = {'lat_min': 53.5, 'lat_max': 65.,
    #              'lon_min': 9.2, 'lon_max': 35.}
    #
    # plot = PlotWhiteMap(data_mat=data.astype(float),
    #                     lat_mat=s.setting.latitude_array,
    #                     lon_mat=s.setting.longitude_array,
    #                     cbar_label='Number of bloom markings',
    #                     cmap_step=1,
    #                     max_tick=6,
    #                     min_tick=0,
    #                     map_frame=map_frame,
    #                     resolution='i',
    #                     # text=str('BAWS - Intercalibration 2022'),
    #                     fig_title='BAWS - Intercalibration 2022'
    #                     )
    #
    # plot._draw_map()
    # plot.map.fillcontinents(color='white', lake_color='white', zorder=3)
    # plot._draw_mesh(p_color=True)
    # plot.hide_axis()
    # plot._save_figure(os.path.join(s.setting.export_directory, 'Intercalibration_2022.png'))
