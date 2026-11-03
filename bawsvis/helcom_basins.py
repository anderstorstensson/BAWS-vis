# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""HELCOM sub-basins of the Baltic Sea: download and read.

The 17 level-2 assessment units of the HELCOM Monitoring and Assessment
Strategy, as published by HELCOM ("HELCOM subbasins 2022 (level 2)"):

    https://metadata.helcom.fi/geonetwork/srv/api/records/d4b6296c-fd19-462c-94d2-4c81b9313d77

The record's download link is a web page that asks the HELCOM Map and
Data Service (MADS) to package the dataset; the same geoprocessing call
is made here, and it answers with the URL of a zipped shapefile in Web
Mercator (EPSG:3857). The shapefile is reprojected to SWEREF99 TM
(EPSG:3006) and stored once as shape/HELCOM_subbasins.shp with

    HELCOM_ID   'SEA-001' .. 'SEA-017'
    BASIN_NR    the number in HELCOM_ID (1 .. 17), the integer key used
                by the pipeline (label raster, csv, workbooks)
    NAME        HELCOM English name (level_2)
    AREA_KM2    HELCOM's own area (area_new_k)

Data can be used freely given that the source (HELCOM) is cited.
"""
import json
import tempfile
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gp
from shapely.ops import unary_union

DATASET_ID = 'd4b6296c-fd19-462c-94d2-4c81b9313d77'
RECORD_URL = f'https://metadata.helcom.fi/geonetwork/srv/api/records/{DATASET_ID}'
PACKAGE_URL = ('https://maps.helcom.fi/arcgis/rest/services/MADS/tools/'
               'GPServer/getAndCompressDataSource/execute')
SHAPEFILE = 'HELCOM_subbasins.shp'
EPSG = 3006
EXPECTED_BASINS = 17
USER_AGENT = 'BAWS-vis helcom_basins'

FIELDS = {'HELCOM_ID': 'HELCOM_ID', 'level_2': 'NAME', 'area_new_k': 'AREA_KM2'}


def package_url():
    return f'{PACKAGE_URL}?{urlencode({"id": DATASET_ID, "f": "json"})}'


def download(url, timeout):
    try:
        with urlopen(Request(url, headers={'User-Agent': USER_AGENT}),
                     timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
        raise RuntimeError(f'Could not download HELCOM sub-basins from '
                           f'{url}: {error}') from error


def zip_url(body):
    """URL of the packaged dataset from the MADS geoprocessing response.

    The service reports failures with HTTP 200 and an 'error' result, so
    the response itself has to be checked.
    """
    try:
        response = json.loads(body)
    except ValueError as error:
        raise RuntimeError('HELCOM sub-basins: packaging response is not '
                           'JSON') from error
    if 'error' in response:
        raise RuntimeError(f'HELCOM sub-basins: service error '
                           f'{response["error"]}')
    results = {item.get('paramName'): item.get('value')
               for item in response.get('results', [])}
    if results.get('error'):
        raise RuntimeError(f'HELCOM sub-basins: packaging failed: '
                           f'{results["error"]}')
    url = (results.get('output_zip') or {}).get('url')
    if not url:
        raise RuntimeError('HELCOM sub-basins: packaging response has no '
                           'download URL')
    return url


def read_zipped_shapefile(archive):
    """The single shapefile in a zip archive (bytes) as a GeoDataFrame."""
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / 'dataset.zip'
        zip_path.write_bytes(archive)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp)
        except zipfile.BadZipFile as error:
            raise RuntimeError('HELCOM sub-basins: download is not a zip '
                               'archive') from error
        shapefiles = list(Path(tmp).glob('*.shp'))
        if len(shapefiles) != 1:
            raise RuntimeError(f'HELCOM sub-basins: expected one shapefile '
                               f'in the archive, found {len(shapefiles)}')
        return gp.read_file(shapefiles[0])


def prepare_basins(basins):
    """Validate the HELCOM layer and convert it to the stored layout."""
    if len(basins) != EXPECTED_BASINS:
        raise RuntimeError(f'HELCOM sub-basins: expected {EXPECTED_BASINS} '
                           f'polygons, got {len(basins)}')
    missing = set(FIELDS) - set(basins.columns)
    if missing:
        raise RuntimeError(f'HELCOM sub-basins: missing attributes '
                           f'{sorted(missing)}')
    if basins.crs is None:
        raise RuntimeError('HELCOM sub-basins: shapefile has no CRS')
    basins = basins.to_crs(epsg=EPSG).rename(columns=FIELDS)
    basins['BASIN_NR'] = basins['HELCOM_ID'].str[-3:].astype(int)
    # As published, most polygons have ring self-intersections and
    # degenerate rings. Repair them, keeping the areas.
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
    print(f'downloading HELCOM sub-basins from HELCOM MADS -> {path}')
    archive = download(zip_url(download(package_url(), timeout)), timeout)
    basins = prepare_basins(read_zipped_shapefile(archive))
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
