"""
Created on 2021-09-02 13:59
@author: johannes
"""
from bawsvis.utils import generate_filepaths
from bawsvis.selection import only_selected
from bawsvis.session import Session
from bawsvis.data_handler import rasterize_daily_shp
from bawsvis.paths import data_dir


if __name__ == "__main__":
    # Set path to data directory.
    # NOTE: rasterize_daily_shp writes each tiff next to its input shapefile,
    # so the daily rasters end up in corrected_geoms/ as well.
    s = Session(data_path=data_dir('corrected_geoms'))

    # Generate filepaths (restricted to BAWS_YEARS if set)
    generator = only_selected(
        generate_filepaths(s.data_path, pattern='cyano_daymap_20',
                           endswith='.shp'))

    for f in generator:
        rasterize_daily_shp(f, meta=s.setting.raster_template_meta)
        print(f)