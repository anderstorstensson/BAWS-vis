# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-31 11:39

@author: a002028
"""
from bawsvis.session import Session
from bawsvis.data_handler import (
    get_interpolated_data_table,
    get_interpolated_statistics_table,
    get_statistics
)
from bawsvis.interpolate import get_interpolated_df
from bawsvis.readers.dictionary import pandas_reader, json_reader
from bawsvis.utils import recursive_dict_update
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import dates

# sns.set(style="darkgrid")
sns.set(style="whitegrid")


def plot_one_season(stat_df):
    from bawsvis.paths import data_dir

    file = data_dir('stats') / 'stats_2023_2.json'
    data = pd.read_json(file)
    data.rename(columns={c: pd.Timestamp(str(c)) for c in data.columns},
                inplace=True)
    try:
        data = data.drop(['{}-day bloom'.format(i+1) for i in range(7)])
    except:
        pass
    df = get_interpolated_data_table(data)

    # 359429 km2 från öresund/bälten upp tom. norra kvarken.
    # Kattegatt exkluderat
    # Kvot * 100 = Procent
    df.loc['cloud_cover_percent', :] = (df.loc['cloud_area', :] / 359429.) * 100
    for key in ('daily_bloom_area', 'weekly_bloom_area', 'surface_area'):
        df.loc[key, :] = df.loc[key, :] / 1000.

    for key in ('weekly_mean', 'weekly_std_u', 'weekly_std_l'):
        stat_df.loc[key, :] = stat_df.loc[key, :] / 1000.

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))
    ax3 = ax1.twinx()

    cc = sns.lineplot(data=df.loc['cloud_cover_percent', :] * -1,
                     label='Molntäcke',
                     color='#9B9B9B',
                     lw=.75,
                     ax=ax1)

    wb = ax1.fill_between(df.columns,
                         df.loc['weekly_bloom_area', :],
                         y2=df.loc['daily_bloom_area', :],
                         label='Veckoblomning',
                         lw=.1, alpha=.6,
                         color='#9B9B9B')

    db = ax1.fill_between(df.columns,
                         df.loc['daily_bloom_area', :],
                         y2=df.loc['surface_area', :],
                         label='Blomning',
                         lw=.1, alpha=.3,
                         color='#49C1BB')

    sa = ax1.fill_between(df.columns,
                         df.loc['surface_area', :],
                         label='Ytansamlingar',
                         lw=.1, alpha=.3,
                         color='#046666')

    cc = ax1.plot(df.columns, df.loc['cloud_cover_percent', :] * .01, '-',
                  label='Molntäcke',
                  color='#9B9B9B',
                  lw=.75)

    sns.lineplot(data=df.loc['cloud_cover_percent', :],
                #  label='Cloud cover',
                 color='#9B9B9B',
                 lw=0.75,
                 ax=ax3)

    sns.lineplot(data=stat_df.loc['weekly_mean', :],
                 label='Medel - Veckodata 2002-2023',
                 color='#046666',
                 ax=ax2)

    ax2.fill_between(stat_df.columns,
                     stat_df.loc['weekly_std_u', :],
                     y2=stat_df.loc['weekly_std_l', :],
                     label='SD - Veckodata 2002-2023',
                     lw=.1, alpha=.6,
                     color='#9B9B9B')

    ax2.xaxis.set_major_formatter(dates.DateFormatter("%d-%b"))
    ax2.set_xlim(stat_df.columns[0], stat_df.columns[-1])
    # ax2.set_ylim(0, 200000)
    ax2.set_ylim(0, 200)
    ax1.set_xlim(stat_df.columns[0], stat_df.columns[-1])
    # ax1.set_ylim(0, 200000)
    ax1.set_ylim(0, 200)
    ax3.set_ylim(0, 100)
    ax3.locator_params(axis='y', nbins=4)
    ax3.grid(False)

    handles, labels = ax1.get_legend_handles_labels()
    new_label_order = ['Ytansamlingar', 'Blomning', 'Veckoblomning', 'Molntäcke']
    new_handle_order = []
    for l in new_label_order:
        new_handle_order.append(handles[labels.index(l)])

    ax1.legend(new_handle_order, new_label_order, loc='upper left')

    ax2.legend(loc='upper left')

    # ax1.set_ylabel('Yta (km$^{2}$)')
    # ax2.set_ylabel('Yta (km$^{2}$)')
    ax1.set_ylabel('Yta (1000 km$^{2}$)')
    ax2.set_ylabel('Yta (1000 km$^{2}$)')
    ax3.set_ylabel('Molntäcke (%)')

    # ax1.ticklabel_format(axis='y', style='sci', scilimits=(1, 2), useMathText=True)
    # ax2.ticklabel_format(axis='y', style='sci', scilimits=(1, 2), useMathText=True)
    # ax1.set_title('Cyanobacterial bloom 2021')

    plt.tight_layout()
    plt.show()
    # plt.savefig(r'C:\Kodning\BAWS-vis\bawsvis\export\diagram_2023_new_colours.png', dpi=600)


if __name__ == "__main__":

    """
              WARNING!!!
    
    Make sure that you do the following before extracting area from cyano_daymaps:
    - cyano_daymap.shp from QGIS-BAWS = master-data. However, we can not use these 
      files to extract statistics due to overlapping geometries. 
    - Therefore we need to create new cyano_daymap.shp files from cyano_daymap.tiff
    - Place these data in some temporary folder, do not overwrite the master-data.
    """

    from bawsvis.paths import data_dir

    file_path = str(data_dir('stats') / 'stats_all.json')
    stat_data = get_statistics(file_path)
    df = pd.DataFrame(stat_data)
    idx = df['summer_dates'].values
    df.drop('summer_dates', axis=1, inplace=True)
    df.index = idx
    df = df.transpose()

    df = get_interpolated_statistics_table(df)

    plot_one_season(df)

    # fig, ax = plt.subplots(figsize=(10, 5))
    #
    # ax.fill_between(df.columns,
    #                 df.loc['weekly_std_u', :],
    #                 y2=df.loc['weekly_std_l', :],
    #                 label='Weekly bloom',
    #                 lw=.1, alpha=.2,
    #                 color='grey')

    # ax.fill_between(df.columns,
    #                 df.loc['daily_std_u', :],
    #                 y2=df.loc['daily_std_l', :],
    #                 label='Daily bloom',
    #                 lw=.1, alpha=.5,
    #                 color='yellow')

    # ax.legend(loc='upper left')
    # plt.ylabel('km$^{2}$')
    # plt.tight_layout()
