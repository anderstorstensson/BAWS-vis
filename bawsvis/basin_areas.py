# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Per-basin daily areas from the 1 km daily cyano rasters.

The daily tiffs (corrected_geoms/cyano_daymap_<date>.tiff) hold one class
per pixel: 0 nothing, 1 cloud, 2 subsurface bloom, 3 surface accumulation.
Combined with a basin label raster on the same grid and the BAWS valid-area
mask, a zonal count gives cloud, subsurface and surface area per basin.
"""
import numpy as np
import pandas as pd
from rasterio import features

CLASS_CLOUD = 1
CLASS_SUBSURFACE = 2
CLASS_SURFACE = 3

AREA_COLUMNS = ('valid_km2', 'cloud_km2', 'subsurface_km2', 'surface_km2')


def rasterize_basins(basins, transform, shape):
    """Label raster: pixel value = BASIN_NR, 0 outside the basins.

    basins: GeoDataFrame with BASIN_NR and geometry in the raster CRS.
    """
    shapes = ((geom, int(nr)) for geom, nr in
              zip(basins.geometry, basins['BASIN_NR']))
    return features.rasterize(shapes, out_shape=shape, transform=transform,
                              fill=0, dtype='uint8')


def _zonal_count(selector, labels, basin_numbers):
    counts = np.bincount(labels[selector], minlength=256)
    return counts[basin_numbers]


def daily_basin_areas(day, labels, mask, pixel_km2, date):
    """Areas (km2) per basin for one day's class raster.

    Returns a DataFrame with one row per basin present in `labels`:
    date, basin_nr, valid_km2, cloud_km2, subsurface_km2, surface_km2.
    Only pixels inside the valid mask count, so clouds over land are
    ignored. The input arrays are not modified.
    """
    valid = (mask == 1) & (labels > 0)
    basin_numbers = np.unique(labels[labels > 0])
    columns = {
        'valid_km2': _zonal_count(valid, labels, basin_numbers),
        'cloud_km2': _zonal_count(valid & (day == CLASS_CLOUD),
                                  labels, basin_numbers),
        'subsurface_km2': _zonal_count(valid & (day == CLASS_SUBSURFACE),
                                       labels, basin_numbers),
        'surface_km2': _zonal_count(valid & (day == CLASS_SURFACE),
                                    labels, basin_numbers),
    }
    return pd.DataFrame({
        'date': pd.Timestamp(date),
        'basin_nr': basin_numbers.astype(int),
        **{k: v.astype(float) * pixel_km2 for k, v in columns.items()},
    })
