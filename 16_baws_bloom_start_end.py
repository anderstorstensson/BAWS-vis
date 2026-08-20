#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Bloom start, end and length per basin and year.

Reads the per-year basin x date tables from script 14
(area_season_bloom_<year>_incl_cloud.xlsx) and writes, to the stats
directory:

  bloom_start_end_<first>-<last>.xlsx
      per_basin : one row per year and basin with bloom start/end dates,
                  bloom length (days, start to end inclusive) and the
                  number of observed bloom days
      yearly    : one row per year combining basin-wide bloom start/end/
                  length, the mean across basins, and the extent metrics
                  from scripts 8 and 13
      climatology : mean/median/std of start and end per basin over all
                  years (what the box plot draws as reference bars)

  area_season_bloom_all_<first>-<last>.xlsx
      the combined workbook (one sheet per year + a stats sheet) that the
      basin timeline figure (0_4) reads. Replaces the earlier manual
      copy-paste assembly of that workbook.

Bloom = class 2 (subsurface) or 3 (surface) touching the basin that day.
"""
import numpy as np
import pandas as pd

from bawsvis.basins import BASIN_NAMES, basin_key
from bawsvis.paths import data_dir
from bawsvis.utils import discover_years

BLOOM_CLASSES = (2, 3)


def read_year_table(stats_dir, year):
    """Basin x date table for one year, BASIN_NR_<n> first, dates sorted."""
    df = pd.read_excel(stats_dir / f'area_season_bloom_{year}_incl_cloud.xlsx')
    date_cols = sorted(c for c in df.columns if c != 'BASIN')
    basins = pd.DataFrame({'BASIN': [basin_key(b) for b in df['BASIN']]})
    dates = df[date_cols].rename(columns=str)
    return pd.concat([basins, dates], axis=1)


def basin_start_end(table):
    """Per-basin start/end/bloom days for one year's table."""
    rows = []
    date_cols = [c for c in table.columns if c != 'BASIN']
    for _, row in table.iterrows():
        values = row[date_cols]
        bloom_dates = [pd.Timestamp(d) for d, v in zip(date_cols, values)
                       if v in BLOOM_CLASSES]
        rows.append({
            'basin': row['BASIN'],
            'start': min(bloom_dates) if bloom_dates else pd.NaT,
            'end': max(bloom_dates) if bloom_dates else pd.NaT,
            'bloom_days': len(bloom_dates),
        })
    return rows


def per_basin_table(stats_dir, years):
    records = []
    for year in years:
        table = read_year_table(stats_dir, year)
        for r in basin_start_end(table):
            records.append({'year': year, **r})
        # Basin-wide ("All"): earliest start / latest end over all basins.
        starts = [r['start'] for r in records
                  if r['year'] == year and not pd.isnull(r['start'])]
        ends = [r['end'] for r in records
                if r['year'] == year and not pd.isnull(r['end'])]
        records.append({
            'year': year, 'basin': 'All',
            'start': min(starts) if starts else pd.NaT,
            'end': max(ends) if ends else pd.NaT,
            'bloom_days': np.nan,
        })
    df = pd.DataFrame(records)
    df['length_days'] = (df['end'] - df['start']).dt.days + 1
    df['basin_nr'] = df['basin'].map(
        lambda b: int(b.split('_')[-1]) if b != 'All' else np.nan)
    df['basin_name'] = df['basin_nr'].map(BASIN_NAMES).fillna('All')
    return df[['year', 'basin', 'basin_nr', 'basin_name', 'start', 'end',
               'length_days', 'bloom_days']]


def _in_dummy_year(series, year):
    return pd.Series([ts.replace(year=year) for ts in series.dropna()])


def _std_text(series):
    comp = series.std().components
    return f'{comp.days} days {comp.hours} hours'


def climatology_table(per_basin, dummy_year):
    """Mean/median/std of start and end per basin, dated in dummy_year.

    Same statistics as the original get_history_bloom_start_end.py.
    """
    rows = []
    for basin, grp in per_basin.groupby('basin', sort=False):
        starts = _in_dummy_year(grp['start'], dummy_year)
        ends = _in_dummy_year(grp['end'], dummy_year)
        if starts.empty:
            continue
        rows.append({
            'BASIN': basin,
            'mean_start': starts.mean(),
            'std_dev_start': _std_text(starts),
            'mean_end': ends.mean(),
            'median_start': starts.median(),
            'median_end': ends.median(),
            'std_dev_end': _std_text(ends),
        })
    return pd.DataFrame(rows)


def yearly_table(per_basin, stats_dir):
    basins = per_basin[per_basin['basin'] != 'All']
    whole = per_basin[per_basin['basin'] == 'All'].set_index('year')

    def mean_date(group, col):
        values = group[col].dropna()
        if values.empty:
            return pd.NaT
        doy = np.mean([ts.dayofyear for ts in values])
        return pd.Timestamp(group.name, 1, 1) + pd.Timedelta(days=round(doy) - 1)

    per_year = basins.groupby('year')
    yearly = pd.DataFrame({
        'bloom_start': whole['start'],
        'bloom_end': whole['end'],
        'bloom_length_days': whole['length_days'],
        'mean_basin_start': per_year.apply(lambda g: mean_date(g, 'start')),
        'mean_basin_end': per_year.apply(lambda g: mean_date(g, 'end')),
        'mean_basin_length_days': per_year['length_days'].mean().round(1),
        'basins_with_bloom': per_year['start'].count(),
    })

    annual_files = sorted(stats_dir.glob('annual_stats_norm_*.xlsx'))
    if annual_files:
        annual = pd.read_excel(annual_files[-1]).set_index('year')
        yearly = yearly.join(annual[['total_area', 'extent', 'duration',
                                     'intensity']])
    fca_file = stats_dir / 'fca_means.xlsx'
    if fca_file.exists():
        fca = pd.read_excel(fca_file).set_index('year')
        yearly = yearly.join(fca[['median_period']].rename(
            columns={'median_period': 'fca_median_period'}))
    return yearly.reset_index()


def main():
    stats_dir = data_dir('stats')
    years = discover_years(stats_dir, pattern='area_season_bloom_',
                           endswith='_incl_cloud.xlsx')
    if not years:
        raise SystemExit(f'No area_season_bloom_<year>_incl_cloud.xlsx in '
                         f'{stats_dir}; run script 14 first')
    span = f'{years[0]}-{years[-1]}'

    per_basin = per_basin_table(stats_dir, years)
    climatology = climatology_table(per_basin, dummy_year=years[-1])
    yearly = yearly_table(per_basin, stats_dir)

    out = stats_dir / f'bloom_start_end_{span}.xlsx'
    with pd.ExcelWriter(out) as writer:
        yearly.to_excel(writer, sheet_name='yearly', index=False)
        per_basin.to_excel(writer, sheet_name='per_basin', index=False)
        climatology.to_excel(writer, sheet_name='climatology', index=False)
    print('wrote', out)

    combined = stats_dir / f'area_season_bloom_all_{span}.xlsx'
    with pd.ExcelWriter(combined) as writer:
        climatology.to_excel(writer, sheet_name=f'stats_{span}', index=False)
        for year in years:
            read_year_table(stats_dir, year).to_excel(
                writer, sheet_name=str(year), index=False)
    print('wrote', combined)


if __name__ == "__main__":
    main()
