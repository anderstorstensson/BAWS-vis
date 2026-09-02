# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""HELCOM sub-basins of the Baltic Sea: download and read.

The 17 level-2 assessment units of the HELCOM Monitoring and Assessment
Strategy (2013), as published by ICES:

    https://gis.ices.dk/geonetwork/srv/api/records/225df9db-bfdf-4388-8ccb-fa4b99053a36

The record has no direct file download; the layer is served from the ICES
ArcGIS REST service, which can return all 17 polygons as GeoJSON in one
request, reprojected to SWEREF99 TM (EPSG:3006) and rounded to whole
metres. The result is stored once as shape/HELCOM_subbasins.shp with

    HELCOM_ID   'SEA-001' .. 'SEA-017'
    BASIN_NR    the number in HELCOM_ID (1 .. 17), the integer key used
                by the pipeline (label raster, csv, workbooks)
    NAME        HELCOM English name (level_2)
    AREA_KM2    HELCOM's own area (area_new_k)

Data can be used freely given that the source (HELCOM) is cited.
"""
import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gp
from shapely.ops import unary_union

RECORD_URL = ('https://gis.ices.dk/geonetwork/srv/api/records/'
              '225df9db-bfdf-4388-8ccb-fa4b99053a36')
QUERY_URL = ('https://gis.ices.dk/gis/rest/services/External_reference_layers/'
             'HELCOM_subbasins/MapServer/0/query')
SHAPEFILE = 'HELCOM_subbasins.shp'
EPSG = 3006
EXPECTED_BASINS = 17
USER_AGENT = 'BAWS-vis helcom_basins'

FIELDS = {'HELCOM_ID': 'HELCOM_ID', 'level_2': 'NAME', 'area_new_k': 'AREA_KM2'}


def query_url():
    params = {
        'where': '1=1',
        'outFields': ','.join(FIELDS),
        'returnGeometry': 'true',
        'outSR': EPSG,
        'geometryPrecision': 0,
        'f': 'geojson',
    }
    return f'{QUERY_URL}?{urlencode(params)}'


def download(url, timeout):
    try:
        with urlopen(Request(url, headers={'User-Agent': USER_AGENT}),
                     timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
        raise RuntimeError(f'Could not download HELCOM sub-basins from '
                           f'{QUERY_URL}: {error}') from error


def parse_geojson(body):
    """Validate the REST response and return it as a GeoDataFrame."""
    try:
        collection = json.loads(body)
    except ValueError as error:
        raise RuntimeError('HELCOM sub-basins: response is not JSON') from error
    if 'error' in collection:
        raise RuntimeError(f'HELCOM sub-basins: service error '
                           f'{collection["error"]}')
    if collection.get('exceededTransferLimit'):
        raise RuntimeError('HELCOM sub-basins: response was truncated')
    features = collection.get('features', [])
    if len(features) != EXPECTED_BASINS:
        raise RuntimeError(f'HELCOM sub-basins: expected {EXPECTED_BASINS} '
                           f'polygons, got {len(features)}')
    basins = gp.read_file(io.BytesIO(body)).set_crs(epsg=EPSG,
                                                    allow_override=True)
    basins = basins.rename(columns=FIELDS)
    basins['BASIN_NR'] = basins['HELCOM_ID'].str[-3:].astype(int)
    # As served, most polygons have ring self-intersections and degenerate
    # rings (the layer was generalized). Repair them, keeping the areas.
    basins['geometry'] = basins.geometry.make_valid().apply(polygonal_part)
    return basins[['BASIN_NR', 'HELCOM_ID', 'NAME', 'AREA_KM2', 'geometry']]


def polygonal_part(geom):
    """The (multi)polygon part of a geometry, dropping stray lines/points."""
    if geom.geom_type in ('Polygon', 'MultiPolygon'):
        return geom
    parts = [g for g in getattr(geom, 'geoms', [])
             if g.geom_type in ('Polygon', 'MultiPolygon')]
    return unary_union(parts)


def fetch_helcom_basins(shape_dir, timeout=600):
    """Download the sub-basins and write shape_dir/HELCOM_subbasins.shp."""
    path = shape_dir / SHAPEFILE
    print(f'downloading HELCOM sub-basins from ICES -> {path}')
    basins = parse_geojson(download(query_url(), timeout))
    shape_dir.mkdir(parents=True, exist_ok=True)
    basins.to_file(path)
    return path


def read_basins(shape_dir, basin_numbers=None, fetch=True):
    """HELCOM sub-basins in EPSG:3006, fetched to shape_dir if missing.

    basin_numbers: keep only these BASIN_NR values (default: all 17).
    """
    path = shape_dir / SHAPEFILE
    if not path.exists():
        if not fetch:
            raise SystemExit(f'Missing HELCOM basin shapefile: {path}; '
                             'see README (Data directory).')
        fetch_helcom_basins(shape_dir)
    basins = gp.read_file(path).to_crs(epsg=EPSG)
    if basin_numbers is not None:
        basins = basins[basins['BASIN_NR'].isin(basin_numbers)]
    return basins.sort_values('BASIN_NR').reset_index(drop=True)
