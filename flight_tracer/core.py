# flight_tracer/core.py
import requests
import pandas as pd
import geopandas as gpd
import boto3
import os
from datetime import date, timedelta
from io import BytesIO

class FlightTracer:
    # Default columns from the ADSB trace data (we’ll drop the extra ones)
    DEFAULT_COLUMNS = [
        "time", "lat", "lon", "altitude", "ground_speed", "heading",
        "unknown1", "baro_rate", "details", "code", "alt_geom",
        "unknown2", "unknown3", "unknown4",
    ]
    DROP_COLUMNS = ["unknown1", "code", "baro_rate", "unknown2", "unknown3", "unknown4"]

    def __init__(self, aircraft_ids=None, meta_url=None, aws_creds=None, aws_profile=None):
        """
        Initialize with a list of aircraft_ids or a metadata URL.
        Optionally pass aws_creds as a dict with keys:
          'aws_access_key_id' and 'aws_secret_access_key'.
        Alternatively, pass aws_profile to use a specific AWS CLI profile.
        """
        if meta_url:
            meta_df = pd.read_json(meta_url)
            # Clean up and extract ICAO codes from metadata
            self.aircraft_ids = meta_df["icao"].str.strip().str.lower().tolist()
            self.meta_df = meta_df
        elif aircraft_ids:
            self.aircraft_ids = [ac.strip().lower() for ac in aircraft_ids]
            self.meta_df = None
        else:
            raise ValueError("Either aircraft_ids or meta_url must be provided")

        # Set up S3 client using aws_profile if provided, else explicit credentials if provided
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        elif aws_creds:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_creds.get('aws_access_key_id'),
                aws_secret_access_key=aws_creds.get('aws_secret_access_key')
            )
        else:
            self.s3_client = None

    def generate_urls(self, start_date, end_date):
        """Generate ADSBExchange URLs for each aircraft over a date range."""
        base_url = "https://globe.adsbexchange.com/globe_history/"
        delta = timedelta(days=1)
        urls = []
        for icao in self.aircraft_ids:
            # Use last 2 chars to build the URL path
            icao_suffix = icao[-2:]
            current_date = start_date
            while current_date <= end_date:
                year = current_date.strftime("%Y")
                month = current_date.strftime("%m")
                day = current_date.strftime("%d")
                url = f"{base_url}{year}/{month}/{day}/traces/{icao_suffix}/trace_full_{icao}.json"
                urls.append((url, icao))
                current_date += delta
        return urls

    def fetch_trace_data(self, url, icao):
        """Fetch and return a trace DataFrame from a given URL."""
        headers = {"Referer": f"https://globe.adsbexchange.com/?icao={icao}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data and "trace" in data:
                trace_df = pd.DataFrame(data["trace"], columns=self.DEFAULT_COLUMNS)
                trace_df = trace_df.drop(columns=self.DROP_COLUMNS, errors='ignore')
                # Add additional metadata
                trace_df["nnumber"] = data["r"]
                trace_df["model"] = data["t"]
                trace_df["desc"] = data["desc"]
                # Convert the initial timestamp to a datetime
                trace_df["timestamp"] = pd.to_datetime(data["timestamp"], unit="s")
                # Compute the actual ping time by adding the offset
                trace_df["ping_time"] = trace_df["timestamp"] + pd.to_timedelta(trace_df["time"], unit="s")
                trace_df["icao"] = icao  # Add the aircraft id to the DataFrame
                return trace_df
        return None


    def get_traces(self, start_date, end_date):
        """
        Loop through generated URLs to fetch trace data.
        Returns a concatenated DataFrame of all valid traces.
        """
        urls = self.generate_urls(start_date, end_date)
        traces = []
        for url, icao in urls:
            trace_df = self.fetch_trace_data(url, icao)
            if trace_df is not None and not trace_df.empty:
                traces.append(trace_df)
                # Print a friendly message using the first timestamp
                ts = pd.to_datetime(trace_df["timestamp"].iloc[0]).strftime('%b %-d, %Y')
                print(f"Yay! {icao} flew on {ts}.")
            else:
                print(f"No data for {icao} on {url}.")
        if traces:
            return pd.concat(traces).reset_index(drop=True).sort_values("timestamp")
        else:
            print("No valid trace data collected.")
            return pd.DataFrame()

    def process_flight_data(self, df, mapping_info=None):
        """
        Process the raw trace data:
        - Compute point_time (UTC) and convert to US/Pacific.
        - Detect flight leg changes by looking at time gaps.
        - Normalize JSON details into columns.
        - Optionally map a flight column to additional info (like owner).
        - Create a combined flight_leg column.
        - Return a GeoDataFrame.
        
        mapping_info: tuple(meta_df, key_col, value_col, target_col) for mapping.
        """
        # First sort and compute the continuous ping time
        df = df.sort_values(['timestamp', 'time'])
        df["point_time"] = df["timestamp"] + pd.to_timedelta(df["time"], unit="s")
        df["timestamp_pst"] = df["point_time"].dt.tz_localize("UTC").dt.tz_convert("US/Pacific")
        df["point_time_pst_clean"] = df["timestamp_pst"].dt.strftime("%H:%M:%S")
        df["flight_date_pst"] = df["timestamp_pst"].dt.strftime("%Y-%m-%d")
        
        # --- Begin leg detection ---
        # Re-sort by aircraft and continuous time so that each group is in order
        df = df.sort_values(['icao', 'point_time'])
        # Compute the difference between successive pings within each aircraft and day
        df['time_diff'] = df.groupby(['icao', 'flight_date_pst'])['point_time'].diff()
        # Define a threshold for a new leg – here we use 15 minutes
        threshold = pd.Timedelta(minutes=15)
        # Flag rows where the gap exceeds the threshold (the first row in each group will be NaT, so fill it with 0)
        df['new_leg'] = (df['time_diff'] > threshold).fillna(0).astype(int)
        # Create a leg id that increments each time a new leg is detected, starting at 1
        df['leg_id'] = df.groupby(['icao', 'flight_date_pst'])['new_leg'].cumsum() + 1
        # --- End leg detection ---
        
        # Extract the call sign from the 'details' column and fill forward missing values
        df["call_sign"] = pd.json_normalize(df['details'])['flight'].str.strip()
        df["call_sign"] = df["call_sign"].ffill()
        
        # Create a combined flight_leg field: call_sign + date + leg_id
        df["flight_leg"] = df["call_sign"] + "_" + df["flight_date_pst"] + "_leg" + df["leg_id"].astype(str)
        
        # Flatten the 'details' JSON column (drop alt_geom if present)
        details_df = pd.json_normalize(df["details"]).drop(columns=["alt_geom"], errors='ignore')
        df = df.join(details_df)
        
        # Optionally apply a mapping (e.g. flight -> owner) if mapping_info is provided
        if mapping_info and "flight" in df.columns:
            meta_df, key_col, value_col, target_col = mapping_info
            mapping = meta_df.set_index(key_col)[value_col].to_dict()
            df[target_col] = df["flight"].map(mapping)
        
        # Select a common set of columns; add the mapped column if available.
        cols = ["flight", "flight_date_pst", "point_time_pst_clean", "altitude",
                "ground_speed", "heading", "lat", "lon", "icao", "call_sign", "leg_id", "flight_leg"]
        if mapping_info:
            cols.append(target_col)
        # Only keep rows where altitude is not "ground"
        flights = df[cols].query('altitude != "ground"').copy()
        
        # Create and return a GeoDataFrame with points from lon/lat
        return gpd.GeoDataFrame(flights, geometry=gpd.points_from_xy(flights.lon, flights.lat))



    def upload_to_s3(self, gdf, bucket_name, csv_object_name, geojson_object_name):
        """Upload the GeoDataFrame as both CSV and GeoJSON to S3 (if configured)."""
        if not self.s3_client:
            print("S3 client not configured; skipping upload.")
            return
        
        # Save CSV in memory and upload
        csv_buffer = BytesIO()
        gdf.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        self.s3_client.put_object(Bucket=bucket_name, Key=csv_object_name, Body=csv_buffer.getvalue())
        print(f"CSV uploaded to s3://{bucket_name}/{csv_object_name}")

        # Convert GeoDataFrame to GeoJSON string and upload
        geojson_str = gdf.to_json()
        self.s3_client.put_object(
            Bucket=bucket_name, 
            Key=geojson_object_name, 
            Body=geojson_str.encode('utf-8')
        )
        print(f"GeoJSON uploaded to s3://{bucket_name}/{geojson_object_name}")