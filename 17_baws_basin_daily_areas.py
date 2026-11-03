#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Daily cloud, subsurface and surface area per sea basin (km2).

Zonal statistics of the daily 1 km class rasters (corrected_geoms) over
the HELCOM sub-basins (bawsvis/helcom_basins.py, downloaded to shape/ on
first use), restricted to the BAWS valid area
(raster_landmask_baws1000_sweref99tm.tiff). Writes, per season,

  stats/basin_daily_areas_<year>.csv
      date, basin_nr, valid_km2, cloud_km2, subsurface_km2, surface_km2

where basin_nr is the HELCOM sub-basin number (SEA-0nn), and caches the
basin label raster as stats/basin_labels_helcom_baws1000.tiff.
Respects BAWS_YEARS. Input to script 18 (bloom indicator).
"""
import os

import pandas as pd
import rasterio as rio

from bawsvis.basin_areas import rasterize_basins, daily_basin_areas
from bawsvis.basins import BASIN_NAMES
from bawsvis.helcom_basins import read_basins
from bawsvis.paths import data_dir, repo_file
from bawsvis.utils import discover_years, generate_filepaths

LABEL_RASTER = 'basin_labels_helcom_baws1000.tiff'


def basin_labels(mask_path, stats_dir):
    """Basin label raster on the mask grid, built once and cached."""
    cached = stats_dir / LABEL_RASTER
    with rio.open(mask_path) as src:
        meta, mask = src.meta.copy(), src.read(1)
    if cached.exists():
        with rio.open(cached) as src:
            return src.read(1), mask, meta
    basins = read_basins(data_dir('shape'), basin_numbers=BASIN_NAMES)
    labels = rasterize_basins(basins, meta['transform'], mask.shape)
    with rio.open(cached, 'w', **{**meta, 'compress': 'lzw'}) as dst:
        dst.write(labels, 1)
    print('wrote', cached)
    return labels, mask, meta


def date_of(path):
    return os.path.basename(path).split('_')[-1].split('.')[0]


def season_table(files, labels, mask, pixel_km2):
    frames = []
    for fid in sorted(files):
        with rio.open(fid) as src:
            day = src.read(1)
        frames.append(daily_basin_areas(day, labels, mask, pixel_km2,
                                        date_of(fid)))
    return pd.concat(frames, ignore_index=True)


def main():
    raster_dir = data_dir('corrected_geoms')
    stats_dir = data_dir('stats')
    labels, mask, meta = basin_labels(
        repo_file('raster_landmask_baws1000_sweref99tm.tiff'), stats_dir)
    pixel_km2 = abs(meta['transform'].a * meta['transform'].e) / 1e6

    years = discover_years(raster_dir, pattern='cyano_daymap_',
                           endswith='.tiff', selected=True)
    for year in years:
        files = list(generate_filepaths(raster_dir,
                                        pattern=f'cyano_daymap_{year}',
                                        endswith='.tiff'))
        table = season_table(files, labels, mask, pixel_km2)
        out = stats_dir / f'basin_daily_areas_{year}.csv'
        table.to_csv(out, index=False, date_format='%Y-%m-%d')
        print(f'{year}: {len(files)} days ->', out)


if __name__ == '__main__':
    main()
