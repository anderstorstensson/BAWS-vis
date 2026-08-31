#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Fig 5: bloom indicator time series (all seasons).

Reads stats/bloom_indicator_<first>-<last>.csv (script 18) and writes

  figures/indicator_all_basins.png   pooled start-end, bloom days, mean FCA
                                     and surface days per year
  figures/indicator_per_basin.png    year x basin heatmaps of the same
                                     metrics
  figures/indicator_bars.png         the three main exported series
                                     (startdatum, blomningsdagar,
                                     medelutbredning) as pooled bar graphs

Seasons flagged low_coverage are drawn with hollow markers / hatched bars.
"""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bawsvis import indicator as ind
from bawsvis.basins import PLOTTED_BASINS, BASIN_NAMES
from bawsvis.paths import data_dir

HUE = '#1f5f8b'          # single series hue
HUE_LIGHT = '#9cc3dc'
INK = '#333333'
INK_MUTED = '#777777'
GRID = '#e5e5e5'
DUMMY_YEAR = 2001        # common year for day-of-season axes

PANELS = (
    ('bloom_days', 'Bloom days (smoothed FCA ≥ 5 %)', 'days'),
    ('mean_fca', 'Mean bloom extent, 1 Jun–30 Sep', 'fraction of observed area'),
    ('surface_days', 'Surface accumulation days (≥ 1 %)', 'days'),
)


def read_indicator(stats_dir):
    files = sorted(stats_dir.glob('bloom_indicator_*.csv'))
    if not files:
        raise SystemExit('No bloom_indicator_*.csv found; run script 18 first')
    return pd.read_csv(files[-1], parse_dates=['start', 'end', 'peak_date'])


def style_axis(ax, ylabel):
    ax.set_ylabel(ylabel, color=INK_MUTED, fontsize=9)
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.spines['left'].set_color(GRID)
    ax.spines['bottom'].set_color(GRID)
    ax.tick_params(colors=INK, labelsize=9)


def day_of_season(ts):
    return np.array([mdates.date2num(t.replace(year=DUMMY_YEAR)) if pd.notna(t)
                     else np.nan for t in ts])


def plot_span(ax, pooled):
    start, end = day_of_season(pooled['start']), day_of_season(pooled['end'])
    ok = pooled['quality'] == 'ok'
    for flag, hatch in ((ok, None), (~ok, '///')):
        sel = flag & ~np.isnan(start)
        ax.bar(pooled.loc[sel, 'year'], (end - start + 1)[sel], bottom=start[sel],
               width=0.7, color=HUE if hatch is None else 'white',
               edgecolor=HUE, hatch=hatch, linewidth=1)
    ax.yaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%-d %b'))
    ax.set_ylim(mdates.date2num(pd.Timestamp(DUMMY_YEAR, *ind.SEASON_START)),
                mdates.date2num(pd.Timestamp(DUMMY_YEAR, *ind.SEASON_END)))
    style_axis(ax, '')
    ax.set_title('Bloom period (start to end)', loc='left', fontsize=11,
                 color=INK)


def plot_series(ax, pooled, column, title, ylabel):
    ax.plot(pooled['year'], pooled[column], color=HUE, linewidth=2, zorder=2)
    ax.set_xlim(pooled['year'].min() - 0.5, pooled['year'].max() + 0.5)
    ok = pooled['quality'] == 'ok'
    ax.scatter(pooled.loc[ok, 'year'], pooled.loc[ok, column], s=36,
               color=HUE, zorder=3)
    ax.scatter(pooled.loc[~ok, 'year'], pooled.loc[~ok, column], s=36,
               facecolor='white', edgecolor=HUE, linewidth=1.5, zorder=3)
    style_axis(ax, ylabel)
    ax.set_ylim(bottom=0)
    ax.set_title(title, loc='left', fontsize=11, color=INK)


def figure_all_basins(table, out):
    pooled = table[table['basin_nr'] == ind.ALL_BASINS].sort_values('year')
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    plot_span(axes[0, 0], pooled)
    for ax, (column, title, ylabel) in zip(axes.flat[1:], PANELS):
        plot_series(ax, pooled, column, title, ylabel)
    fig.suptitle('Cyanobacterial bloom indicator, all basins '
                 f'({pooled["year"].min()}–{pooled["year"].max()})',
                 fontsize=13, color=INK, x=0.01, ha='left')
    fig.text(0.01, -0.02,
             'Hollow markers / hatched bars: fewer than 60 % of season days '
             'observed. Threshold 5 % of cloud-free area, 7-day mean, '
             '3-day persistence.', fontsize=8, color=INK_MUTED)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)


def quality_bars(ax, pooled, heights, bottom=0.0):
    """Bars per year; hatched when the season is flagged low_coverage."""
    ok = (pooled['quality'] == 'ok').to_numpy()
    values = np.asarray(heights, dtype=float)
    years = pooled['year'].to_numpy()
    for flag, hatch in ((ok, None), (~ok, '///')):
        sel = flag & ~np.isnan(values)
        ax.bar(years[sel], values[sel], bottom=bottom, width=0.7,
               color=HUE if hatch is None else 'white',
               edgecolor=HUE, hatch=hatch, linewidth=1)
    ax.set_xlim(years.min() - 0.7, years.max() + 0.7)


def plot_start_bars(ax, pooled):
    floor = mdates.date2num(pd.Timestamp(DUMMY_YEAR, *ind.SEASON_START))
    quality_bars(ax, pooled, day_of_season(pooled['start']) - floor,
                 bottom=floor)
    ax.yaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%-d %b'))
    ax.set_ylim(floor, mdates.date2num(pd.Timestamp(DUMMY_YEAR, 9, 1)))
    style_axis(ax, '')
    ax.set_title('Startdatum', loc='left', fontsize=11, color=INK)


def figure_indicator_bars(table, out):
    pooled = table[table['basin_nr'] == ind.ALL_BASINS].sort_values('year')
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), constrained_layout=True)
    plot_start_bars(axes[0], pooled)
    for ax, heights, title, ylabel in (
            (axes[1], pooled['bloom_days'], 'Blomningsdagar', 'dagar'),
            (axes[2], pooled['mean_fca'] * pooled['valid_km2'] / 1000,
             'Medelutbredning', '1000 km²')):
        quality_bars(ax, pooled, heights)
        style_axis(ax, ylabel)
        ax.set_ylim(bottom=0)
        ax.set_title(title, loc='left', fontsize=11, color=INK)
    fig.suptitle('Cyanoblomning – indikatorer, hela området '
                 f'({pooled["year"].min()}–{pooled["year"].max()})',
                 fontsize=13, color=INK, x=0.01, ha='left')
    fig.text(0.01, -0.03,
             'Skrafferade staplar: färre än 60 % av säsongens dagar '
             'observerade.', fontsize=8, color=INK_MUTED)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)


def heatmap(ax, grid, title, fmt):
    ax.grid(False)
    im = ax.imshow(grid.values, aspect='auto', cmap='Blues', vmin=0)
    ax.set_xticks(range(grid.shape[1]))
    ax.set_xticklabels(grid.columns, rotation=90, fontsize=7, color=INK)
    ax.set_yticks(range(grid.shape[0]))
    ax.set_yticklabels(grid.index, fontsize=8, color=INK)
    ax.set_title(title, loc='left', fontsize=10, color=INK)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, format=fmt)


def figure_per_basin(table, out):
    basins = table[table['basin_nr'].isin([str(b) for b in PLOTTED_BASINS])]
    basins = basins.assign(basin_nr=basins['basin_nr'].astype(int))
    order = [BASIN_NAMES[b] for b in PLOTTED_BASINS]
    fig, axes = plt.subplots(1, 3, figsize=(17, 7), constrained_layout=True)
    for ax, (column, title, _) in zip(axes, PANELS):
        grid = basins.pivot(index='basin_name', columns='year',
                            values=column).reindex(order)
        heatmap(ax, grid, title, '%.2f' if column == 'mean_fca' else '%d')
    fig.suptitle('Cyanobacterial bloom indicator per basin', fontsize=13,
                 color=INK, x=0.01, ha='left')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)


def main():
    table = read_indicator(data_dir('stats'))
    table = table.assign(basin_nr=table['basin_nr'].astype(str))
    figures = data_dir('figures')
    figure_all_basins(table, figures / 'indicator_all_basins.png')
    figure_per_basin(table, figures / 'indicator_per_basin.png')
    figure_indicator_bars(table, figures / 'indicator_bars.png')
    print('wrote', figures / 'indicator_all_basins.png')
    print('wrote', figures / 'indicator_per_basin.png')
    print('wrote', figures / 'indicator_bars.png')


if __name__ == '__main__':
    main()
