#!/usr/bin/env python3
"""
Created on 2021-10-15 14:43

@author: johannes
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib import rc

# sns.set_theme(style="ticks")
font = {
    'family': 'sans-serif',
    'sans-serif': 'Helvetica',
    # 'weight': 'bold'
}
#
rc('font', **font)
sns.set_theme()
sns.set(style="whitegrid")


from bawsvis.basins import BASIN_NAMES, PLOTTED_BASINS, basin_key

# Season year being plotted; set in __main__ from the data present.
YEAR = None

mapping_basin = {basin_key(n): BASIN_NAMES[n] for n in PLOTTED_BASINS}

def change_height(ax, new_value):
    for patch in ax.patches:
        current_height = patch.get_height()
        diff = current_height - new_value
        patch.set_height(new_value)
        patch.set_y(patch.get_y() + diff * .5)


def get_nr_of_bloom_days(df, area):
    inv_map = {v: k for k, v in mapping_basin.items()}
    boolean = df['BASIN'] == inv_map.get(area)
    # row_boolean = df.loc[boolean, :].notna()
    row_boolean = df.loc[boolean, :].isin(['2', '3'])
    row_boolean = row_boolean & (df.columns != 'BASIN')
    return row_boolean.values.sum()


def get_list_of_dataframes(df, only_red=False, only_yellow=False, only_cloud=False, only_bloom=False):
    list_of_frames = []
    date_check = {b: None for b in mapping_basin}

    data_exsists = True
    while data_exsists:

        data_exsists = False
        data = {k: [] for k in ('ts_start', 'ts_end', 'ts_mid', 'days', 'area')}

        for basin, name in mapping_basin.items():
            basin_row = df['BASIN'] == basin
            start = date_check.get(basin)
            # print(basin, name, start)
            if start:
                start_index = start
            else:
                start_index = 0

            ts_start = np.nan
            ts_end = np.nan
            for d in df.columns.to_list()[start_index:]:
                if d == 'BASIN':
                    continue
                # print(d, start_index)
                v = df.loc[basin_row, d].values[0]
                if only_red:
                    if v == '2':
                        v = np.nan

                if only_cloud:
                    if v in ('2', '3'):
                        v = np.nan
                else:
                    if v == '1':
                        v = np.nan
                
                if only_yellow:
                    if v == '3':
                        v = np.nan

                if only_bloom:
                    if v == '1':
                        v = np.nan

                if not pd.isnull(v):
                    # print(name)
                    data_exsists = True
                    if pd.isnull(ts_start):
                        ts_start = pd.Timestamp(d)
                        ts_end = ts_start + pd.Timedelta('1 day')
                    else:
                        ts_end = pd.Timestamp(d) + pd.Timedelta('1 day')
                elif not pd.isnull(ts_start) and not pd.isnull(ts_end):
                    date_check[basin] = df.columns.to_list().index(d) + 1
                    break

                if not pd.isnull(ts_end):
                    if ts_end > pd.Timestamp(df.columns[-1]):
                        date_check[basin] = len(df.columns) + 1

            if pd.isnull(ts_start):
                # Dummy dates
                ts_start = pd.Timestamp(f'{YEAR}1231')
                ts_end = pd.Timestamp(f'{YEAR}12310101')

            delta = ts_end - ts_start

            data['ts_start'].append(mdates.date2num(ts_start))
            data['ts_end'].append(mdates.date2num(ts_end))
            data['ts_mid'].append(mdates.date2num(ts_start + delta / 2))
            data['days'].append(delta.days)
            data['area'].append(name)

        list_of_frames.append(pd.DataFrame(data))

    return list_of_frames


if __name__ == "__main__":
    import re
    from bawsvis.paths import data_dir
    from bawsvis.selection import plot_year

    # Combined workbook from script 16: area_season_bloom_all_<first>-<last>.xlsx
    candidates = sorted(data_dir('stats').glob('area_season_bloom_all_*.xlsx'))
    if not candidates:
        raise SystemExit('No area_season_bloom_all_*.xlsx found; run script 16 first')
    season_bloom_file = candidates[-1]
    span = re.search(r'(\d{4}-\d{4})', season_bloom_file.stem).group(1)
    # One sheet per season in the workbook; draw BAWS_PLOT_YEAR or the latest.
    sheets = pd.ExcelFile(season_bloom_file).sheet_names
    YEAR = plot_year(int(name) for name in sheets if name.isdigit())

    stats_df = pd.read_excel(
        season_bloom_file,
        sheet_name=f'stats_{span}',
        dtype=str,
    )

    stats_df = stats_df.loc[stats_df['BASIN'].isin(list(mapping_basin)), :]
    for key in stats_df:
        stats_df[key] = stats_df[key].str.split('.', expand=True)[0]
        if key == 'BASIN':
            continue
        elif key.startswith('std'):
            stats_df[key] = stats_df[key].apply(pd.Timedelta)
        else:
            stats_df[key] = stats_df[key].apply(pd.Timestamp)

    stats_df['std_dev_start_lo'] = stats_df['mean_start'] - stats_df['std_dev_start']
    stats_df['std_dev_start_hi'] = stats_df['mean_start'] + stats_df['std_dev_start']
    stats_df['std_dev_end_lo'] = stats_df['mean_end'] - stats_df['std_dev_end']
    stats_df['std_dev_end_hi'] = stats_df['mean_end'] + stats_df['std_dev_end']

    date_keys = ['mean_start', 'mean_end', 'median_start', 'median_end',
                 'std_dev_start_lo', 'std_dev_start_hi', 'std_dev_end_lo', 'std_dev_end_hi']
    stats_df[date_keys] = stats_df[date_keys].apply(mdates.date2num)

    df = pd.read_excel(
        season_bloom_file,
        sheet_name=f'{YEAR}',
        dtype=str,
    )
    df.columns = df.columns.astype(str)
    df = df.loc[df['BASIN'].isin(list(mapping_basin)), :]

    data_bloom = get_list_of_dataframes(df, only_yellow=True)
    data_red = get_list_of_dataframes(df, only_red=True)
    data_cloud = get_list_of_dataframes(df, only_cloud=True)
    data_total_bloom_line = get_list_of_dataframes(df, only_bloom=True)

    major_locator_ticks = []
    for m in ('06', '07', '08'):
        for d in ('01', '10', '20'):
            major_locator_ticks.append(mdates.datestr2num(f'{YEAR}{m}{d}'))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.use_sticky_edges = True
    fig.autofmt_xdate()
    ax.set_xlim([mdates.datestr2num(df.columns[1]), mdates.datestr2num(df.columns[-1]+'2359')])
    # ax.set_xlim([stats_df['std_dev_start_lo'].min()+0.06, stats_df['std_dev_end_hi'].max()])

    for df_set in data_cloud:
        sns.barplot(
            y=df_set['area'],
            x=df_set['ts_end'] - df_set['ts_start'],
            left=df_set['ts_start'],
            ec='#9B9B9B',
            linewidth=0,
            color='#9B9B9B',
            alpha=1,
            ax=ax
        )

    for df_set in data_red:
        sns.barplot(
            y=df_set['area'],
            x=df_set['ts_end'] - df_set['ts_start'],
            left=df_set['ts_start'],
            ec='#046666',
            linewidth=0,
            color='#046666',
            ax=ax,
            zorder=1
        )

    for df_set in data_bloom:
        sns.barplot(
            y=df_set['area'],
            x=df_set['ts_end'] - df_set['ts_start'],
            left=df_set['ts_start'],
            ec='k',
            linewidth=0,
            color='#49C1BB',
            # facecolor=(0, 0, 0, 0.7),
            ax=ax,
        )

    bar_plots = []
    for df_set in data_total_bloom_line:
        p = sns.barplot(
            y=df_set['area'],
            x=df_set['ts_end'] - df_set['ts_start'],
            left=df_set['ts_start'],
            ec='k',
            linewidth=1,
            color='#49C1BB',
            # facecolor=(0, 0, 0, 0.7),
            facecolor='#49C1BB00',
            ax=ax,
        )
        bar_plots.append(p)

    change_height(ax, .35)

    inv_map = {v: k for k, v in mapping_basin.items()}
    basin_y_pos = {}
    for i, (p, df_set) in enumerate(zip(bar_plots, data_total_bloom_line)):
        for (index, row), patch in zip(df_set.iterrows(), p.patches):
            if row.days > 0:
                _y = patch.get_y() - patch.get_height() / 6
                p.text(row.ts_mid, _y, str(row.days), color='black', ha="center", size=8)
            if i == len(data_total_bloom_line) - 1:
                nr_blooms = get_nr_of_bloom_days(df, row.area)
                _x = ax.get_xlim()[1] + 3
                _y = patch.get_y() + patch.get_height() / 2
                p.text(_x, _y, str(nr_blooms), color='black', va="center", size=10)
            basin_y_pos.setdefault(inv_map.get(row.area), patch.get_y())

    for basin, y_pos in basin_y_pos.items():
        basin_bool = stats_df['BASIN'] == basin
        for tw in ('median_start', 'median_end'):
            p.plot(
                [stats_df.loc[basin_bool, tw]]*2,
                [y_pos-.05, y_pos+.40],
                # [y_pos, y_pos+.525],
                '-',
                lw=1,
                color='#C24A50'
            )
        for tw in ('mean_start', 'mean_end'):
            p.plot(
                [stats_df.loc[basin_bool, tw]]*2,
                [y_pos+.45, y_pos+.5],
                # [y_pos, y_pos+.525],
                '-k',
                lw=1
            )
        for std_pair in (['std_dev_start_lo', 'std_dev_start_hi'], ['std_dev_end_lo', 'std_dev_end_hi']):
            p.plot(
                stats_df.loc[basin_bool, std_pair].values[0],
                [y_pos + .5, y_pos + .5],
                # [y_pos + .525, y_pos + .525],
                '-k',
                lw=1
            )

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=[10, 20, 30], interval=1))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=[5, 15, 25], interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    ax.tick_params(axis='x', which='minor', labelsize=12)
    ax.tick_params(axis='x', which='major', labelsize=9)
    ax.set_ylabel('')
    ax.set_xlabel('')
    ax.xaxis.set_ticks_position("top")
    ax.grid(False)
    sns.despine(offset=5, ax=ax, bottom=True, left=True)

    # Pin the minor ticks to fixed positions so the labels can be replaced
    # (set_ticklabels without a FixedLocator triggers a UserWarning).
    minor_ticks = ax.get_xticks(minor=True)
    ax.set_xticks(minor_ticks, minor=True)
    ax.set_xticklabels(
        ['', 'Juni', '', '', 'Juli', '', '', 'Augusti', '', '', 'September', ''][:len(minor_ticks)],
        minor=True,
    )

    for i, l in enumerate(ax.get_xticklabels(minor=True)):
        if i in (1, 4, 7, 10):
            l.set_y(1.05)

    plt.tight_layout()
    # plt.show()
    plt.savefig(
        data_dir('figures') / f'basin_timeline_{YEAR}.png',
        dpi=600)

