#!/usr/bin/env bash
set -e

python ingestion/ingest_trips.py
python ingestion/ingest_stations.py
python warehouse/build_warehouse.py
python export/export_tableau_csvs.py