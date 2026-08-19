# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-09-01 15:50

@author: a002028

"""
from bawsvis.session import Session
from bawsvis.readers.dictionary import json_reader
from bawsvis.writers.dictionary import json_writer
from bawsvis.utils import recursive_dict_update


if __name__ == "__main__":
    """
    Make sure that you do the following before extracting area from cyano_daymaps:
    - cyano_daymap.shp from QGIS-BAWS the master-data. However, we can not use these 
      files to extract statistics due to ovrlapping geometries. 
    - Therefore we need to create new cyano_daymap.shp files from cyano_daymap.tiff
    - Place these data in some temporary folder.
    """
    import os
    from bawsvis.paths import data_dir
    from bawsvis.utils import discover_years

    stats_dir = data_dir('stats')
    for year in discover_years(stats_dir, pattern='stats_',
                               endswith='_2.json'):
      file_path_1 = str(stats_dir / f'stats_{year}_2.json')
      file_path_2 = str(stats_dir / 'stats_all.json')

      data = json_reader(file_path_1)
      # stats_all.json does not exist on the first run; start from empty.
      data_2 = json_reader(file_path_2) if os.path.exists(file_path_2) else {}

      data_2 = recursive_dict_update(data_2, data)

      out_file_path = file_path_1.replace(f'stats_{year}_2', 'stats_all')
      json_writer(out_file_path, data_2)