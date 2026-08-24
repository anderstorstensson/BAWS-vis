#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Run the BAWS-vis pipeline scripts in order.

Each numbered script in the repository root is run as its own process,
in pipeline order, stopping at the first failure. Seasons and the figure
year are passed to the scripts through the BAWS_YEARS / BAWS_PLOT_YEAR
environment variables (see bawsvis/selection.py).

Examples
--------
    uv run python run_pipeline.py --list
    uv run python run_pipeline.py                      # everything, all seasons
    uv run python run_pipeline.py --years 2025         # reprocess one season
    uv run python run_pipeline.py --from 9 --to 16     # statistics only
    uv run python run_pipeline.py --figures --plot-year 2024
    uv run python run_pipeline.py --steps 6 7 8 --dry-run
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from bawsvis.paths import data_dir
from bawsvis.selection import (PLOT_YEAR_ENV, YEARS_ENV, format_years,
                               parse_years)
from bawsvis.utils import discover_years

REPO_ROOT = Path(__file__).resolve().parent

# (key, script, description). Order matters: it is the pipeline order.
PROCESSING_STEPS = (
    ('1', '1_baws_correct_geoms.py',
     'Correct geometries, remove duplicates (daymaps -> corrected_geoms)'),
    ('2', '2_baws_rasterize_daily_shapefiles.py',
     'Rasterize daily shapefiles to tiff'),
    ('2.1', '2.1_baws_landmask_on_cyanoraster.py',
     'Remove bloom pixels on land from the daily tiffs'),
    ('3', '3_baws_create_weekly_aggregations.py',
     'Create 7-day composites (cyano_weekmap tiffs)'),
    ('4', '4_baws_shapeify_raster_data.py',
     'Shapeify daily/weekly tiffs (-> shapeified)'),
    ('5', '5_baws_shapeify_masked_cloud_data.py',
     'Shapeify daily cloud data (-> clouds)'),
    ('6', '6_baws_aggregate_daily_data.py',
     'Seasonal aggregation rasters, per season and all seasons'),
    ('7', '7_baws_shapeify_annual_raster_data.py',
     'Shapeify the seasonal aggregation rasters'),
    ('8', '8_baws_get_annual_stats.py',
     'Annual statistics workbook (all seasons)'),
    ('9', '9_baws_set_up_table_data.py',
     'Daily/weekly areas per date (stats_<year>.json)'),
    ('10', '10_baws_get_statistics.py',
     'Daily statistics (stats_<year>_2.json)'),
    ('11', '11_baws_get_cloud_cover_area.py',
     'Add cloud cover area to the daily statistics'),
    ('12', '12_baws_get_fca.py',
     'Add fractional cloud-free area (FCA) to the daily statistics'),
    ('13', '13_baws_get_fca_means.py',
     'FCA means per season and month (all seasons)'),
    ('14', '14_baws_area_stats.py',
     'Bloom and cloud cover per sea basin and date'),
    ('15', '15_baws_update_stat_file.py',
     'Combine daily statistics into stats_all.json (all seasons)'),
    ('16', '16_baws_bloom_start_end.py',
     'Bloom start/end/length per basin and the combined season workbook'),
    ('17', '17_baws_basin_daily_areas.py',
     'Daily cloud/bloom areas per sea basin from the daily tiffs'),
    ('18', '18_baws_bloom_indicator.py',
     'Bloom indicator (5 % FCA threshold) per basin and pooled (all seasons)'),
)

FIGURE_STEPS = (
    ('0_1', '0_1_baws_plot_single_map.py',
     'Fig 1: bloom-days map, all seasons'),
    ('0_2', '0_2_baws_season_diagram.py',
     'Fig 2: season diagram for one season (BAWS_PLOT_YEAR)'),
    ('0_3', '0_3_baws_plot_bars_TA_FCA.py',
     'Fig 3: TA / FCA bars, all seasons'),
    ('0_4', '0_4_baws_plot_basin_timeline.py',
     'Fig 4: bloom timeline per basin for one season (BAWS_PLOT_YEAR)'),
    ('0_5', '0_5_baws_plot_indicator.py',
     'Fig 5: bloom indicator time series, all seasons'),
)

ALL_STEPS = PROCESSING_STEPS + FIGURE_STEPS


def step_keys(steps=ALL_STEPS):
    return tuple(key for key, _, _ in steps)


def select_steps(steps, start=None, stop=None, only=None, skip=()):
    """Subset of `steps` in pipeline order.

    start/stop are inclusive step keys; only is an explicit list of keys
    (keeps pipeline order, not the given order); skip removes keys.
    Raises ValueError for unknown keys.
    """
    keys = step_keys(steps)
    for key in [k for k in (start, stop) if k] + list(only or []) + list(skip):
        if key not in keys:
            raise ValueError(
                f'Unknown step {key!r}. Known steps: {", ".join(keys)}')
    first = keys.index(start) if start else 0
    last = keys.index(stop) if stop else len(keys) - 1
    if last < first:
        raise ValueError(f'--to {stop} comes before --from {start}')
    chosen = steps[first:last + 1]
    if only:
        chosen = tuple(s for s in chosen if s[0] in set(only))
    return tuple(s for s in chosen if s[0] not in set(skip))


