# Visualize BAWS data

## Work-in-progress README
BAWS-vis produces the statistics and figures for the yearly Baltic Sea cyanobacteria season report, and a yearly table of bloom extent, bloom start and bloom length. The numbered files in the root folder (1 to 16) are run in that order to prepare the data for the figure scripts 0_1 to 0_4. All scripts read and write below one data directory (see Setup), so no file paths need to be edited.

TODO (incomplete):
- Remove unnecessary code in all files
- Refactor code to better integrate existing SMHI tools and data workflow
    - Implement FAIR principles
- Remove remaining hardcoded constants (for example the valid BAWS area of 359429 km2)
- Annotate code and improve readability (PEP 8 compliance)

## Setup
The project uses [uv](https://docs.astral.sh/uv/) for the Python environment and needs Python 3.11 or 3.12.

Linux/macOS:
```bash
git clone <repository-url> && cd BAWS-vis
uv sync
```

Windows (PowerShell):
```powershell
git clone <repository-url>; cd BAWS-vis
uv sync
```

### Data directory
All scripts read and write below one data root, by default `data/` in the repository. Set `BAWS_DATA_ROOT` to use another location:
```bash
export BAWS_DATA_ROOT=/path/to/baws_data
```
```powershell
$env:BAWS_DATA_ROOT = "D:\baws_data"
```

The scripts create these folders as needed:
```
daymaps/          raw daily cyano_daymap_YYYYMMDD.shp
corrected_geoms/  cleaned shapefiles plus daily and weekly tiffs (scripts 1 to 3)
shapeified/       shapefiles regenerated from the rasters (script 4)
clouds/           daily cloud shapefiles (script 5)
aggregates/       seasonal aggregation rasters and annual shapefiles (scripts 6 and 7)
stats/            json and xlsx statistics (scripts 8 to 16)
figures/          png output of the figure scripts
shape/            static inputs, see below
```

Two static inputs go in `shape/`. They are not part of the repository.
- `Havsomr_SVAR_2016_3b_CP1252.*`: the SVAR sea basins used by script 14. Available from SMHI open data (Havsområden SVAR2016).
- `GSHHS_h_L1.*`: the GSHHS high resolution coastline used by the map figure. Take it from `GSHHS_shp/h/` in the gshhg-shp archive at https://www.soest.hawaii.edu/pwessel/gshhg/.

## Running the pipeline
The daily maps can be downloaded from SMHI's open data WFS instead of being copied from the file server. One shapefile per day is written to `daymaps/`. Days that already exist are skipped, so the download can be rerun after an interruption.
```bash
uv run python fetch_wfs_daymaps.py --years 2002-2026 --out data/daymaps
```

## Original README
Post season processing pinpoints
--------------------------------
Products we want to produce:
1. Quality controlled data (daily/weekly - shp/raster)
2. Daily areas (subsurface, surface, weekly-composition, clouds over area of interest) for each date (json)
3. Aggregated data (seasonal matrix - raster)
4. Figures based on the data above (png)


Different data formats for different purposes. 
Shapefiles for:
- manual adjustment in QGIS
- Calculating areas

Geotiff for:
- aggregations
- masking (coastal, basin areas)

JSON/Excel for:
- areas
- statistics

Workflow - Data processing
----------
Step 1: Copy all the shp/raster files from the server to the local machine, or download them with `fetch_wfs_daymaps.py` (see Running the pipeline above).

Step 2: Manually quality control data for each date. This includes:
- Start with going through "Algarkivet" on smhi.se to spot false positives. Compare to RGB-images form the file server.
- Open any suspicious files in QGIS and adjust if needed.

Step 3: Run the script `baws_correct_geoms.py` -> This will correct geometries (eg. bowtie geometries) and remove duplicates.

Step 4: Rasterize the shapefiles using `baws_rasterize_daily_shapefiles.py` -> This will create a raster for each date.

Step 5: Create weekly composites using `baws_create_weekly_aggregations.py` -> This will create a weekly composite for each date using the past 7 days.

Step 6: Shapeify the weekly composites using `baws_shapeify_raster_data.py` -> This will create a shapefile for each weekly composite.

Step 7: Create daily cloud data using `baws_shapeify_masked_cloud_data.py` -> This will create a raster for each date with cloud data.

Step 8: Create a seasonal bloom aggregation 2D array using `baws_aggregate_daily_data.py` -> This will create a 2D array for the given season.

Step 9: Calculate seasonal stats using the datafile above and `baws_get_annual_stats.py` -> This will create an excel file with stats for the given season. 

Step 10: Calculate areas for each date using `baws_get_statistics.py` -> This will create a json file with areas for each date.

Step 11: Mark bloom and cloud cover per sea basin and date using `baws_area_stats.py` -> This will create an excel file per season with one row per basin.

Step 12: Calculate bloom start, end and length using `baws_bloom_start_end.py` -> This will create an excel file with one row per year and basin, a yearly summary, and the combined workbook used by Fig 4.

Create figures
--------------
Fig 1: Seasonal bloom aggregation 2D array (heatmap) -> `baws_plot_single_map.py`

Fig 2: Season diagram (line plot) -> `baws_season_diagram.py`

Fig 3: Plot TA / FCA (bar plot) -> `baws_plot_bars_TA_FCA.py`

Fig 4: Bloom timeline per sea basin (bar plot) -> `baws_plot_basin_timeline.py`