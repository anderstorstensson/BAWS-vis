#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Season (year) selection for the pipeline scripts.

Two environment variables steer which seasons the scripts work on. Both
are optional; without them every script behaves as before and processes
whatever years are present in the data directory.

    BAWS_YEARS      Seasons to (re)process in the per-season stages
                    (scripts 1-7, 9-12 and 14). Accepts single years,
                    ranges and comma/space separated lists:
                    "2025", "2002-2010", "2019,2021", "2002-2005 2024".
                    The cross-season stages (8, 13, 15, 16) ignore this
                    on purpose: they build climatologies and "all years"
                    tables and must always see every season on disk.

    BAWS_PLOT_YEAR  The season drawn by the per-season figures (0_2 and
                    0_4). Defaults to the most recent season available.

run_pipeline.py sets both from its --years / --plot-year options.
"""
import os
import re
import sys
from datetime import date

YEARS_ENV = 'BAWS_YEARS'
PLOT_YEAR_ENV = 'BAWS_PLOT_YEAR'

# First season in the BAWS archive; used to reject typos like 202 or 20255.
ARCHIVE_START_YEAR = 2002

_YEAR_IN_NAME = re.compile(r'(20\d{2})')


def _parse_year(token):
    try:
        year = int(token)
    except ValueError:
        raise ValueError(f'Not a year: {token!r}') from None
    last_valid = date.today().year
    if not ARCHIVE_START_YEAR <= year <= last_valid:
        raise ValueError(
            f'Year {year} is outside the archive '
            f'({ARCHIVE_START_YEAR}-{last_valid})')
    return year


def parse_years(text):
    """Parse "2025", "2002-2010", "2019,2021" or "2002-2005 2024" to a frozenset.

    Years must lie within ARCHIVE_START_YEAR..today. Returns None for an
    empty/blank string (meaning "no restriction"). Raises ValueError.
    """
    if text is None or not text.strip():
        return None
    years = set()
    for token in re.split(r'[,\s]+', text.strip()):
        if '-' in token:
            first, last = (_parse_year(part) for part in token.split('-', 1))
            if last < first:
                raise ValueError(f'Bad year range {token!r}: end before start')
            years.update(range(first, last + 1))
        else:
            years.add(_parse_year(token))
    return frozenset(years)


def format_years(years):
    """Compact "2002-2005, 2024" representation of an iterable of years."""
    years = sorted(set(years))
    if not years:
        return ''
    runs = []
    start = prev = years[0]
    for year in years[1:]:
        if year != prev + 1:
            runs.append((start, prev))
            start = year
        prev = year
    runs.append((start, prev))
    return ', '.join(f'{a}-{b}' if a != b else f'{a}' for a, b in runs)


def selected_years():
    """Years requested through BAWS_YEARS, or None if unrestricted."""
    try:
        return parse_years(os.environ.get(YEARS_ENV))
    except ValueError as error:
        raise SystemExit(f'{YEARS_ENV}={os.environ[YEARS_ENV]!r}: {error}')


def year_of(file_name):
    """First 20xx year found in a file name, or None."""
    match = _YEAR_IN_NAME.search(os.path.basename(os.fspath(file_name)))
    return int(match.group(1)) if match else None


def is_selected(file_name, selection=None):
    """True if the file's year is in the selection (or nothing is selected).

    Files without a year in their name are never filtered out.
    """
    selection = selected_years() if selection is None else selection
    if selection is None:
        return True
    year = year_of(file_name)
    return year is None or year in selection


def only_selected(paths):
    """Filter an iterable of file paths to the selected seasons."""
    selection = selected_years()
    if selection is None:
        yield from paths
        return
    for path in paths:
        if is_selected(path, selection):
            yield path


def restrict_years(years):
    """Intersect a list of available years with the selection, sorted.

    Warns on stderr when the selection matches none of the available
    years, so a typo does not pass as a silent, successful no-op.
    """
    selection = selected_years()
    if selection is None:
        return sorted(years)
    chosen = sorted(set(years) & selection)
    if not chosen:
        print(f'warning: {YEARS_ENV}={format_years(selection)} matches none '
              f'of the seasons on disk ({format_years(years) or "none"}); '
              f'nothing to do', file=sys.stderr)
    return chosen


def plot_year(available):
    """Season to draw: BAWS_PLOT_YEAR if set, else the latest available."""
    available = sorted(available)
    if not available:
        raise SystemExit('No seasons available to plot')
    requested = os.environ.get(PLOT_YEAR_ENV, '').strip()
    if not requested:
        return available[-1]
    try:
        year = int(requested)
    except ValueError:
        raise SystemExit(f'{PLOT_YEAR_ENV}={requested!r} is not a year') from None
    if year not in available:
        raise SystemExit(
            f'{PLOT_YEAR_ENV}={year} is not available; '
            f'seasons on disk: {format_years(available)}')
    return year
