# FlightTracer

FlightTracer is a Python package to fetch and process flight trace data from ADS-B Exchange for any given aircraft. It supports fetching data for a single ICAO code or a list of codes and it offers an option to upload processed data as CSV and GeoJSON to Amazon S3. It also detects separate flight legs based on significant time gaps and creates a combined flight leg identifier (call_sign, date, leg) for easier differentiation in GIS tools.

## Installation

1. Clone the repository or download the source code  
2. Install the required dependencies using pip

~~~bash
pip install requests pandas geopandas boto3
~~~

## Usage

FlightTracer can be used with either a list of aircraft IDs or a metadata URL that contains aircraft information. You can also configure AWS credentials if you wish to upload the output to S3. In addition, you can pass an AWS profile name if you have multiple sets of credentials in your environment.

### Example

Below is an example of how to use FlightTracer:

~~~python
#!/usr/bin/env python
"""
example.py

This example demonstrates the full capabilities of the FlightTracer package.
It fetches real flight trace data, processes it (computing the continuous ping_time
and inferring separate flight legs based on time gaps), saves the results locally
with a filename that includes the ICAO code(s) and today's date, and optionally
uploads the CSV and GeoJSON files to S3 using a specified AWS profile.
"""

import os
from datetime import date, datetime
from flight_tracer import FlightTracer

# Option 1: Use explicit AWS credentials (via environment variables or directly)
aws_credentials = {
    "aws_access_key_id": os.getenv("MY_AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("MY_AWS_SECRET_ACCESS_KEY")
}

# Option 2: Alternatively, use an AWS profile from your environment
aws_profile = os.getenv("MY_AWS_PROFILE")  # e.g., "my_profile_name"

# You can initialize FlightTracer with either explicit credentials or an AWS profile.
# For example, to use explicit credentials:
# tracer = FlightTracer(aircraft_ids=["a97753"], aws_creds=aws_credentials)
# Or, to use an AWS profile:
tracer = FlightTracer(aircraft_ids=["a97753"], aws_profile=aws_profile)

# Define the date range for trace data
start = date(2025, 1, 28)
end = date(2025, 2, 1)

# Fetch raw flight trace data from ADS-B Exchange
print("Fetching raw flight trace data...")
raw_df = tracer.get_traces(start, end)
if raw_df.empty:
    print("No valid data to process.")
else:
    print("Raw data sample:")
    print(raw_df.head())

    # Process trace data into a GeoDataFrame (computing continuous ping_time in UTC
    # and detecting flight leg changes based on time gaps). A new 'flight_leg' column is
    # created that combines call_sign, flight_date, and leg_id.
    print("\nProcessing flight data into a GeoDataFrame...")
    gdf = tracer.process_flight_data(raw_df)
    print("Processed GeoDataFrame sample:")
    print(gdf.head())

    # Optionally, inspect the unique flight legs detected in the data.
    print("\nUnique flight legs detected:")
    print(gdf["flight_leg"].unique())

    # Build dynamic filenames that include the ICAO code(s) and today's date
    icao_str = "_".join(tracer.aircraft_ids)
    date_str = datetime.today().strftime("%Y%m%d")
    csv_filename = f"data/flight_traces_{icao_str}_{date_str}.csv"
    geojson_filename = f"data/flight_traces_{icao_str}_{date_str}.geojson"

    # Save the processed data locally as CSV and GeoJSON
    gdf.to_csv(csv_filename, index=False)
    gdf.to_file(geojson_filename, driver="GeoJSON")
    print(f"\nSaved processed data locally as '{csv_filename}' and '{geojson_filename}'.")

    # Optionally, upload the processed files to S3
    # (Replace 'your-bucket-name' with your actual S3 bucket name)
    bucket_name = "your-bucket-name"
    csv_object_name = f"flight_tracer/flight_traces_{icao_str}_{date_str}.csv"
    geojson_object_name = f"flight_tracer/flight_traces_{icao_str}_{date_str}.geojson"
    print("\nUploading files to S3 (if AWS credentials or profile are configured)...")
    tracer.upload_to_s3(gdf, bucket_name, csv_object_name, geojson_object_name)
    print("Upload process completed.")
~~~

## Configuration

FlightTracer supports the following configurations:

- **Aircraft IDs or metadata URL**: Provide either a list of ICAO codes or a metadata URL to extract aircraft information.  
- **AWS credentials or profile**: Pass AWS credentials as a dictionary, specify an AWS profile, or set them as environment variables.  
- **Date range**: Define the start and end dates to fetch trace data.

## Notes

- Ensure that your AWS credentials or profile are configured correctly if you wish to use the S3 upload feature.  
- The package fetches data from ADS-B Exchange so the availability of data depends on the public API.  
- Flight leg detection is based on a configurable time gap threshold (default is 15 minutes). Adjust as needed for your data.

## License

This project is open source so feel free to modify and use it according to your needs.