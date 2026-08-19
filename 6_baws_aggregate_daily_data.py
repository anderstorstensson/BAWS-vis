# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-31 09:48

@author: a002028
"""
from bawsvis.utils import generate_filepaths, discover_years
from bawsvis.session import Session
from bawsvis.data_handler import raster_aggregation


# if __name__ == "__main__":
#     # Set path to data directory
#     data_path = r'C:\Temp\baws_tempo\data_2021\corrected_geometries'
#
#     # Create the Session object
#     s = Session(data_path=data_path)
#
#     # If we want to save data to a specific location, we set the export path here.
#     # s.setting.set_export_directory(path=None)
#
#     # Generate filepaths
#     generator = generate_filepaths(s.data_path, pattern='cyano_daymap_', endswith='.tiff')
#
#     # Loop through the file-generator and aggregate the data.
#     # aggregation is a numpy 2d-array
#     aggregation = raster_aggregation(generator)
#
#     # Export the aggragation in a tiff file.
#     # WARNING! tiff files only handles integer data with values <=100.
#     # The benefit of tiff-files are the super compressed format
#     s.export_data(data=aggregation, file_name='aggregation_2021.tiff')

if __name__ == "__main__":
    from bawsvis.paths import data_dir

    # Set path to data directory
    s = Session(data_path=data_dir('corrected_geoms'))

    # If we want to save data to a specific location,
    # we set the export path here.
    s.setting.set_export_directory(path=data_dir('aggregates'))

    years = discover_years(s.data_path, pattern='cyano_daymap',
                           endswith='.tiff')
    if not years:
        raise SystemExit(f'No cyano_daymap tiffs found in {s.data_path}')

    # Annual aggregates (one tiff per year, used by scripts 7-8).
    # WARNING! tiff files only handles integer data with values <=100.
    # The benefit of tiff-files are the super compressed format
    for year in years:
        print(f"{year}")
        generator = generate_filepaths(s.data_path,
                                       pattern=f'cyano_daymap_{year}',
                                       endswith='.tiff')
        aggregation = raster_aggregation(generator, only_surface=False)
        s.export_data(
            data=aggregation,
            file_name=f'aggregation_{year}.tiff'
        )

    # All-years aggregate (text matrix, used by plot script 0_1).
    generator = generate_filepaths(s.data_path, pattern='cyano_daymap',
                                   endswith='.tiff')
    aggregation = raster_aggregation(generator, only_surface=False)
    s.export_data(
        data=aggregation,
        file_name=f'aggregation_{years[0]}-{years[-1]}.txt',
        writer='text'
    )

        # # Monthly aggregate
        # for month in range(6, 9):
        #     print(f"{year}0{month}")
        #     generator = generate_filepaths(s.data_path, pattern=f'cyano_daymap_{year}0{month}',
        #                             endswith='.tiff')

        #     # Loop through the file-generator and aggregate the data.
        #     # aggregation is a numpy 2d-array
        #     aggregation = raster_aggregation(generator, only_surface=False)

        #     # Export the aggragation in a tiff file.
        #     # WARNING! tiff files only handles integer data with values <=100.
        #     # The benefit of tiff-files are the super compressed format
        #     s.export_data(
        #         data=aggregation,
        #         file_name=f'aggregation_{year}0{month}.tiff'
        #     )