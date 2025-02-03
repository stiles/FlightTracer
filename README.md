# Tracking ADS-B Exchange flights

FlightTracer is a Python package to fetch and process aircraft trace data from ADS-B Exchange. It supports a single ICAO code or a list of codes — and it has an option to upload processed data as CSV and GeoJSON to Amazon S3. FlightTracer also detects separate flight legs based on significant time gaps and creates a combined flight leg identifier (call_sign, date, leg) for easier differentiation in GIS tools. In addition, the package also provides plotting capabilities with a basemap and an option to save the plot as a PNG.

This project is in the early stages of development. Contributions and feedback welcome. 

## Installation

1. Clone the repository or download the source code  
2. Install the required dependencies using pip

~~~bash
pip install requests pandas geopandas boto3 contextily matplotlib
~~~

## Usage

FlightTracer can be used with either a list of aircraft IDs or a metadata URL that contains aircraft information. You can also configure AWS credentials if you wish to upload the output to S3. In addition, you can pass an AWS profile name if you have multiple sets of credentials in your environment.

### Example

Below is an example of how to use FlightTracer:

~~~python
#!/usr/bin/env python
"""
fetch_example.py

This example fetches real flight trace data, processes it (computing the continuous ping_time
and inferring separate flight legs based on time gaps), saves the results locally
with a filename that includes the ICAO code(s) and today's date, and optionally
uploads the CSV and GeoJSON files to S3 using a specified AWS profile.
It also shows how to generate a plot of the flight activity and save the plot as a PNG.
"""

import os
from datetime import date, datetime
from flight_tracer import FlightTracer
import geopandas as gpd

# Option 1: Use explicit AWS credentials (via environment variables or directly)
aws_credentials = {
    "aws_access_key_id": os.getenv("MY_AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("MY_AWS_SECRET_ACCESS_KEY")
}

# Option 2: Alternatively, use an AWS profile from your environment
aws_profile = os.getenv("MY_AWS_PROFILE")  # e.g., "my_profile_name"

# Initialize flight_tracer with either explicit credentials or an AWS profile.
# For example, to use explicit credentials:
# tracer = flight_tracer(aircraft_ids=["a97753"], aws_creds=aws_credentials)
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

    # Export linestring geometry for each flight leg
    linestring_geojson_filename = f"data/flight_traces_lines_{icao_str}_{date_str}.geojson"
    tracer.export_linestring_geojson(gdf, linestring_geojson_filename)

    # Optionally upload the processed files to S3
    bucket_name = "your-bucket-name"  # replace with your bucket name
    csv_object_name = f"flight_tracer/flight_traces_{icao_str}_{date_str}.csv"
    geojson_object_name = f"flight_tracer/flight_traces_{icao_str}_{date_str}.geojson"
    print("\nUploading files to S3 (if AWS credentials or profile are configured)...")
    tracer.upload_to_s3(gdf, bucket_name, csv_object_name, geojson_object_name)
    print("Upload process completed.")

    # Plot the points with a basemap and optionally save the plot as a PNG
    fig_filename = f"visuals/flight_map_{icao_str}_{date_str}.png"
    tracer.plot_flights(gdf, geometry_type='points', figsize=(12,10), fig_filename=fig_filename)
~~~

## Configuration

The package supports the following configurations:

- **Aircraft IDs or metadata URL**: Provide either a list of ICAO codes or a metadata URL to extract aircraft information.  
- **AWS credentials or profile**: Pass AWS credentials as a dictionary, specify an AWS profile, or set them as environment variables.  
- **Date range**: Define the start and end dates to fetch trace data.

## Notes

- Ensure that your AWS credentials or profile are configured correctly if you wish to use the S3 upload feature.  
- The package fetches data from ADS-B Exchange so the availability of data depends on the public API.  
- Flight leg detection is based on a configurable time gap threshold (default is 15 minutes). Adjust as needed for your data.  
- Plotting functionality includes an option to expand the plotted extent (via `pad_factor`) for broader context and to save the plot as a PNG.

## Roadmap for Enhancements

#### Enrich with external metadata:
- Build tools to “hydrate” your flight data with additional aircraft metadata from external sources such as FAA, ICAO, or other databases (e.g., aircraft type, operator, age, etc.).

#### Package distribution:
- Finalize the code structure (including tests, documentation, and a setup script) and publish the package to PyPI for installation via pip.

#### Enhanced documentation and examples:
- Update the README with comprehensive, end-to-end examples for various scenarios (e.g., pulling all flights for a month of a particular aircraft, processing a list of aircraft from a metadata URL, etc.), including usage examples for linestring export, leg splitting, and metadata enrichment.

#### Configurable thresholds and options:
- Allow users to adjust parameters like the time-gap threshold for determining new flight legs, output formats, and which metadata fields to hydrate.

#### Performance and error handling improvements:
- Add caching or parallel processing options to improve performance when fetching data over a long date range or for multiple aircraft.
- Improve error handling to gracefully skip problematic dates or flights while logging issues.

## License

This project is licensed under the **Creative Commons CC0 1.0 Universal (CC0 1.0) Public Domain Dedication**.  

This means that to the extent possible under law, the creator has waived all copyright and related or neighboring rights to this work. 

You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.

For more details, refer to the full [CC0 1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/legalcode).

![CC0 Badge](https://licensebuttons.net/p/zero/1.0/88x31.png)
