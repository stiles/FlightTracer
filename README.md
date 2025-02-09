# FlightTracer: Tracking ADS-B Exchange flights

# FlightTracer: Tracking ADS-B Exchange flights

[![PyPI version](https://img.shields.io/pypi/v/flight-tracer.svg)](https://pypi.org/project/flight-tracer/)
[![License: CC0-1.0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)

**FlightTracer** is a Python package for fetching, processing, storing and plotting flight trace data from [ADS-B Exchange](https://globe.adsbexchange.com/). It provides tools for managing flight data and offers flexible options for users. The project is new and under active development.

---

## Features

- Fetches flight trace data from [ADS-B Exchange](https://globe.adsbexchange.com/)
- Identifies flight legs by detecting time gaps and handling Zulu day transitions
- Converts raw flight trace data into GeoDataFrames for easy analysis
- Saves processed flight data in CSV, GeoJSON or shapefile formats
- Visualizes flight paths with customizable basemaps and clear leg differentiation
- Supports AWS S3 uploads for cloud storage
- Offers customization options for file formats and filtering
- **Now includes a command-line interface (CLI) for easy execution**

---

## Installation

FlightTracer is available on **PyPI** and can be installed using:

```bash
pip install flight-tracer
```

Alternatively, install the latest development version from GitHub:

```bash
pip install git+https://github.com/stiles/flight_tracer.git
```

### Dependencies

FlightTracer requires the following Python packages:
- `requests`
- `pandas`
- `geopandas`
- `boto3`
- `matplotlib`
- `contextily`
- `shapely`
- `click` (for CLI support)

These dependencies will be installed automatically with `pip`.

---

## Using FlightTracer via CLI

With the new CLI support, FlightTracer can be run directly from the command line.

### **Basic command**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --format csv
```

This fetches flight data for aircraft `A11F59` for the given date range and saves it as a CSV file.

### **CLI options**

| Option            | Description |
|------------------|-------------|
| `--icao`         | ICAO aircraft ID (required, can be multiple) |
| `--start`        | Start date (YYYY-MM-DD) |
| `--end`          | End date (YYYY-MM-DD) |
| `--format`       | Output format: `csv`, `geojson`, `shp` |
| `--filter-ground` | Filter out ground-level points (default: True) |
| `--upload`       | Upload to S3 (requires credentials) |
| `--plot`         | Generate a visualization of the flight trace |

### **Example: Fetch, process, and export as GeoJSON**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --format geojson
```

### **Example: Fetch and plot flight trace**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --plot
```

### **Example: Upload results to AWS S3**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --upload --bucket my-bucket
```

---

## Using FlightTracer in Python

FlightTracer can also be used as a Python library for more flexibility.

### **Basic example**

```python
from flight_tracer import FlightTracer
from datetime import date

# Initialize the FlightTracer with an aircraft ID
tracer = FlightTracer(aircraft_ids=["A11F59"])

# Define the date range for fetching trace data
start = date(2025, 2, 7)
end = date(2025, 2, 8)

# Fetch flight data
raw_df = tracer.get_traces(start, end)

# Process the raw data into a GeoDataFrame
if not raw_df.empty:
    gdf = tracer.process_flight_data(raw_df)
    print(gdf.head())
```

---

### Customizing output

FlightTracer provides options to save data in different formats and configure the output directory:

#### **Supported file formats**
- CSV
- GeoJSON
- Esri shapefile

#### **Example: Exporting data**
```python
# Save processed data locally
tracer.export_flight_data(gdf, base_path="data/flight_traces", export_format="geojson") # or "shp"
```
# FlightTracer: Tracking ADS-B Exchange flights

[![PyPI version](https://img.shields.io/pypi/v/flight-tracer.svg)](https://pypi.org/project/flight-tracer/)
[![License: CC0-1.0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)

**FlightTracer** is a Python package for fetching, processing, storing and plotting flight trace data from [ADS-B Exchange](https://globe.adsbexchange.com/). It provides tools for managing flight data and offers flexible options for users. The project is new and under active development.

---

## Features

- Fetches flight trace data from [ADS-B Exchange](https://globe.adsbexchange.com/)
- Identifies flight legs by detecting time gaps and handling Zulu day transitions
- Converts raw flight trace data into GeoDataFrames for easy analysis
- Saves processed flight data in CSV, GeoJSON or shapefile formats
- Visualizes flight paths with customizable basemaps and clear leg differentiation
- Supports AWS S3 uploads for cloud storage
- Offers customization options for file formats and filtering
- **Now includes a command-line interface (CLI) for easy execution**

---

## Installation

FlightTracer is available on **PyPI** and can be installed using:

```bash
pip install flight-tracer
```

Alternatively, install the latest development version from GitHub:

```bash
pip install git+https://github.com/stiles/flight_tracer.git
```

### Dependencies

FlightTracer requires the following Python packages:
- `requests`
- `pandas`
- `geopandas`
- `boto3`
- `matplotlib`
- `contextily`
- `shapely`
- `click` (for CLI support)

These dependencies will be installed automatically with `pip`.

---

## Using FlightTracer via CLI

With the new CLI support, FlightTracer can be run directly from the command line.

### **Basic command**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --format csv
```

This fetches flight data for aircraft `A11F59` for the given date range and saves it as a CSV file.

### **CLI options**

| Option            | Description |
|------------------|-------------|
| `--icao`         | ICAO aircraft ID (required, can be multiple) |
| `--start`        | Start date (YYYY-MM-DD) |
| `--end`          | End date (YYYY-MM-DD) |
| `--format`       | Output format: `csv`, `geojson`, `shp` |
| `--filter-ground` | Filter out ground-level points (default: True) |
| `--upload`       | Upload to S3 (requires credentials) |
| `--plot`         | Generate a visualization of the flight trace |

### **Example: Fetch, process, and export as GeoJSON**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --format geojson
```

### **Example: Fetch and plot flight trace**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --plot
```

### **Example: Upload results to AWS S3**

```bash
flight-tracer --icao A11F59 --start 2025-02-07 --end 2025-02-08 --upload --bucket my-bucket
```

---

## Using FlightTracer in Python

FlightTracer can also be used as a Python library for more flexibility.

### **Basic example**

```python
from flight_tracer import FlightTracer
from datetime import date

# Initialize the FlightTracer with an aircraft ID
tracer = FlightTracer(aircraft_ids=["A11F59"])

# Define the date range for fetching trace data
start = date(2025, 2, 7)
end = date(2025, 2, 8)

# Fetch flight data
raw_df = tracer.get_traces(start, end)

# Process the raw data into a GeoDataFrame
if not raw_df.empty:
    gdf = tracer.process_flight_data(raw_df)
    print(gdf.head())
```

---

### Customizing output

FlightTracer provides options to save data in different formats and configure the output directory:

#### **Supported file formats**
- CSV
- GeoJSON
- Esri shapefile

#### **Example: Exporting data**
```python
# Save processed data locally
tracer.export_flight_data(gdf, base_path="data/flight_traces", export_format="geojson") # or "shp"
```
---

### **AWS S3 integration**

Easily upload processed data to AWS S3 for cloud storage. Provide your AWS credentials or use an AWS profile:

#### **Example: Uploading to S3**
```python
aws_creds = {
    "aws_access_key_id": "your-access-key",
    "aws_secret_access_key": "your-secret-key"
}

tracer.upload_to_s3(
    gdf,
    bucket_name="your-bucket",
    csv_object_name="flight_data.csv",
    geojson_object_name="flight_data.geojson"
)
```

---

## **Advanced features**

### **Metadata mapping**
Enrich your flight data with custom metadata using mapping options.

#### **Example: Adding metadata**
```python
meta_df = pd.DataFrame({
    "flight": ["AAL124", "UAL1053"],
    "airline": ["American Airlines", "United Airlines"]
})
mapping_info = (meta_df, "flight", "airline", "airline")

# Pass mapping_info to process_flight_data
gdf = tracer.process_flight_data(raw_df, mapping_info=mapping_info)
```

### **Custom time thresholds for legs**
Customize the time gap threshold for detecting new flight legs:

#### **Example: Adjusting time gap threshold**
```python
tracer.set_time_gap_threshold(minutes=45)
```

---

## Outputs

The example above would output two GeoJSON files: One with point features for each moment captured during the aircraft's flight and another with lines representing the overall route(s). Legs of the flights are differentiated in the `flight_leg` item. The script also outputs a CSV and a simple map plot.

```json
"features": [
    {
        "type": "Feature",
        "properties": {
            "point_time": "2025-02-08T02:38:02.920",
            "flight_date_pst": "2025-02-07",
            "altitude": "30000",
            "ground_speed": 408.4,
            "heading": 253.2,
            "lat": 35.968307,
            "lon": -97.348509,
            "icao": "a11f59",
            "call_sign": "UAL333",
            "leg_id": 1,
            "flight_leg": "UAL333_leg1"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [
                -97.348509,
                35.968307
            ]
        }
    }
]
```

**Notes:**

- Values such as altitude and ground speed are raw and uncorrected
- I live in Los Angeles so I convert the `point_time` value from UTC, or Zulu time, to Pacific Time. You can choose your own location.

The plot has different colors for the various legs that day to help you identify them more clearly as you use the data for more advanced visualizations using QGIS or other tools.

![alt text](https://github.com/stiles/flight-tracer/raw/main/visuals/flight_map_a11f59_20250208.png)

---

## **Roadmap**

- **CLI option**: Add a command-line interface for easier usage
- **Improved metadata integration**: Automatically enrich flight data with external sources (e.g., FAA, ICAO)
- **Parallel processing**: Optimize for large datasets
- **Better visualizations**: Add support for tools like Altair or Plotly
- **Analysis tools**: Better understand a flight's speed and altitude changes

---

## **Credits**
Thanks to [ADS-B Exchange](https://globe.adsbexchange.com/) for providing open flight data. Please consider supporting their service by [subscribing](https://store.adsbexchange.com/collections/subscriptions) or [contributing data](https://www.adsbexchange.com/ways-to-join-the-exchange/).

---

## **License**
This project is licensed under the **Creative Commons CC0 1.0 Universal** Public Domain Dedication.

[![CC0 Badge](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/legalcode)