#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-11-08 12:22

@author: johannes
"""
import numpy as np
import pandas as pd
from scipy import interpolate
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import dates

sns.set(style="ticks", palette="pastel")
# sns.set(style="darkgrid")
# sns.set(style="whitegrid")


def change_width(ax, new_value):
    for patch in ax.patches:
        current_width = patch.get_width()
        diff = current_width - new_value
        patch.set_width(new_value)
        patch.set_x(patch.get_x() + diff * .5)


if __name__ == "__main__":
    from bawsvis.paths import data_dir

    # Combine the pipeline's annual stats (script 8) with the FCA means
    # (script 13); the old committed workbook had both in one sheet.
    annual_files = sorted(data_dir('stats').glob('annual_stats_norm_*.xlsx'))
    if not annual_files:
        raise SystemExit('No annual_stats_norm_*.xlsx found; run script 8 first')
    df = pd.read_excel(annual_files[-1], sheet_name='data')
    fca = pd.read_excel(data_dir('stats') / 'fca_means.xlsx', sheet_name='data')
    df = df.merge(fca, on='year')
    df_monthly = pd.DataFrame({
        'year': df['year'].to_list() * 3,
        'fca': df['june'].to_list() + df['july'].to_list() + df['august'].to_list(),
        'month': ['Juni'] * df['year'].__len__() + ['Juli'] * df['year'].__len__() + ['Augusti'] * df['year'].__len__()
    })
    print(df_monthly.head())
    df_monthly['fca'] = df_monthly['fca'] * 100
    df['median_period'] = df['median_period'] * 100

    df['total_area'] = df['total_area'] / 1000.

    label_mapper = {
        'total_area': 'Total area (1000 km$^{2}$)',
        'median_period': 'FCA (%)',
        'monthly': 'FCA (%)',
        # 'june': 'FCA - Juni',
        # 'july': 'FCA - Juli',
        # 'august': 'FCA - Augusti',
    }
    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    for ax, data_key, note in zip(axes, ('total_area', 'median_period', 'monthly'),
                                  ('a', 'b', 'c')):
        if data_key == 'monthly':
            g = sns.barplot(x=df_monthly['year'], y=df_monthly['fca'],
                        # color='#49C1BB',
                        palette='blend:#49C1BB,#046666',
                        hue=df_monthly['month'],
                        # hue=palette,
                        ax=ax)
            ax.legend(title='', frameon=False, loc='upper left')
            g.grid(True, which='both', axis='y', linewidth=0.5)
        else:
            g = sns.barplot(x=df['year'], y=df[data_key],
                        color='#9B9B9B',
                        ax=ax)
            change_width(ax, .5)
            g.grid(True, which='major', axis='y', linewidth=0.5)
        sns.despine(offset=5, ax=ax, fig=fig)
        # if data_key == 'total_area':
        #     ax.ticklabel_format(axis='y', style='sci', scilimits=(1, 2), useMathText=True)
        ax.set_ylabel(label_mapper.get(data_key))
        ax.set_xlabel('')

        y_text_pos = ax.get_ylim()[1] - (ax.get_ylim()[1] - ax.get_ylim()[0]) / 9.
        ax.text(ax.get_xlim()[-1], y_text_pos, note)

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        data_dir('figures')
        / f"TA_FCA_{df['year'].iloc[0]}-{df['year'].iloc[-1]}.png",
        dpi=600)
