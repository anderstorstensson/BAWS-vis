# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-28 10:15

@author: a002028

"""
import os
import time
import numpy as np
import pandas as pd
from bawsvis.config import Settings
from bawsvis.session import Session
from bawsvis.readers.raster import raster_reader
from bawsvis.readers.text import np_txt_reader
from bawsvis.readers.shape import shape_reader
from bawsvis.readers.dictionary import pandas_reader
from bawsvis.plotting.map import PlotMap
from bawsvis.writers.raster import raster_writer
from bawsvis.utils import generate_filepaths, Grid, transform_ref_system, round_value
from bawsvis.interpolate import get_interpolated_df

import shapely
import fiona
from fiona.crs import to_string
import rasterio as rio
from rasterio.features import shapes, rasterize
import geopandas as gp
import descartes
from pprint import pprint
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.ops import polygonize


# def area2transform_baws1000_sweref99tm():
#     crs = rio.crs.CRS.from_string('+init=epsg:3006')
#     west, south, east, north = (-49739.0, 5954123.0, 1350261.0, 7354123.0)
#     height, width = (1400, 1400)
#     transform = rio.transform.from_bounds(west, south,
#                                           east, north,
#                                           width, height)
#     return crs, transform, (height, width)

def area2transform_baws1000_sweref99tm():
    crs = rio.crs.CRS.from_string("epsg:3006")
    west, south, east, north = (-49739.0, 5954123.0, 1350261.0, 7354123.0)
    height, width = (1400, 1400)
    transform = rio.transform.from_bounds(west, south,
                                          east, north,
                                          width, height)
    return crs, transform, (height, width)

def date_range_composite(timestamp):
    dr = pd.date_range(timestamp - pd.Timedelta('6 days'), periods=7)
    return [ts.strftime("%Y%m%d") for ts in dr]


def get_area(geoframe):
    return round_value(
        geoframe['geometry'].area.sum() / 10 ** 6,
        nr_decimals=1,
        out_format=float
    )


def shapeify_clouds(array, export_path=None):
    """Doc."""
    shape_list = get_shapes_from_raster(array)
    schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}
    crs, transform, area_shape = area2transform_baws1000_sweref99tm()
    with fiona.open(export_path, 'w', driver='ESRI Shapefile',
                    crs=to_string(crs), schema=schema) as dst:
        dst.writerecords(shape_list)


def shapeify_annual(rst_path, export_path=None):
    rst = rio.open(rst_path)
    array = rst.read()
    array = array[0]
    array = array.astype(int)

    print('shapeify:', rst_path)
    shape_list = get_shapes_from_raster(array, exclude_values=[0])

    fname = rst_path.replace('.tiff', '.shp')

    if export_path:
        fname = os.path.join(export_path, os.path.basename(fname))

    schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}

    crs, transform, area_shape = area2transform_baws1000_sweref99tm()

    with fiona.open(fname, 'w', driver='ESRI Shapefile', crs=to_string(crs), schema=schema) as dst:
        dst.writerecords(shape_list)


def shapeify_weekly(rst_path, export_path=None):
    rst = rio.open(rst_path)
    array = rst.read()
    array = array[0]
    array = array.astype(int)

    print('shapeify:', rst_path)
    shape_list = get_shapes_from_raster(array, exclude_values=[0])

    fname = rst_path.replace('.tiff', '.shp')

    if export_path:
        fname = os.path.join(export_path, os.path.basename(fname))

    schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}

    crs, transform, area_shape = area2transform_baws1000_sweref99tm()

    with fiona.open(fname, 'w', driver='ESRI Shapefile', crs=to_string(crs), schema=schema) as dst:
        dst.writerecords(shape_list)


def shapeify(rst_path, export_path=None):
    rst = rio.open(rst_path)
    array = rst.read()
    array = array[0]
    array = array.astype(int)

    print('shapeify:', rst_path)
    shape_list = get_shapes_from_raster(array)

    fname = rst_path.replace('.tiff', '.shp')

    if export_path:
        fname = os.path.join(export_path, os.path.basename(fname))

    schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}

    crs, transform, area_shape = area2transform_baws1000_sweref99tm()

    with fiona.open(fname, 'w', driver='ESRI Shapefile', crs=to_string(crs), schema=schema) as dst:
        dst.writerecords(shape_list)


def get_shapes_from_raster(raster, exclude_values=None):
    exclude_values = exclude_values or [0, 4]
    shapes_with_properties = []

    # rasterio.features.shapes does not accept 64-bit integers; plain
    # .astype(int) gives int64 on Linux (but int32 on Windows).
    raster = np.asarray(raster).astype(np.int32)

    crs, transform, area_shape = area2transform_baws1000_sweref99tm()

    classes = {int(cls): {'class': int(cls)} for cls in np.unique(raster)}
    classes[0] = None

    mask = None

    for i, (s, v) in enumerate(shapes(raster, mask=mask, transform=transform)):
        if v in exclude_values:
            continue
        shapes_with_properties.append({
            'properties': classes[int(v)],
            'geometry': s
        })

    return shapes_with_properties


def rasterize_daily_shp(fid, meta=None):
    gf = gp.read_file(fid)
    gf = filter_shapes(gf)
    
    if gf.empty:
        print('EMPTY', os.path.basename(fid))
    else:
        save_path = fid.replace('.shp', '.tiff')
        with rio.open(save_path, 'w+', **meta) as out:
            out_arr = out.read(1)
            shapes = ((geom, value) for geom, value in list(zip(gf['geometry'], gf['class'])))
            burned = rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)


def rasterize_daily_iceshp(fid, meta=None, crs=None):
    gf = gp.read_file(fid)
    gf = gf.to_crs(*crs)
    gf['class'] = 0
    filter_boolean = gf['type'] >= 1
    gf.loc[filter_boolean, 'class'] = 1
    # gf.geometry = shapes.buffer(0)
    save_path = fid.replace('.shp', '.tiff')
    with rio.open(save_path, 'w+', **meta) as out:
        out_arr = out.read(1)
        shapes = ((geom, value) for geom, value in list(zip(gf['geometry'], gf['class'])))
        burned = rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
        out.write_band(1, burned)


def filter_shapes(gf):
    filter_boolean = gf['class'].isin([1, 2, 3, 4])
    filter_shapes = gf.loc[filter_boolean]
    filter_shapes['sort_order'] = ''

    # Value 1 (cloud) will be printed on top of all other.
    # Value 4 (No data) will only be printed if there are no other values to be printed.
    sorting_mapping = {1: 'D', 2: 'B', 3: 'C', 4: 'A'}
    for key, value in sorting_mapping.items():
        boolean = filter_shapes['class'] == key
        filter_shapes.loc[boolean, 'sort_order'] = value
    filter_shapes.sort_values(by='sort_order', ascending=True, inplace=True)

    return filter_shapes


def get_geodataframe(shape_list):
    print('get_geodataframe..')
    gf_dict = {'geometry': [], 'class': []}

    for s in shape_list:

        if type(s['geometry']['coordinates'][0]) == list:
            poly = Polygon(s['geometry']['coordinates'][0])
        else:
            poly = Polygon(s['geometry']['coordinates'])

        if not poly.is_empty:
            if poly.area:
                gf_dict['class'].append(s['properties']['class'])
                gf_dict['geometry'].append(poly)

    return gp.GeoDataFrame(gf_dict)


def create_7day_composite(folder_path, main_file):
    file_ts = pd.Timestamp(os.path.basename(main_file).split('.')[0].split('_')[-1])
    week_dates_generator = generate_filepaths(folder_path, pattern='cyano_daymap_',
                                              pattern_list=date_range_composite(file_ts),
                                              endswith='.tiff')
    zeros = np.array(())
    week_bloom = None
    raster_meta = None
    # pprint({os.path.basename(main_file): [
    #     os.path.basename(f) for f in week_dates_generator
    # ]})
    for fid in week_dates_generator:
        rst = rio.open(fid)
        array = rst.read()
        array = array[0]

        if not zeros.size:
            # First iteration of loop: We resets "zeros" to the shape of "array" and extract raster metadata
            # (used for creation of new tiff-file)
            zeros = np.zeros(array.shape)
            week_bloom = np.zeros(zeros.shape)
            raster_meta = rst.meta.copy()
            raster_meta.update(compress='lzw')

        day_bloom = np.where(np.logical_or(array == 2, array == 3), 1, zeros)
        week_bloom += day_bloom

    fid_rst_week = main_file.replace('_daymap_', '_weekmap_')
    with rio.open(fid_rst_week, 'w+', **raster_meta) as out:
        out.write(week_bloom.astype(np.uint8), 1)
    out.close()


def get_daily_stats(generator):
    stat_dict = {}
    million = 10 ** 6
    for shp_path in generator:
        file_name = os.path.basename(shp_path)
        date_str = ''.join(filter(str.isdigit, file_name))
        print('get_daily_stats', file_name)
        gf = gp.read_file(shp_path)
        boolean_bloom = gf['class'].isin([2, 3])

        if any(boolean_bloom):
            boolean_subsurface_bloom = gf['class'] == 2
            boolean_surface_bloom = gf['class'] == 3

            bloom_area = gf.loc[boolean_bloom, :].geometry.area.sum() / million
            subsurface_bloom_area = gf.loc[boolean_subsurface_bloom, :].geometry.area.sum() / million
            surface_bloom_area = gf.loc[boolean_surface_bloom, :].geometry.area.sum() / million

            bloom_area = round(bloom_area, 1)
            surface_bloom_area = round(surface_bloom_area, 1)
            subsurface_bloom_area = round(subsurface_bloom_area, 1)
        else:
            bloom_area = 0
            surface_bloom_area = 0
            subsurface_bloom_area = 0

        stat_dict[date_str] = {'daily_bloom_area': bloom_area,
                               'surface_area': surface_bloom_area,
                               'subsurface_area': subsurface_bloom_area}
    return stat_dict


def get_weekly_stats(generator):
    stat_dict = {}
    million = 10 ** 6
    for shp_path in generator:
        file_name = os.path.basename(shp_path)
        date_str = ''.join(filter(str.isdigit, file_name))
        print('get_weekly_stats', file_name)
        gf = gp.read_file(shp_path)
        boolean_bloom = gf['class'] > 0

        if any(boolean_bloom):
            bloom_area = gf.loc[boolean_bloom, :].geometry.area.sum() / million
            bloom_area = round(bloom_area, 1)
        else:
            bloom_area = 0

        stat_dict[date_str] = {'weekly_bloom_area': bloom_area}

    return stat_dict


def aggregation_annuals(file_generator, mask=None, reader='raster'):
    """Doc."""
    arrays = []
    for fid in file_generator:
        print(fid)
        if reader == 'raster':
            array = raster_reader(fid)
        else:
            array = np_txt_reader(fid)

        # Exclude areas marked with class value 2 or 3 outside of our "valid_baws_area".
        # Mask value 1 marks valid area; Masked value 0 marks not valid area
        if type(mask) == np.ndarray:
            print('Mask = True')
            array = np.where(mask == 0, 0, array)

        arrays.append(array)

    # Two loops? in case we want to lift out the part below..
    agg_array = arrays[0]
    if len(arrays) == 1:
        pass
    else:
        for scene in arrays[1:]:
            agg_array += scene

    return agg_array


def raster_aggregation(file_generator, mask=None, only_surface=False, reader='raster'):
    """

    :param reader:
    :param file_generator:
    :param mask:
    :param only_surface:
    :return:
    """
    # Keep a running sum instead of collecting every scene: a full
    # multi-decade run is thousands of scenes and holding them all
    # in memory (~16 MB each) exhausts RAM and gets the process
    # OOM-killed.
    agg_array = None
    zeros = np.array(())
    for fid in file_generator:
        print(fid)
        if reader == 'raster':
            array = raster_reader(fid)
        else:
            array = np_txt_reader(fid)

        if not zeros.shape[0]:
            zeros = np.zeros(array.shape)

        # Exclude areas marked with class value 2 or 3 outside of our "valid_baws_area".
        # Mask value 1 marks valid area; Maske value 0 marks not valid area
        if mask:
            array = np.where(mask == 0, 0, array)

        if only_surface:
            array = np.where(array == 3, 1, zeros)
        else:
            array = np.where(np.logical_or(array == 2, array == 3), 1, zeros)

        if agg_array is None:
            agg_array = array
        else:
            agg_array += array

    return agg_array


def raster_cloud_aggregation(file_generator, reader='raster'):
    """Doc."""
    agg_array = np.array(())
    for fid in file_generator:
        print(fid)
        if reader == 'raster':
            array = raster_reader(fid)
        else:
            array = np_txt_reader(fid)

        if not agg_array.shape[0]:
            agg_array = np.zeros(array.shape)

        array = np.where(array == 1, 1, 0)
        agg_array += array

    return agg_array


def raster_aggregation_ice(file_generator):
    agg_array = np.zeros((1400, 1400))
    for fid in file_generator:
        print(fid)
        array = raster_reader(fid)
        agg_array = agg_array + array
    return agg_array


def get_interpolated_data_table(data):
    """
    Hardcoded to fit BAWS statistics.
    :param data:
    :return:
    """
    df = pd.DataFrame({'timestamp': data.columns,
                       'daily_bloom_area': data.loc['daily_bloom_area', :],
                       'surface_area': data.loc['surface_area', :],
                       'subsurface_area': data.loc['subsurface_area', :],
                       'weekly_bloom_area': data.loc['weekly_bloom_area', :],
                       'cloud_area': data.loc['cloud_area', :],
                       })
    new_df = pd.DataFrame()
    for parameter in ['daily_bloom_area', 'surface_area', 'subsurface_area', 'weekly_bloom_area', 'cloud_area']:
        param_df = get_interpolated_df(df, 'timestamp', parameter)
        param_df = param_df.transpose()
        if new_df.empty:
            new_df = pd.DataFrame(columns=param_df.loc['x', :].values, index=[parameter])
            new_df.loc[parameter] = param_df.loc['y'].values
        else:
            new_df.loc[parameter] = param_df.loc['y'].values

    return new_df.astype(float)


def get_interpolated_statistics_table(data):
    """
    Hardcoded to fit BAWS statistics.
    :param data:
    :return:
    """
    df = pd.DataFrame({'timestamp': data.columns,
                       'daily_mean': data.loc['daily_mean', :],
                       'daily_std_u': data.loc['daily_std_u', :],
                       'daily_std_l': data.loc['daily_std_l', :],
                       'weekly_mean': data.loc['weekly_mean', :],
                       'weekly_std_u': data.loc['weekly_std_u', :],
                       'weekly_std_l': data.loc['weekly_std_l', :],
                       })
    new_df = pd.DataFrame()
    for parameter in ['daily_mean', 'daily_std_u', 'daily_std_l', 'weekly_mean', 'weekly_std_u', 'weekly_std_l']:
        param_df = get_interpolated_df(df, 'timestamp', parameter)
        param_df = param_df.transpose()
        if new_df.empty:
            new_df = pd.DataFrame(columns=param_df.loc['x', :].values, index=[parameter])
            new_df.loc[parameter] = param_df.loc['y'].values
        else:
            new_df.loc[parameter] = param_df.loc['y'].values

    return new_df.astype(float)


def get_statistics(file_path):
    """"""
    data = pandas_reader(file_path)
    data.rename(columns={c: pd.Timestamp(str(c)) for c in data.columns}, inplace=True)
    # df = get_interpolated_data_table(data)

    data = data.transpose()
    summer_dates = pd.date_range('20230601', '20230831')
    stats = {'summer_dates': summer_dates,
             'daily_mean': [], 'daily_std_u': [], 'daily_std_l': [],
             'weekly_mean': [], 'weekly_std_u': [], 'weekly_std_l': []}

    for date in summer_dates:
        boolean = (data.index.month == date.month) & (data.index.day == date.day)
        daily = data.loc[boolean, 'daily_bloom_area']
        weekly = data.loc[boolean, 'weekly_bloom_area']

        daily_mean = round(daily.mean(), 1)
        daily_std = round(daily.std(), 1)
        weekly_mean = round(weekly.mean(), 1)
        weekly_std = round(weekly.std(), 1)

        stats['daily_mean'].append(daily_mean)
        stats['daily_std_u'].append(round(daily_mean + daily_std, 1))
        daily_std_l = round(daily_mean - daily_std, 1)
        if daily_std_l < 0:
            daily_std_l = 0
        stats['daily_std_l'].append(daily_std_l)

        stats['weekly_mean'].append(weekly_mean)
        stats['weekly_std_u'].append(round(weekly_mean + weekly_std, 1))
        weekly_std_l = round(weekly_mean - weekly_std, 1)
        if weekly_std_l < 0:
            weekly_std_l = 0
        stats['weekly_std_l'].append(weekly_std_l)

    return stats


def get_valid_interiors(polygon_interiors):
    """Doc."""
    valid_interiors = []
    for ie in polygon_interiors:
        if ie.is_valid and ie.is_simple:
            valid_interiors.append(ie)
        else:
            print('Found invalid interior polygon. Cleaning...')
            clean = ie.buffer(0)

            if clean.is_valid and clean.is_simple:
                print('Cleaned!')
                valid_interiors.append(clean)
            else:
                print('Unable to clean.')
            
            # be = Polygon(ie).exterior
            # mls = be.intersection(be)
            # polygons = polygonize(mls)
            # valid_bowtie = MultiPolygon(polygons)
            # for poly_of_multi in list(valid_bowtie):
            #     line = poly_of_multi.exterior
            #     if line.is_valid and line.is_simple:
            #         valid_interiors.append(line)
            #     else:
            #         print(line)
    return valid_interiors


# def get_valid_exterior(poly):
#     """Doc."""
#     if type(poly) == MultiPolygon:
#         valid_geom = []
#         for p in list(poly):
#             if len(list(poly)) > 2:
#                 print(len(list(poly)))
#             if p.area > 1 and p.is_valid:
#                 valid_geom.append(p)
#         if len(valid_geom) > 1:
#             return MultiPolygon(valid_geom)
#         else:
#             return valid_geom[0]
#     else:
#         return poly


class ExteriorLog:
    log = {}
    name_numbers = {}

    def __init__(self, *args, areas=None, name=None, reset_log=None, **kwargs):
        if reset_log:
            self._reset_log()

        if name:
            if name in self.log:
                self.name_numbers[name] += 1
                self.log[name + f'-{self.name_numbers[name]}'] = areas
            else:
                self.log[name] = areas
                self.name_numbers[name] = 1

    @classmethod
    def _reset_log(cls):
        cls.log = {}
        cls.name_numbers = {}

    @classmethod
    def update_info(cls, *args, **kwargs):
        """Update information to log."""
        return cls(*args, **kwargs)


def get_valid_exterior(poly, name):
    """Doc."""
    if type(poly) == MultiPolygon:
        # valid_geom = []
        if len(list(poly)) > 2:
            ExteriorLog.update_info(areas=[p.area for p in list(poly)], name=name)
            # print(len(list(poly)), [p.area for p in list(poly)])
        for p in list(poly):

            if p.area > 1 and p.is_valid:
                return p
        # if len(valid_geom) > 1:
        #     return MultiPolygon(valid_geom)
        # else:
        #     return valid_geom[0]
    else:
        return poly


def correct_shapefile(fid, export_path=None):
    """Doc."""
    print(fid)
    gf = gp.read_file(fid)
    name = os.path.basename(fid)

    shapes = []
    for i, shape in enumerate(gf._to_geo()['features']):

        row_gf = gf.iloc[i: i + 1].explode(index_parts=False).reset_index(drop=True)

        if row_gf.shape[0] > 1:
            exp_gf = row_gf.buffer(0)
            invalid_exteriors = []
            for ii, geom in enumerate(exp_gf):
                indices = [j for j in range(exp_gf.shape[0]) if j != ii]
                invalid_exteriors.append(exp_gf[indices].contains(geom).any())

            interiors = get_valid_interiors(
                [p.exterior for p in row_gf.loc[invalid_exteriors, :].geometry]
            )
            polys = row_gf.loc[np.logical_not(invalid_exteriors), :].geometry
        else:
            polys = row_gf.geometry
            interiors = []

        for poly in polys:
            if not poly.is_valid:
                print('Found invalid polygon. Cleaning...')
                clean = poly.buffer(0)
                
                if clean.is_valid == True:
                    print('Cleaned!')
                    new_shape = shape.copy()
                    new_shape['geometry'] = mapping(clean)
                    shapes.append(new_shape)
                else:
                    print('Unable to clean.')
                # ie = get_valid_interiors(poly.interiors)
                # be = poly.exterior
                # mls = be.intersection(be)
                # polygons = polygonize(mls)
                # valid_bowtie = MultiPolygon(polygons)
                # for poly_of_multi in list(valid_bowtie):
                #     if poly_of_multi.is_valid:
                #         poly_interiors = get_valid_interiors(poly_of_multi.interiors)
                #         interiors.extend(poly_interiors)
                #         for line_ring in ie:
                #             if poly_of_multi.contains(line_ring):
                #                 interiors.append(line_ring)

                # exterior = get_valid_exterior(poly.buffer(0), name)

                # new_poly = Polygon(
                #     exterior.exterior,
                #     interiors
                # )
            else:
                if row_gf.shape[0] == 1:
                    shapes.append(shape)
                else:
                    new_shape = shape.copy()
                    new_shape['geometry'] = mapping(poly)
                    shapes.append(new_shape)

    crs = rio.crs.CRS.from_string("epsg:3006")
    schema = {'properties': [('class', 'int')], 'geometry': 'Polygon'}

    # Keep only the 'class' attribute; source files (e.g. from the SMHI
    # open-data WFS) may carry extra fields not in the schema above.
    shapes = [
        {'geometry': s['geometry'],
         'properties': {'class': int(s['properties']['class'])}}
        for s in shapes
    ]

    out_path = os.path.join(export_path, os.path.basename(fid))
    with fiona.open(out_path, 'w',
                    driver='ESRI Shapefile', crs=to_string(crs),
                    schema=schema) as dst:
        dst.writerecords(shapes)


if __name__ == "__main__":
    # settings = Settings()

    data_path = '...\\Manuell_algtolkning'

    s = Session(data_path=data_path)

    generator = generate_filepaths(s.data_path,
                                   pattern='cyano_daymap_',
                                   endswith='.shp',
                                   only_from_dir=True)

    # df = get_statistics_from_shapefiles(generator)


    # print('get_shapes_from_raster')
    # shape_list = get_shapes_from_raster(data)
    # gdf = get_geodataframe(shape_list)
    #
    # patches = get_matplotlib_patches(gdf, map_obj=plot.map)
    # plot.plot_patches(patches)