def child_environment(years=None, plot_year=None):
    """Environment for the scripts.

    Inherits the parent environment, but the season selection comes from
    the command line only: BAWS_YEARS / BAWS_PLOT_YEAR set in the shell
    are dropped unless --years / --plot-year were given. Output is made
    unbuffered so a redirected log shows progress as it happens.
    """
    env = {k: v for k, v in os.environ.items()
           if k not in (YEARS_ENV, PLOT_YEAR_ENV)}
    if years:
        env[YEARS_ENV] = format_years(years).replace(' ', '')
    if plot_year:
        env[PLOT_YEAR_ENV] = str(plot_year)
    env['PYTHONUNBUFFERED'] = '1'
    return env


def latest_processed_season():
    """Most recent season with daily statistics (stats_<year>_2.json)."""
    years = discover_years(data_dir('stats'), pattern='stats_',
                           endswith='_2.json')
    return years[-1] if years else None


def with_default_plot_year(env):
    """Pin BAWS_PLOT_YEAR to the latest processed season if not set.

    Called right before the first figure step, i.e. after any processing
    steps in the same run, so that 0_2 and 0_4 draw the same season
    instead of each picking "latest" from its own input files.
    """
    if env.get(PLOT_YEAR_ENV):
        return env
    year = latest_processed_season()
    if year is None:
        return env
    print(f'Figure year: {year} (latest processed season)', flush=True)
    return {**env, PLOT_YEAR_ENV: str(year)}


def is_figure_step(step):
    return step in FIGURE_STEPS


def run_step(step, env, dry_run=False):
    """Run one script; return (ok, seconds)."""
    key, script, description = step
    print(f'\n=== Step {key}: {description}\n    {script}', flush=True)
    if dry_run:
        return True, 0.0
    started = time.monotonic()
    result = subprocess.run([sys.executable, str(REPO_ROOT / script)],
                            cwd=REPO_ROOT, env=env)
    return result.returncode == 0, time.monotonic() - started


def run_steps(steps, env, dry_run=False):
    """Run steps in order, stopping at the first failure. Returns exit code."""
    for step in steps:
        if is_figure_step(step) and not dry_run:
            env = with_default_plot_year(env)
        ok, seconds = run_step(step, env, dry_run=dry_run)
        if not ok:
            print(f'\nStep {step[0]} failed ({step[1]}); stopping. '
                  f'Fix the problem and rerun with --from {step[0]}.',
                  file=sys.stderr)
            return 1
        if not dry_run:
            print(f'    done in {seconds:.0f} s', flush=True)
    return 0


def list_steps():
    print('Processing steps (run in this order):')
    for key, script, description in PROCESSING_STEPS:
        print(f'  {key:>4}  {script:<42} {description}')
    print('Figure steps:')
    for key, script, description in FIGURE_STEPS:
        print(f'  {key:>4}  {script:<42} {description}')


def build_parser():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog='Step keys: ' + ', '.join(step_keys()),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--years', nargs='+', metavar='YEARS',
                        help=f'Seasons to (re)process in the per-season '
                             f'steps, e.g. 2025 or 2002-2010 or 2019 2021. '
                             f'Sets {YEARS_ENV}. Default: all seasons on disk.')
    parser.add_argument('--plot-year', type=int, metavar='YEAR',
                        help=f'Season drawn by figures 0_2 and 0_4. '
                             f'Sets {PLOT_YEAR_ENV}. Default: latest season.')
    parser.add_argument('--from', dest='start', metavar='STEP',
                        help='First step to run (inclusive)')
    parser.add_argument('--to', dest='stop', metavar='STEP',
                        help='Last step to run (inclusive)')
    parser.add_argument('--steps', nargs='+', metavar='STEP',
                        help='Run only these steps (in pipeline order)')
    parser.add_argument('--skip', nargs='+', default=(), metavar='STEP',
                        help='Steps to leave out')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--figures', action='store_true',
                       help='Run only the figure scripts (0_1 to 0_4)')
    group.add_argument('--no-figures', action='store_true',
                       help='Run the processing steps but not the figures')
    parser.add_argument('--list', action='store_true',
                        help='List the steps and exit')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would run without running it')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.list:
        list_steps()
        return 0

    try:
        years = parse_years(' '.join(args.years)) if args.years else None
    except ValueError as error:
        print(f'error: --years: {error}', file=sys.stderr)
        return 2
    if args.plot_year and years and args.plot_year not in years:
        print(f'Note: --plot-year {args.plot_year} is not among --years '
              f'{format_years(years)}; the figures use the statistics '
              f'already on disk for that season.', file=sys.stderr)

    pool = FIGURE_STEPS if args.figures else (
        PROCESSING_STEPS if args.no_figures else ALL_STEPS)
    try:
        steps = select_steps(pool, start=args.start, stop=args.stop,
                             only=args.steps, skip=args.skip)
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2
    if not steps:
        print('error: no steps selected', file=sys.stderr)
        return 2

    env = child_environment(years, args.plot_year)
    print(f'Seasons: {format_years(years) if years else "all on disk"}; '
          f'figure year: {args.plot_year or "latest"}; '
          f'steps: {", ".join(step_keys(steps))}')
    return run_steps(steps, env, dry_run=args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
