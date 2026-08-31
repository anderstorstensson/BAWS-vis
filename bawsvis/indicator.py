# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Threshold-based cyanobacterial bloom indicator.

Input is the long table written by script 17: one row per date and basin
with valid_km2, cloud_km2, subsurface_km2 and surface_km2. From it:

  fca          bloom area / cloud-free observed area in the basin, per day.
               Undefined when less than MIN_OBSERVED_FRACTION of the basin
               was observed.
  smoothed     7-day centred running mean of fca over the days with data.
  start / end  first / last day where the smoothed fca is >= THRESHOLD for
               at least PERSIST consecutive days, inside the fixed season
               window (1 Jun - 30 Sep).
  span_days    end - start + 1
  bloom_days   days in the window with smoothed fca >= THRESHOLD
  mean_fca     mean of daily fca over the window, unobserved days excluded
  peak_smoothed_fca
               seasonal maximum of the smoothed fca; times valid_km2 (the
               basin sea area) it is the bloom's maximum extent in km2
  surface_days days with smoothed surface fca >= SURFACE_THRESHOLD
  quality      'ok' or 'low_coverage' (fewer than MIN_SEASON_COVERAGE of
               the window days usable)

"All basins" is the same computation on the basin areas summed per day.
"""
import numpy as np
import pandas as pd

THRESHOLD = 0.05
SURFACE_THRESHOLD = 0.01
PERSIST = 3
WINDOW = 7
MIN_WINDOW_OBS = 2
MIN_OBSERVED_FRACTION = 0.2
MIN_SEASON_COVERAGE = 0.6
SEASON_START = (6, 1)
SEASON_END = (9, 30)
ALL_BASINS = 'All'

METRIC_COLUMNS = ('start', 'end', 'span_days', 'bloom_days', 'mean_fca',
                  'mean_bloom_km2', 'peak_fca', 'peak_smoothed_fca',
                  'peak_date', 'surface_days', 'observed_days',
                  'observed_fraction', 'valid_km2', 'quality')


def season_index(year):
    return pd.date_range(pd.Timestamp(year, *SEASON_START),
                         pd.Timestamp(year, *SEASON_END), freq='D')


def daily_fca(df):
    """Add observed_km2, bloom_km2, fca and surface_fca columns (new frame)."""
    observed = df['valid_km2'] - df['cloud_km2']
    bloom = df['subsurface_km2'] + df['surface_km2']
    usable = observed >= MIN_OBSERVED_FRACTION * df['valid_km2']
    safe_observed = observed.where(usable)
    return df.assign(
        observed_km2=observed,
        bloom_km2=bloom,
        fca=(bloom / safe_observed).where(usable),
        surface_fca=(df['surface_km2'] / safe_observed).where(usable),
    )


def pool_basins(df):
    """Sum the areas over basins per date; basin_nr becomes ALL_BASINS."""
    area_cols = ['valid_km2', 'cloud_km2', 'subsurface_km2', 'surface_km2']
    pooled = df.groupby('date', as_index=False)[area_cols].sum()
    return pooled.assign(basin_nr=ALL_BASINS)[['date', 'basin_nr', *area_cols]]


def smooth(series, window=WINDOW, min_obs=MIN_WINDOW_OBS):
    return series.rolling(window, center=True, min_periods=min_obs).mean()


def persistent_run_bounds(above, persist=PERSIST):
    """(first index, last index) of runs of True at least `persist` long.

    Positions are integer positions; (None, None) if no such run exists.
    """
    values = np.asarray(above, dtype=bool)
    if not values.any():
        return None, None
    padded = np.concatenate(([False], values, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    starts, ends = edges[::2], edges[1::2] - 1
    long_enough = (ends - starts + 1) >= persist
    if not long_enough.any():
        return None, None
    return int(starts[long_enough][0]), int(ends[long_enough][-1])


def _season_frame(daily, year):
    """Daily frame reindexed to the full season window (missing days NaN)."""
    return daily.set_index('date').reindex(season_index(year))


def season_metrics(daily, year):
    """Indicator metrics for one basin and year. `daily` from daily_fca()."""
    frame = _season_frame(daily, year)
    fca = frame['fca']
    smoothed = smooth(fca)
    above = smoothed >= THRESHOLD
    first, last = persistent_run_bounds(above)
    n_days = len(frame)
    observed_days = int(fca.notna().sum())
    observed_fraction = observed_days / n_days
    has_peak = fca.notna().any()
    return {
        'start': frame.index[first] if first is not None else pd.NaT,
        'end': frame.index[last] if last is not None else pd.NaT,
        'span_days': last - first + 1 if first is not None else 0,
        'bloom_days': int(above.sum()),
        'mean_fca': fca.mean() if has_peak else np.nan,
        'mean_bloom_km2': frame['bloom_km2'].where(fca.notna()).mean()
        if has_peak else np.nan,
        'peak_fca': fca.max() if has_peak else np.nan,
        'peak_smoothed_fca': smoothed.max() if has_peak else np.nan,
        'peak_date': fca.idxmax() if has_peak else pd.NaT,
        'surface_days': int((smooth(frame['surface_fca'])
                             >= SURFACE_THRESHOLD).sum()),
        'observed_days': observed_days,
        'observed_fraction': observed_fraction,
        'valid_km2': frame['valid_km2'].max(),
        'quality': 'ok' if observed_fraction >= MIN_SEASON_COVERAGE
        else 'low_coverage',
    }


def indicator_table(df):
    """One row per year and basin (plus ALL_BASINS) with the metrics."""
    with_all = pd.concat([df, pool_basins(df)], ignore_index=True)
    daily = daily_fca(with_all)
    rows = [
        {'year': year, 'basin_nr': basin,
         **season_metrics(group, year=year)}
        for (year, basin), group in daily.groupby(
            [daily['date'].dt.year, 'basin_nr'], sort=False)
    ]
    return pd.DataFrame(rows)[['year', 'basin_nr', *METRIC_COLUMNS]]
