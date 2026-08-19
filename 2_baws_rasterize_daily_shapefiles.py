"""
Created on 2021-09-02 13:59
@author: johannes
"""
from bawsvis.utils import generate_filepaths
from bawsvis.session import Session
from bawsvis.data_handler import rasterize_daily_shp
from bawsvis.paths import data_dir


if __name__ == "__main__":
    # Set path to data directory.
    # NOTE: rasterize_daily_shp writes each tiff next to its input shapefile,
    # so the daily rasters end up in corrected_geoms/ as well.
    s = Session(data_path=data_dir('corrected_geoms'))

    # Generate filepaths
    generator = generate_filepaths(s.data_path, pattern='cyano_daymap_20',
                                   endswith='.shp')
    
    for f in generator:
        rasterize_daily_shp(f, meta=s.setting.raster_template_meta)
        print(f)
        # if not any((d in f for d in ('cyano_daymap_20080702',
        #                              'cyano_daymap_20040705',
        #                              'cyano_daymap_20040702',
        #                              'cyano_daymap_20040630',
        #                              'cyano_daymap_20040629',
        #                              'cyano_daymap_20040626',
        #                              'cyano_daymap_20030705',
        #                              'cyano_daymap_20030615'))):
        #     continue
        # print(f)
        # # if 'cyano_daymap_200' in f:
        # #     continue
        # rasterize_daily_shp(f, meta=s.setting.raster_template_meta)
        # # break