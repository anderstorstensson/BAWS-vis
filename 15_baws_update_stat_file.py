# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-01 15:50

@author: a002028

"""
from bawsvis.readers.dictionary import json_reader
from bawsvis.writers.dictionary import json_writer


if __name__ == "__main__":
    """
    Combine the per-season daily statistics (stats_<year>_2.json, one
    key per date) into stats_all.json, which the season diagram (0_2)
    uses for its climatology.

    The file is rebuilt from scratch on every run, over every season on
    disk regardless of BAWS_YEARS, so that a reprocessed season replaces
    its old values. (The previous setdefault-based merge kept whatever
    was already in stats_all.json and silently ignored new numbers.)
    """
    from bawsvis.paths import data_dir
    from bawsvis.utils import discover_years

    stats_dir = data_dir('stats')
    years = discover_years(stats_dir, pattern='stats_', endswith='_2.json')
    if not years:
        raise SystemExit('No stats_<year>_2.json found; run scripts 9-12 first')

    combined = {}
    for year in years:
        combined.update(json_reader(str(stats_dir / f'stats_{year}_2.json')))

    json_writer(str(stats_dir / 'stats_all.json'), combined)
    print(f'stats_all.json: {len(combined)} dates from {years[0]}-{years[-1]}')