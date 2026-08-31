#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Cross-platform locations for the BAWS-vis pipeline.

All pipeline scripts read and write below a single data root so that no
script needs hardcoded, platform-specific paths. The root defaults to
<repository>/data and can be overridden with the BAWS_DATA_ROOT
environment variable (any absolute path, Windows or POSIX).

Standard stage directories under the data root:

    daymaps/          raw daily cyano_daymap_YYYYMMDD.shp
                      (from fetch_wfs_daymaps.py or the SMHI file server)
    corrected_geoms/  script 1 output; scripts 2-3 write daily/weekly
                      tiffs alongside these shapefiles
    shapeified/       script 4 output; non-overlapping shp regenerated
                      from the daily rasters (used for area statistics)
    clouds/           script 5 output; daily cloud shapefiles
    aggregates/       scripts 6-7 output; seasonal aggregation rasters,
                      text matrices and annual shapefiles
    stats/            scripts 8-15 output; json/xlsx statistics
    indicator/        script 18 output; indicator text series (year;value)
    figures/          plotting output (0_1-0_3, box plots)
    shape/            static user-provided inputs (not generated, not in
                      git): the SVAR sea-basin shapefile used by scripts
                      14 and 17 (Havsomr_SHARK_mod_SVAR2022_v1.*, the
                      SHARK-modified SVAR2022 basins with BASIN_NR)
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_ROOT = Path(os.environ.get('BAWS_DATA_ROOT', REPO_ROOT / 'data'))

STAGES = (
    'daymaps',
    'corrected_geoms',
    'shapeified',
    'clouds',
    'aggregates',
    'stats',
    'indicator',
    'figures',
    'shape',
)


def data_dir(stage, create=True):
    """Return (and by default create) a stage directory under DATA_ROOT."""
    if stage not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}. Choose one of {STAGES}")
    path = DATA_ROOT / stage
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def repo_file(*parts):
    """Return the path to a file shipped with the repository."""
    path = REPO_ROOT.joinpath(*parts)
    if not path.exists():
        raise FileNotFoundError(f"Expected repository file is missing: {path}")
    return path
