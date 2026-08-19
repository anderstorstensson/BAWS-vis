"""
Created on 2021-09-02 14:57
@author: johannes
"""
from bawsvis.utils import generate_filepaths
from bawsvis.session import Session
from bawsvis.data_handler import create_7day_composite
from bawsvis.paths import data_dir


if __name__ == "__main__":
    # Set path to data directory.
    # NOTE: create_7day_composite writes each cyano_weekmap tiff next to
    # the daily tiffs, i.e. into corrected_geoms/ as well.
    s = Session(data_path=data_dir('corrected_geoms'))

    # Generate filepaths
    generator = generate_filepaths(
        s.data_path,
        pattern='cyano_daymap_',
        endswith='.tiff'
    )

    for f in generator:
        print(f)
        create_7day_composite(s.data_path, f)
