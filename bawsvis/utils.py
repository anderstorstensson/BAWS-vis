# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-28 10:50

@author: a002028

"""
import os
import re
import numpy as np
import rasterio as rio
from collections.abc import Mapping
from pyproj import Proj, CRS, transform
from decimal import Decimal, ROUND_HALF_UP


def round_value(value, nr_decimals=0, out_format=str):
    return out_format(Decimal(str(value)).quantize(Decimal('%%1.%sf' % nr_decimals % 1), rounding=ROUND_HALF_UP))


def transform_ref_system(lat=0.0, lon=0.0,
                         in_proj='EPSG:3006',  # SWEREF 99TM 1200
                         out_proj='EPSG:4326'):
    """
    Transform coordinates from one spatial reference system to another.
    in_proj is your current reference system
    out_proj is the reference system you want to transform to, default is EPSG:4326 = WGS84
    (Another good is EPSG:4258 = ETRS89 (Europe), almost the same as WGS84 (in Europe)
    and not always clear if coordinates are in WGS84 or ETRS89, but differs <1m.
    lat = latitude
    lon = longitude

    To find your EPSG check this website: http://spatialreference.org/ref/epsg/
    """
    o_proj = CRS(out_proj)
    i_proj = CRS(in_proj)

    x, y = transform(i_proj, o_proj, float(lon), float(lat))

    return y, x


class Grid:
    """
    """
    def __init__(self, meta):
        self.meta = meta
        self.proj = Proj(**self.meta['crs'])

        self.map_width = int(self.meta['width'] * self.meta['transform'][0])
        self.map_height = int(self.meta['height'] * self.meta['transform'][0])

        self.x_size = int(self.map_width / self.meta['width'])
        self.y_size = int(self.map_height / self.meta['height'])

        self.xmin_proj = self.meta['transform'][2]
        self.xmax_proj = self.xmin_proj + self.map_width
        self.ymax_proj = self.meta['transform'][5]
        self.ymin_proj = self.ymax_proj - self.map_height

        self.xmin_wgs84, self.ymin_wgs84 = self.llcord
        self.xmax_wgs84, self.ymax_wgs84 = self.urcord

        self.map_wgs84_width = self.xmax_wgs84 - self.xmin_wgs84
        self.map_wgs84_height = self.ymax_wgs84 - self.ymin_wgs84

        self.x_wgs84_size = self.map_wgs84_width / self.meta['width']
        self.y_wgs84_size = self.map_wgs84_height / self.meta['height']

    def get_longitude_grid(self):
        """
        :return:
        """
        array1d = np.arange(self.xmin_proj, self.xmax_proj, self.x_size)
        return np.tile(array1d, (self.map_height, 1))

    def get_latitude_grid(self):
        """
        :return:
        """
        array1d = np.arange(self.ymin_proj, self.ymax_proj, self.y_size)
        return np.flip(np.tile(array1d, (self.map_width, 1))).T

    def get_longitude_wgs84grid(self):
        """
        :return:
        """
        array1d = np.arange(self.xmin_wgs84, self.xmax_wgs84, self.x_wgs84_size)
        return np.tile(array1d, (self.meta['height'], 1))

    def get_latitude_wgs84grid(self):
        """
        :return:
        """
        array1d = np.arange(self.ymin_wgs84, self.ymax_wgs84, self.y_wgs84_size)
        return np.flip(np.tile(array1d, (self.meta['width'], 1))).T

    @property
    def llcord(self):
        return self.proj(*(self.xmin_proj, self.ymin_proj), inverse=True)

    @property
    def urcord(self):
        return self.proj(*(self.xmax_proj, self.ymax_proj), inverse=True)


def generate_filepaths(directory, pattern='', not_pattern='DUMMY_PATTERN',
                       pattern_list=[], endswith='',
                       only_from_dir=True):
    """
    :param directory:
    :param pattern:
    :param not_pattern:
    :param pattern_list:
    :param endswith:
    :param only_from_dir:
    :return:
    """
    # Accept both str and pathlib.Path; os.walk yields str roots, so the
    # path != directory comparison below needs a str directory.
    directory = os.fspath(directory)
    for path, subdir, fids in os.walk(directory):
        if only_from_dir:
            if path != directory:
                continue
        # Generator function (uses yield) https://docs.python.org/3/glossary.html#term-generator
        for f in fids:
            if pattern in f and not_pattern not in f and f.endswith(endswith):
                if any(pattern_list):
                    for pat in pattern_list:
                        if pat in f:
                            yield os.path.abspath(os.path.join(path, f))
                else:
                    yield os.path.abspath(os.path.join(path, f))


def discover_years(directory, pattern='', endswith='', selected=False):
    """Return a sorted list of years found in matching file names.

    Scans `directory` for files matching `pattern`/`endswith` (same
    semantics as generate_filepaths) and extracts the first four-digit
    year (20xx) from each file name. Lets pipeline scripts loop over the
    years actually present in the data instead of hardcoded ranges.

    With selected=True the list is further restricted to the seasons
    requested through BAWS_YEARS (see bawsvis.selection). Per-season
    stages pass this; cross-season stages (climatologies) must not.
    """
    years = set()
    for fid in generate_filepaths(directory, pattern=pattern,
                                  endswith=endswith):
        match = re.search(r'(20\d{2})', os.path.basename(fid))
        if match:
            years.add(int(match.group(1)))
    if selected:
        from bawsvis.selection import restrict_years
        return restrict_years(years)
    return sorted(years)


def recursive_dict_update(d, u):
    """ Recursive dictionary update using
    Copied from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        via satpy
    """
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = recursive_dict_update(d.get(k, {}), v)
            d.setdefault(k, r)
        else:
            d.setdefault(k, u[k])
    return d


# if __name__ == "__main__":
#
#     meta = get_raster_meta('C:/Utveckling/BAWS-vis/bawsvis/etc/raster_template.tiff')
#     g = Grid(meta)
