#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Bloom climate indicator: start, end, length, extent per basin and pooled.

Reads every stats/basin_daily_areas_<year>.csv (script 17) and applies
bawsvis.indicator (5 % FCA threshold, 3-day persistence, 7-day smoothing,
fixed 1 Jun - 30 Sep window). Writes

  stats/bloom_indicator_<first>-<last>.xlsx
      all_basins : one row per year, the pooled indicator
      per_basin  : one row per year and basin
      method     : the parameters used
  stats/bloom_indicator_<first>-<last>.csv   (per_basin + all, long)
  indicator/data_cyanoblomning_JJAS_<basin>_<parameter>.txt
      one year;value line per year (LF, empty value when undefined),
      basin 'sverige' for the pooled series, else the basin name;
      parameters: startdatum (day of year), blomningsdagar (days with
      smoothed FCA >= threshold), cyanoblomningens_langd (span_days,
      start to end), medelutbredning (mean FCA x basin sea area,
      1000 km2), maxutbredning (peak smoothed FCA x basin sea area,
      1000 km2; supporting series, coverage-sensitive) and
      observerad_andel (percent of season days with a usable FCA
      value, the basis of the quality flag)

Always reads all seasons on disk (ignores BAWS_YEARS).
"""
import pandas as pd

from bawsvis import indicator as ind
from bawsvis.basins import BASIN_NAMES
from bawsvis.paths import data_dir
from bawsvis.utils import discover_years

TEXT_PREFIX = 'data_cyanoblomning_JJAS'
POOLED_TEXT_BASIN = 'sverige'

METHOD = {
    'fca_threshold': ind.THRESHOLD,
    'surface_fca_threshold': ind.SURFACE_THRESHOLD,
    'persistence_days': ind.PERSIST,
    'smoothing_window_days': ind.WINDOW,
    'min_observed_fraction_per_day': ind.MIN_OBSERVED_FRACTION,
    'min_season_coverage': ind.MIN_SEASON_COVERAGE,
    'season_window': f'{ind.SEASON_START[0]:02d}-{ind.SEASON_START[1]:02d}'
                     f' to {ind.SEASON_END[0]:02d}-{ind.SEASON_END[1]:02d}',
    'valid_area': 'raster_landmask_baws1000_sweref99tm.tiff',
}


def read_daily_areas(stats_dir, years):
    frames = [pd.read_csv(stats_dir / f'basin_daily_areas_{year}.csv',
                          parse_dates=['date']) for year in years]
    return pd.concat(frames, ignore_index=True)


def with_names(table):
    names = table['basin_nr'].map(
        lambda b: BASIN_NAMES.get(b, ind.ALL_BASINS))
    return table.assign(basin_name=names)[
        ['year', 'basin_nr', 'basin_name', *ind.METRIC_COLUMNS]]


def day_of_year(value):
    return '' if pd.isna(value) else str(value.dayofyear)


def span_days(row):
    return '' if pd.isna(row['start']) else str(int(row['span_days']))


def bloom_days(row):
    return '' if pd.isna(row['mean_fca']) else str(int(row['bloom_days']))


def extent_1000km2(row, column):
    if pd.isna(row[column]):
        return ''
    return f"{row[column] * row['valid_km2'] / 1000:.1f}"


TEXT_PARAMETERS = {
    'startdatum': lambda row: day_of_year(row['start']),
    'blomningsdagar': bloom_days,
    'cyanoblomningens_langd': span_days,
    'medelutbredning': lambda row: extent_1000km2(row, 'mean_fca'),
    'maxutbredning': lambda row: extent_1000km2(row, 'peak_smoothed_fca'),
    'observerad_andel': lambda row: str(round(row['observed_fraction'] * 100)),
}


def basin_token(name):
    return name.lower().translate(str.maketrans('åäö', 'aao')).replace(' ', '_')


def write_text_series(out_dir, token, rows):
    for parameter, value in TEXT_PARAMETERS.items():
        lines = [f'{int(row["year"])};{value(row)}' for row in rows]
        path = out_dir / f'{TEXT_PREFIX}_{token}_{parameter}.txt'
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8',
                        newline='\n')


def write_text_files(table, out_dir):
    for basin, group in table.groupby('basin_name', sort=False):
        token = POOLED_TEXT_BASIN if basin == ind.ALL_BASINS \
            else basin_token(basin)
        rows = group.sort_values('year').to_dict('records')
        write_text_series(out_dir, token, rows)
    print('wrote', len(table['basin_name'].unique()) * len(TEXT_PARAMETERS),
          'text series in', out_dir)


def main():
    stats_dir = data_dir('stats')
    years = discover_years(stats_dir, pattern='basin_daily_areas_',
                           endswith='.csv')
    if not years:
        raise SystemExit(f'No basin_daily_areas_<year>.csv in {stats_dir}; '
                         'run script 17 first')
    table = with_names(ind.indicator_table(read_daily_areas(stats_dir, years)))
    pooled = table[table['basin_nr'] == ind.ALL_BASINS].drop(
        columns=['basin_nr', 'basin_name'])
    per_basin = table[table['basin_nr'] != ind.ALL_BASINS]

    span = f'{years[0]}-{years[-1]}'
    out = stats_dir / f'bloom_indicator_{span}.xlsx'
    with pd.ExcelWriter(out) as writer:
        pooled.to_excel(writer, sheet_name='all_basins', index=False)
        per_basin.to_excel(writer, sheet_name='per_basin', index=False)
        pd.DataFrame(list(METHOD.items()), columns=['parameter', 'value']) \
            .to_excel(writer, sheet_name='method', index=False)
    table.to_csv(stats_dir / f'bloom_indicator_{span}.csv', index=False,
                 date_format='%Y-%m-%d')
    write_text_files(table, data_dir('indicator'))
    print('wrote', out)
    print(pooled.to_string(index=False))


if __name__ == '__main__':
    main()
