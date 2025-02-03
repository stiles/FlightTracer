# FlightTracer: Tracking ADS-B Exchange Flights

[![PyPI version](https://img.shields.io/pypi/v/flight-tracer.svg)](https://pypi.org/project/flight-tracer/)
[![License: CC0-1.0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)

**FlightTracer** is a Python package for fetching, processing, and analyzing flight trace data from **ADS-B Exchange**. It supports a single ICAO code or a list of codes and offers options for exporting processed flight data to **CSV**, **GeoJSON**, and **Amazon S3**.

### :airplane: :helicopter: Features:
- Fetches real flight trace data from [ADS-B Exchange](https://globe.adsbexchange.com/).
- Seeks to identify flight legs by detecting time gaps in the data.
- Saves processed flight data as CSV and GeoJSON.
- Generates Linestring GeoJSONs for flight paths.
- Provides plotting of flight paths with basemaps.
- Supports AWS S3 uploads for cloud storage.

---

## **Installation**
FlightTracer is available on **PyPI** and can be installed using:

```bash
pip install flight-tracer
```

Alternatively, you can install the latest development version from GitHub:

```bash
pip install git+https://github.com/stiles/flight_tracer.git
```

### **Dependencies**
FlightTracer requires the following packages:
- `requests`
- `pandas`
- `geopandas`
- `boto3`
- `matplotlib`
- `contextily`
- `shapely`

These will be installed automatically with `pip`.

---

## **Usage**
FlightTracer can be used with **a list of aircraft IDs** or **a metadata URL** containing aircraft information.

### **Basic Example**
```python
from flight_tracer import FlightTracer
from datetime import date

# Initialize FlightTracer with a single ICAO code
tracer = FlightTracer(aircraft_ids=["a97753"])

# Define a date range for flight trace data
start = date(2025, 1, 28)
end = date(2025, 2, 1)

# Fetch and process flight data
flight_data = tracer.get_traces(start, end)

# Convert to a GeoDataFrame
gdf = tracer.process_flight_data(flight_data)

# Save to a CSV and GeoJSON
gdf.to_csv("flight_data.csv", index=False)
gdf.to_file("flight_data.geojson", driver="GeoJSON")

# Plot the flight paths
tracer.plot_flights(gdf, geometry_type="points", figsize=(10,8))
```

### **Using AWS S3 for Storage**
If you want to **upload processed flight data** to AWS S3, provide your AWS credentials:

```python
aws_creds = {
    "aws_access_key_id": "your-access-key",
    "aws_secret_access_key": "your-secret-key"
}

tracer = FlightTracer(aircraft_ids=["a97753"], aws_creds=aws_creds)

# Upload to S3
tracer.upload_to_s3(gdf, bucket_name="your-bucket",
                     csv_object_name="flight_data.csv",
                     geojson_object_name="flight_data.geojson")
```

---

## Outputs

The example above would output a GeoJSON points file with features such as this one for each moment captured during the aircraft's flight. 

**Notes:**

- Values such as altitude and ground speed are raw and uncorrected. 
- Use the `flight_leg` item to identify separate flights in a single calendar day. 
- I live in Los Angeles so I convert the `point_time` value from UTC, or Zulu time, to Pacific Time. You can choose your own location.
- This software is experimental and under active development so use with caution. 

```json
"features": [
        {
            "type": "Feature",
            "properties": {
                "flight": "XAUCI",
                "point_time": "2025-01-31T17:52:15.010",
                "flight_date_pst": "2025-01-31",
                "point_time_pst_clean": "09:52:15",
                "altitude": 37000,
                "ground_speed": 499.2,
                "heading": 22.9,
                "lat": 31.656967,
                "lon": -81.21083,
                "icao": "0d086e",
                "call_sign": "XAUCI",
                "leg_id": 1,
                "flight_leg": "XAUCI_2025-01-31_leg1"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -81.21083,
                    31.656967
                ]
            }
        }
    ]
```

---

## **Roadmap**
🔹 **Metadata enrichment**: Integrate external aircraft metadata (FAA, ICAO, etc.)  
🔹 **Performance improvements**: Parallel processing for large datasets  
🔹 **Advanced plotting**: More customizable visualizations  
🔹 **Enhanced CLI tools**: Command-line interface for easy usage  

---

## **Credits**
Thanks to [ADS-B Exchange](https://globe.adsbexchange.com/) for the data. If you use the service, consider [subscribing](https://store.adsbexchange.com/collections/subscriptions) or [contributing](https://www.adsbexchange.com/ways-to-join-the-exchange/) data to its network. 

## **License**
This project is licensed under the **Creative Commons CC0 1.0 Universal** Public Domain Dedication.

[![CC0 Badge](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/legalcode)