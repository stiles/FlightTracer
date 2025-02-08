#!/usr/bin/env python
"""
fetch_from_json.py

This example fetches ADS-B flight trace data using a JSON file with a list of aircraft objects.
It extracts ICAO codes, retrieves trace data for the specified aircraft, processes it, and
exports the data as CSV and GeoJSON. Optionally, it can upload results to S3 and generate maps.
"""

import os
import json
import requests
from datetime import date, datetime
from flight_tracer import FlightTracer
import geopandas as gpd

# URL of the JSON file containing aircraft data
json_url = "https://stilesdata.com/lapd-helicopters/lapd_aircraft.json"

# Fetch the JSON file
print("Fetching aircraft list...")
response = requests.get(json_url)
if response.status_code != 200:
    print("❌ Failed to fetch aircraft list.")
    exit()

# Parse JSON and extract ICAO codes
aircraft_data = response.json()
icao_codes = [aircraft["icao"] for aircraft in aircraft_data]

print(f"✅ Extracted {len(icao_codes)} ICAO codes: {icao_codes}")

# AWS credentials (optional)
aws_profile = os.getenv("MY_PERSONAL_PROFILE")
aws_creds = {
    "aws_access_key_id": os.getenv("MY_AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("MY_AWS_SECRET_ACCESS_KEY"),
}

# Initialize FlightTracer
tracer = FlightTracer(aircraft_ids=icao_codes, aws_profile=aws_profile)

# Define the date range for fetching flight trace data
start = date(2025, 1, 1)
end = date(2025, 2, 8)

print("Fetching raw flight trace data...")

# Fetch all traces for the specified date range
raw_df = tracer.get_traces(start, end, recent=False)

# Fetch only the most recent trace (if needed)
# raw_df = tracer.get_traces(recent=True)

if raw_df.empty:
    print("❌ No trace data was fetched.")
else:
    print("✅ Raw data sample:")
    print(raw_df.head())

    # Process raw data into a GeoDataFrame
    print("\nProcessing flight data into a GeoDataFrame...")
    gdf = tracer.process_flight_data(raw_df)

    print("✅ Processed GeoDataFrame sample:")
    print(gdf.head())

    # Check detected flight legs
    print("\nUnique flight legs detected:")
    print(gdf["leg_id"].unique())

    # Build filenames for output
    date_str = datetime.today().strftime("%Y%m%d")
    csv_filename = f"data/lapd_flight_traces_{date_str}.csv"
    geojson_filename = f"data/lapd_flight_traces_{date_str}.geojson"
    linestring_geojson_filename = f"data/lapd_flight_traces_lines_{date_str}.geojson"

    # Save processed data locally
    gdf.to_csv(csv_filename, index=False)
    gdf.to_file(geojson_filename, driver="GeoJSON")
    print(f"\n✅ Saved data as '{csv_filename}' and '{geojson_filename}'.")

    # Export flight legs as LineStrings
    tracer.export_linestring_geojson(gdf, linestring_geojson_filename)

    # Optionally upload the files to S3
    bucket_name = "stilesdata.com"  # Replace with your S3 bucket
    csv_object_name = f"flight_tracer/lapd_flight_traces_{date_str}.csv"
    geojson_object_name = f"flight_tracer/lapd_flight_traces_{date_str}.geojson"

    print("\nUploading files to S3 (if AWS credentials are configured)...")
    tracer.upload_to_s3(gdf, bucket_name, csv_object_name, geojson_object_name)
    print("✅ Upload process completed.")

    # Generate a flight activity map
    fig_filename = f"visuals/lapd_flight_map_{date_str}.png"
    tracer.plot_flights(gdf, geometry_type='points', figsize=(12, 10), fig_filename=fig_filename)

    print("✅ Map generation complete.")
