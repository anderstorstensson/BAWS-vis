#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-11-17 15:14

@author: johannes
"""
from bawsvis.session import Session
from bawsvis.readers.dictionary import json_reader
from bawsvis.writers.dictionary import json_writer
import os
import pandas as pd
import numpy as np
import copy

MONTH_MAP = {
    6: 'june',
    7: 'july',
    8: 'august',
}


if __name__ == "__main__":
    from bawsvis.paths import data_dir

    s = Session()
    # Stats json files live in the stats directory.
    s.setting.set_export_directory(path=data_dir('stats'))

    for year in range(2002, 2023):
        stat = json_reader(os.path.join(s.setting.export_directory, f'stats_{year}_2.json'))

        # dummy_year = 2022
        start = pd.Timestamp(f'{year}-06-20')  # median start 2002-2022
        end = pd.Timestamp(f'{year}-09-01')  # median end 2002-2022

        annual_data = {}
        season = {
            'median_period': [],
            'june': [],
            'july': [],
            'august': [],
        }
        for date, item in stat.items():
            ts = pd.Timestamp(date)
            if ts.year not in annual_data:
                annual_data[ts.year] = copy.deepcopy(season)

            if start <= ts.replace(year=year) <= end:
                annual_data[ts.year]['median_period'].append(item.get('fca'))

            if ts.month in MONTH_MAP:
                annual_data[ts.year][MONTH_MAP.get(ts.month)].append(item.get('fca'))

        out_dict = {k: [] for k in ('year', 'median_period', 'june', 'july', 'august')}
        for key in annual_data:
            for period in season:
                value = np.nanmean(annual_data[key][period])
                annual_data[key][period] = value
                out_dict[period].append(round(value, 5))
            out_dict['year'].append(key)

    out_file_path = os.path.join(
        s.setting.export_directory, f'fca_means.json')
    json_writer(out_file_path, annual_data)

    pd.DataFrame(out_dict).to_excel(
        out_file_path.replace('.json', '.xlsx'),
        sheet_name='data',
        index=False
    )
