# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""HELCOM sub-basins used in the basin statistics.

Keys are the HELCOM sub-basin numbers (HELCOM_ID SEA-0nn, see
bawsvis/helcom_basins.py). The names are the Swedish ones used in the
figures and the indicator delivery files; the HELCOM English name is in
the comment.

Of the 17 HELCOM sub-basins, Bothnian Bay (17) lies outside the BAWS
area, and Kattegat (1) and The Quark (16) are inside it but left out of
the statistics, as they were with the SVAR basins. The Archipelago Sea,
a separate SVAR basin that used to be left out, is part of the HELCOM
Åland Sea. The former SVAR basin Bälthavet corresponds to Great Belt,
Kiel Bay and Bay of Mecklenburg together.

Basin 3 (Öresund / The Sound) is included in the area tables (script 14)
but left out of the report figure, as in the original box-plot script.
"""

BASIN_NAMES = {
    15: 'Bottenhavet',                 # SEA-015 Bothnian Sea
    14: 'Ålands hav',                  # SEA-014 Åland Sea
    13: 'Finska viken',                # SEA-013 Gulf of Finland
    12: 'Norra Egentliga Östersjön',   # SEA-012 Northern Baltic Proper
    10: 'Västra Gotlandshavet',        # SEA-010 Western Gotland Basin
    9: 'Östra Gotlandshavet',          # SEA-009 Eastern Gotland Basin
    11: 'Rigabukten',                  # SEA-011 Gulf of Riga
    8: 'Gdanskbukten',                 # SEA-008 Gdansk Basin
    7: 'Bornholmshavet',               # SEA-007 Bornholm Basin
    6: 'Arkonahavet',                  # SEA-006 Arkona Basin
    5: 'Mecklenburgbukten',            # SEA-005 Bay of Mecklenburg
    4: 'Kielbukten',                   # SEA-004 Kiel Bay
    2: 'Stora Bält',                   # SEA-002 Great Belt
    3: 'Öresund',                      # SEA-003 The Sound
}

PLOTTED_BASINS = tuple(n for n in BASIN_NAMES if n != 3)


def helcom_id(basin_nr):
    """HELCOM_ID of a basin number, e.g. 15 -> 'SEA-015'."""
    return f'SEA-{int(basin_nr):03d}'


def basin_key(basin_nr):
    """Column label used in the season-bloom workbooks (the HELCOM_ID)."""
    return helcom_id(basin_nr)


def basin_nr_from_key(key):
    """Inverse of basin_key: 'SEA-015' -> 15."""
    return int(str(key).rsplit('-', 1)[-1])
