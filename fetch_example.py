#!/usr/bin/env python
"""
fetch_example.py

This example demonstrates the full capabilities of the flight_tracer package.
It fetches real flight trace data, processes it (computing the continuous ping_time
and inferring separate flight legs based on time gaps), saves the results locally
with a filename that includes the ICAO code(s) and today's date, and optionally
uploads the CSV and GeoJSON files to S3 using a specified AWS profile.
"""

import os
from datetime import date, datetime
from flight_tracer import FlightTracer
import geopandas as gpd

# Two options:
# 1. Use a specific AWS profile from your environment 
aws_profile = os.getenv("MY_PERSONAL_PROFILE")

# 2. Use standard AWS credentials from your environment
aws_creds = {
    "aws_access_key_id": os.getenv("MY_AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("MY_AWS_SECRET_ACCESS_KEY")
}

# You can pass either aws_profile or aws_creds.
# Example: using the AWS profile
tracer = FlightTracer(aircraft_ids=["A11F59"], aws_profile=aws_profile)

# Define the date range for which you want to fetch trace data
start = date(2025, 2, 7)
end = date(2025, 2, 8)

# Set export format: "geojson" or "shp"
export_format = "geojson"  # Change to "geojson" if needed

# Fetch raw flight trace data from ADSBExchange
print("Fetching raw flight trace data...")
raw_df = tracer.get_traces(start, end, recent=False)

if raw_df.empty:
    print("No trace data was fetched.")
else:
    print("Raw data sample:")
    print(raw_df.head())

    # Process the raw data to compute a continuous 'ping_time' (UTC)
    # and to infer flight legs based on time gaps.
    print("\nProcessing flight data into a GeoDataFrame...")
    gdf = tracer.process_flight_data(raw_df)

    print("Processed GeoDataFrame sample:")
    print(gdf.head())
    
    # Optionally, inspect the unique flight legs detected in the data
    print("\nUnique flight legs detected:")
    print(gdf["leg_id"].unique())

    # Build dynamic filenames that include the ICAO code(s) and today's date
    icao_str = "_".join(tracer.aircraft_ids)
    date_str = datetime.today().strftime("%Y%m%d")
    base_path = f"data/flight_traces_{icao_str}_{date_str}"

    # Save the processed data locally as CSV
    csv_filename = f"{base_path}.csv"
    gdf.to_csv(csv_filename, index=False)
    print(f"\nSaved processed data locally as '{csv_filename}'.")

    # Export flight data in the selected format
    tracer.export_flight_data(gdf, base_path, export_format=export_format)

    # Optionally upload the processed files to S3
    bucket_name = "stilesdata.com"  # Replace with your bucket name
    csv_object_name = f"flight_tracer/flight_traces_{icao_str}_{date_str}.csv"
    
    print("\nUploading files to S3 (if AWS credentials are configured)...")
    tracer.upload_to_s3(gdf, bucket_name, csv_object_name, f"{base_path}.{export_format}")
    print("Upload process completed.")

    # Plot the points with a basemap and optionally save the plot as a PNG
    fig_filename = f"visuals/flight_map_{icao_str}_{date_str}.png"
    tracer.plot_flights(gdf, geometry_type='points', figsize=(12,10), fig_filename=fig_filename)