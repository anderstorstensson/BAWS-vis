#!/usr/bin/env python3
"""Fetch daily BAWS cyanobacteria maps from SMHI's open-data WFS.

Downloads one shapefile per day from the SE.SR "Ytansamling av alger"
dataset (https://opendata-catalog.smhi.se/catalog/single/se-sr-ytansamling-av-alger)
and stores it as cyano_daymap_YYYYMMDD.shp, the naming and format expected
by step 1 of the BAWS-vis pipeline (1_baws_correct_geoms.py).

Data is in EPSG:3006 (SWEREF99 TM) with a 'class' attribute:
1 = cloud, 2 = subsurface bloom, 3 = surface bloom, 4 = no data.

License: SMHI open data (https://www.smhi.se/data/om-smhis-data/villkor-for-anvandning).
Cite SMHI as source.

Usage:
    python fetch_wfs_daymaps.py --years 2023 --out ./data/wfs_daymaps
    python fetch_wfs_daymaps.py --years 2002-2005 2023 --out ./data/wfs_daymaps
"""
import argparse
import io
import re
import sys
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

WFS_URL = "https://opendata-view.smhi.se/algae/SR.SeaSurfaceArea/wfs"
TYPE_NAME = "algae:SR.SeaSurfaceArea"
USER_AGENT = "BAWS-vis fetch_wfs_daymaps"
ARCHIVE_START_YEAR = 2002


def build_url(day, result_type=None):
    params = {
        "service": "wfs",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": TYPE_NAME,
        "cql_filter": f"date='{day.isoformat()}'",
        # Without an explicit srsName, GeoServer honors EPSG:3006's official
        # (northing, easting) axis order and the shapefile comes out with
        # swapped coordinates. The plain "EPSG:3006" form forces x=easting.
        "srsName": "EPSG:3006",
    }
    if result_type == "hits":
        params["resultType"] = "hits"
    else:
        params["outputFormat"] = "SHAPE-ZIP"
    return f"{WFS_URL}?{urlencode(params)}"


def http_get(url, timeout, retries, backoff):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if attempt < retries:
                wait = backoff * 2 ** (attempt - 1)
                print(f"    retry {attempt}/{retries - 1} in {wait:.0f}s ({error})")
                time.sleep(wait)
    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_error


def feature_count(day, timeout, retries, backoff):
    body = http_get(build_url(day, result_type="hits"), timeout, retries, backoff)
    match = re.search(rb'numberMatched="(\d+)"', body)
    if match is None:
        raise RuntimeError(f"Unexpected hits response for {day}: {body[:200]!r}")
    return int(match.group(1))


def save_day_shapefile(day, out_dir, timeout, retries, backoff):
    body = http_get(build_url(day), timeout, retries, backoff)
    stem = f"cyano_daymap_{day.strftime('%Y%m%d')}"
    try:
        archive = zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile as error:
        raise RuntimeError(
            f"Response for {day} was not a zip (server error page?): {body[:200]!r}"
        ) from error
    written = []
    for member in archive.namelist():
        suffix = Path(member).suffix.lower()
        if suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".cst"):
            target = out_dir / f"{stem}{suffix}"
            target.write_bytes(archive.read(member))
            written.append(target.name)
    if f"{stem}.shp" not in written:
        raise RuntimeError(f"No .shp in zip for {day}: {archive.namelist()}")
    return written


def season_days(year, start_monthday, end_monthday):
    start = date(year, *start_monthday)
    end = date(year, *end_monthday)
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def parse_years(tokens):
    years = set()
    for token in tokens:
        if "-" in token:
            first, last = token.split("-", 1)
            years.update(range(int(first), int(last) + 1))
        else:
            years.add(int(token))
    bad = [y for y in years if y < ARCHIVE_START_YEAR or y > date.today().year]
    if bad:
        raise SystemExit(f"Years outside archive ({ARCHIVE_START_YEAR}-today): {sorted(bad)}")
    return sorted(years)


def parse_monthday(text):
    month, day = text.split("-", 1)
    return int(month), int(day)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--years", nargs="+", required=True,
                        help="Years and/or ranges, e.g. 2023 or 2002-2005")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--season-start", default="05-20", type=parse_monthday,
                        help="Season start as MM-DD (default 05-20)")
    parser.add_argument("--season-end", default="09-30", type=parse_monthday,
                        help="Season end as MM-DD (default 09-30)")
    parser.add_argument("--sleep", type=float, default=1.0,
                        help="Seconds to wait between days (default 1.0)")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--backoff", type=float, default=5.0,
                        help="First retry delay in seconds, doubles per retry")
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-download days that already exist locally")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    totals = {"downloaded": 0, "empty": 0, "skipped": 0, "failed": 0}
    failed_days = []

    for year in parse_years(args.years):
        print(f"=== {year}")
        for day in season_days(year, args.season_start, args.season_end):
            stem = f"cyano_daymap_{day.strftime('%Y%m%d')}"
            if not args.overwrite and (out_dir / f"{stem}.shp").exists():
                totals["skipped"] += 1
                continue
            try:
                count = feature_count(day, args.timeout, args.retries, args.backoff)
                if count == 0:
                    print(f"  {day}  no features")
                    totals["empty"] += 1
                else:
                    save_day_shapefile(day, out_dir, args.timeout,
                                       args.retries, args.backoff)
                    print(f"  {day}  {count} features -> {stem}.shp")
                    totals["downloaded"] += 1
            except RuntimeError as error:
                print(f"  {day}  FAILED: {error}", file=sys.stderr)
                totals["failed"] += 1
                failed_days.append(day.isoformat())
            time.sleep(args.sleep)

    print(f"\nDone. downloaded={totals['downloaded']} empty={totals['empty']} "
          f"skipped={totals['skipped']} failed={totals['failed']}")
    if failed_days:
        print("Failed days (rerun without --overwrite to retry just these):")
        print(" ", " ".join(failed_days))
        sys.exit(1)


if __name__ == "__main__":
    main()
