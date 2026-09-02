# Visualize BAWS data

## Work-in-progress README
BAWS-vis produces the statistics and figures for the yearly Baltic Sea cyanobacteria season report, and a yearly table of bloom extent, bloom start and bloom length. The numbered files in the root folder (1 to 18) are run in that order to prepare the data for the figure scripts 0_1 to 0_5. All scripts read and write below one data directory (see Setup), so no file paths need to be edited.

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

Two static inputs live in `shape/`. They are not part of the repository.
- `HELCOM_subbasins.*`: the 17 HELCOM sub-basins of the Baltic Sea (level-2 assessment units of the HELCOM Monitoring and Assessment Strategy, 2013), used by scripts 14 and 17. Downloaded automatically the first time either script runs, from the ICES ArcGIS REST service behind the [ICES/HELCOM record](https://gis.ices.dk/geonetwork/srv/api/records/225df9db-bfdf-4388-8ccb-fa4b99053a36), reprojected to SWEREF99 TM, topologically repaired and written as a shapefile with `HELCOM_ID` (SEA-001 to SEA-017), `BASIN_NR` (the number in the id), `NAME` and `AREA_KM2` (`bawsvis/helcom_basins.py`). Data can be used freely given that HELCOM is cited as the source. Delete the files to force a fresh download. The basins used are listed in `bawsvis/basins.py`, with Swedish names for the figures and the delivery files.
- `GSHHS_h_L1.*`: the GSHHS high resolution coastline used by the map figure. Take it from `GSHHS_shp/h/` in the gshhg-shp archive at https://www.soest.hawaii.edu/pwessel/gshhg/.

## Running the pipeline

### 1. Get the daily maps
The daily maps can be downloaded from SMHI's open data WFS instead of being copied from the file server. One shapefile per day is written to `daymaps/`. Days that already exist are skipped, so the download can be rerun after an interruption.
```bash
uv run python fetch_wfs_daymaps.py --years 2002-2026 --out data/daymaps
```
Quality control the daymaps in QGIS before continuing (see the original README below).

### 2. Run the processing steps and the figures
`run_pipeline.py` runs the numbered scripts in order, each in its own process, and stops at the first script that fails. With no options it processes every season found in `daymaps/` and then draws the four figures.
```bash
uv run python run_pipeline.py --list            # show the steps and what they produce
uv run python run_pipeline.py                   # everything: steps 1-18, then figures 0_1-0_5
uv run python run_pipeline.py --no-figures      # processing only
uv run python run_pipeline.py --figures         # figures only (needs steps 1-18 done once)
uv run python run_pipeline.py --indicator       # indicator data files only (steps 1, 2, 2.1, 17, 18)
uv run python run_pipeline.py --from 9 --to 16  # a range of steps, e.g. statistics only
uv run python run_pipeline.py --steps 6 7 8     # specific steps (always run in pipeline order)
uv run python run_pipeline.py --skip 2.1        # leave a step out
uv run python run_pipeline.py --dry-run ...     # print the plan without running it
```
When a step fails, the error message names it. Fix the cause and continue with `--from <step>`. The scripts can also be run one at a time with `uv run python <script>.py`.

### Processing one season or a range of seasons
`--years` limits the per-season steps to the seasons you name. After a new season has been downloaded and quality controlled, run:
```bash
uv run python run_pipeline.py --years 2026
```
Years can be given as `--years 2026`, `--years 2002-2010` or `--years 2019 2021`, and must lie between 2002 and the current year.

The restriction applies to steps 1 to 7, 9 to 12, 14 and 17. Steps 8, 13, 15, 16 and 18 always read every season on disk. They produce the climatology and the all-season tables (the mean and standard deviation season curve, the FCA means, `stats_all.json` and the combined season workbook) that the new season is compared against in the figures, and they only read the per-season summary files, so they are quick.

Step 6 is a special case. It writes the per-season aggregation tiff only for the selected seasons, but it always rebuilds the all-season matrix for figure 1, which means reading every daily tiff. This is the slowest part of a single-season rerun. Use `--skip 6` when figure 1 does not need to be updated.

`--years` works by setting the environment variable `BAWS_YEARS`, which the scripts read through `bawsvis/selection.py`. The variable can also be set by hand when running a single script:
```bash
BAWS_YEARS=2026 uv run python 10_baws_get_statistics.py
```
```powershell
$env:BAWS_YEARS = "2026"; uv run python 10_baws_get_statistics.py
```

### Figures for a specific season
Figure 1 (`0_1`, map of bloom days), figure 3 (`0_3`, TA and FCA bars) and figure 5 (`0_5`, bloom indicator) always cover all seasons. Figure 2 (`0_2`, season diagram) and figure 4 (`0_4`, basin timeline) show one season. By default this is the latest season that has daily statistics on disk, and `run_pipeline.py` uses the same year for both figures. Choose another season with `--plot-year`:
```bash
uv run python run_pipeline.py --figures --plot-year 2024
```
This writes `figures/diagram_2024.png` and `figures/basin_timeline_2024.png`. Figures for other seasons are not touched. `--plot-year` sets the environment variable `BAWS_PLOT_YEAR`, so `BAWS_PLOT_YEAR=2024 uv run python 0_2_baws_season_diagram.py` has the same effect for a single script. The season must have been processed first: its `stats_<year>_2.json` and its sheet in the combined season workbook must exist.

## Bloom indicator (steps 17, 18 and figure 0_5)
A threshold-based indicator of bloom extent, start and length, per sea basin and for all basins pooled, intended for a climate indicator. It is computed from the daily 1 km class rasters rather than from the first/last day a bloom polygon touched a basin, so single pixels and single clear days do not set the dates.

- Step 17 (`17_baws_basin_daily_areas.py`) counts cloud, subsurface and surface pixels per HELCOM sub-basin and day inside the BAWS valid area (`raster_landmask_baws1000_sweref99tm.tiff`, 352 682 km2) and writes `stats/basin_daily_areas_<year>.csv`, with `basin_nr` the HELCOM sub-basin number (SEA-0nn). The basin label raster is cached as `stats/basin_labels_helcom_baws1000.tiff`; delete it if the basin shapefile changes.
- Step 18 (`18_baws_bloom_indicator.py`) applies `bawsvis/indicator.py` and writes `stats/bloom_indicator_<first>-<last>.xlsx` (sheets `all_basins`, `per_basin`, `method`), the same table as csv, and the `indicator/data_cyanoblomning_JJA_<basin>_<parameter>.txt` delivery series.

### Updating the indicator after a season
The indicator files only need the daily class tiffs, not the rest of the pipeline. After the season:
```bash
uv run python fetch_wfs_daymaps.py --years 2026 --out data/daymaps
# quality control the new daymaps in QGIS, then
uv run python run_pipeline.py --indicator --years 2026
```
`--indicator` runs steps 1, 2 and 2.1 (daymaps to landmasked daily tiffs) for the selected seasons, step 17 (per-basin daily areas) and step 18, which always recomputes the indicator from every season on disk. Weekly composites, the statistics files and the figures are left untouched; run the full pipeline when those need the new season too. A season whose window has not yet passed (plus a grace week) is flagged preliminary and kept out of the text series until a later run finds it complete.

Method (parameters in `bawsvis/indicator.py`):
- Daily FCA = bloom area / cloud-free observed area in the basin. A day is unusable for a basin if less than 20 % of the basin was observed. "All basins" sums the areas of the 14 basins in `bawsvis/basins.py` (324 988 km2) before the ratio is taken, so it is the same quantity at another aggregation level. Kattegat and The Quark (SEA-001, SEA-016) are inside the BAWS area but not among the 14 basins and are therefore not part of the pooled value; Bothnian Bay (SEA-017) is outside the BAWS area. Compared with the SVAR basins used before, the Archipelago Sea is now part of Ålands hav, Bälthavet is split into Stora Bält, Kielbukten and Mecklenburgbukten, and Gdanskbukten is much smaller (most of the former SVAR basin belongs to the HELCOM Eastern Gotland Basin).
- Season window is fixed to 1 June to 31 August.
- Start and end are the first and last day the 7-day centred running mean of FCA is at least 5 % for at least 3 consecutive days. `span_days` is end to start inclusive, `bloom_days` the number of days the smoothed FCA is at least 5 % (can exceed the span when short runs occur outside the persistent period).
- Extent is `mean_fca`, the mean daily FCA over the window (unobserved days excluded), with `mean_bloom_km2` and `peak_fca` / `peak_date` as supporting values.
- `surface_days` counts days with smoothed surface-accumulation FCA of at least 1 %.
- `observed_fraction` is the share of window days that were usable; seasons below 60 % are flagged `low_coverage` and drawn hollow or hatched in figure 5.
- Absolute values only; no climatology or trend is computed because the record is short.

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