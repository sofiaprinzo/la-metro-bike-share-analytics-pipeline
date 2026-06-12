#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile

import click
import requests
from bs4 import BeautifulSoup


TRIP_FILE_PREFIX = "metro-trips-"
TRIP_FILE_SUFFIX = ".zip"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}


def get_file_name(url):
    return Path(urlparse(url).path).name


def get_trip_quarter(zip_file_name):
    """Read year and quarter from a file name like metro-trips-2026-q1.zip."""
    name_parts = Path(zip_file_name).stem.split("-")

    if len(name_parts) < 4 or name_parts[:2] != ["metro", "trips"]:
        raise ValueError(f"Unexpected trip file name: {zip_file_name}")

    year = int(name_parts[2])
    quarter = int(name_parts[3].replace("q", ""))

    return year, quarter


def find_trip_zip_links(page_url):
    response = requests.get(page_url, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    trip_links_by_quarter = {}

    for link in soup.find_all("a", href=True):
        file_url = urljoin(page_url, link["href"])
        file_name = get_file_name(file_url)

        if file_name.startswith(TRIP_FILE_PREFIX) and file_name.endswith(TRIP_FILE_SUFFIX):
            year, quarter = get_trip_quarter(file_name)
            quarter_key = (year, quarter)

            if quarter_key not in trip_links_by_quarter:
                trip_links_by_quarter[quarter_key] = {
                    "url": file_url,
                    "file_name": file_name,
                    "csv_file_name": f"metro-trips-{year}-q{quarter}.csv",
                    "year": year,
                    "quarter": quarter,
                }

    return sorted(
        trip_links_by_quarter.values(),
        key=lambda item: (item["year"], item["quarter"]),
    )


def download_file(url, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(
        url,
        headers=REQUEST_HEADERS,
        stream=True,
        timeout=60,
    ) as response:
        response.raise_for_status()

        with output_path.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output_file.write(chunk)


def extract_trip_csv(zip_path, output_dir, expected_csv_name):
    output_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path) as zip_file:
        csv_names = [
            name
            for name in zip_file.namelist()
            if Path(name).name.startswith(TRIP_FILE_PREFIX)
            and Path(name).name.endswith(".csv")
        ]

        if not csv_names:
            raise FileNotFoundError(
                f"Could not find a Metro trip CSV inside {zip_path}"
            )

        source_name = csv_names[0]
        output_path = output_dir / expected_csv_name

        with zip_file.open(source_name) as source_file:
            with output_path.open("wb") as output_file:
                output_file.write(source_file.read())

    return output_path


@click.command()
@click.option(
    "--data-page-url",
    default="https://bikeshare.metro.net/about/data/",
    help="Metro Bike Share data page URL",
)
@click.option(
    "--raw-dir",
    default="data/raw",
    help="Directory where raw trip CSV files will be stored",
)
@click.option(
    "--download-dir",
    default="data/raw/downloads",
    help="Directory where downloaded ZIP files will be stored",
)
def run(data_page_url, raw_dir, download_dir):
    """Download missing quarterly Metro Bike Share trip files."""
    raw_path = Path(raw_dir)
    download_path = Path(download_dir)
    trip_links = find_trip_zip_links(data_page_url)

    if not trip_links:
        raise ValueError(f"No Metro trip ZIP links found at {data_page_url}")

    downloaded_count = 0
    skipped_count = 0

    for trip_link in trip_links:
        csv_path = raw_path / trip_link["csv_file_name"]

        if csv_path.exists():
            skipped_count += 1
            print(f"Skipped existing {csv_path}")
            continue

        zip_path = download_path / trip_link["file_name"]

        print(f"Downloading {trip_link['url']}")
        download_file(trip_link["url"], zip_path)

        extracted_path = extract_trip_csv(
            zip_path,
            raw_path,
            trip_link["csv_file_name"],
        )
        downloaded_count += 1

        print(f"Wrote {extracted_path}")

    print(f"Found {len(trip_links):,} quarterly trip file(s)")
    print(f"Downloaded {downloaded_count:,} new trip file(s)")
    print(f"Skipped {skipped_count:,} existing trip file(s)")


if __name__ == "__main__":
    run()
