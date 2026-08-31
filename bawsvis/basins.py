# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""Baltic sub-basins (SVAR BASIN_NR, SHARK-mod SVAR2022) used in the basin statistics.

Basin 15 (Öresund) is included in the area tables (script 14) but left
out of the report figure, as in the original box-plot script.
"""

BASIN_NAMES = {
    3: 'Bottenhavet',
    4: 'Ålands hav',
    6: 'Finska viken',
    7: 'Norra Egentliga Östersjön',
    8: 'Västra Gotlandshavet',
    9: 'Östra Gotlandshavet',
    10: 'Rigabukten',
    11: 'Gdanskbukten',
    12: 'Bornholmshavet',
    13: 'Arkonahavet',
    14: 'Bälthavet',
    15: 'Öresund',
}

PLOTTED_BASINS = tuple(n for n in BASIN_NAMES if n != 15)


def basin_key(basin_nr):
    """Column label used in the combined season-bloom workbook."""
    return f'BASIN_NR_{int(basin_nr)}'
