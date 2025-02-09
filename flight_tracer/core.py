# flight_tracer/core.py
import requests
import pandas as pd
import geopandas as gpd
import boto3
import os
import pytz
from datetime import date, timedelta
from io import BytesIO
from shapely.geometry import LineString
import matplotlib.pyplot as plt
import contextily as ctx
import matplotlib.cm as cm
import matplotlib.colors as mcolors

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Column names longer than 10 characters")

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

    def generate_urls(self, start_date, end_date, recent=False):
        """Generate ADSBExchange URLs for each aircraft.
        
        Parameters:
        - start_date (date): Start of the date range.
        - end_date (date): End of the date range.
        - recent (bool): If True, fetches only the most recent trace.

        Returns:
        - List of tuples (url, icao)
        """
        base_url_recent = "https://globe.adsbexchange.com/data/traces/"
        base_url_historical = "https://globe.adsbexchange.com/globe_history/"
        
        urls = []
        for icao in self.aircraft_ids:
            icao_suffix = icao[-2:]

            if recent:
                # Use the single, fixed "recent" URL
                url = f"{base_url_recent}{icao_suffix}/trace_full_{icao}.json"
                urls.append((url, icao))
            else:
                # Generate historical URLs with date structure
                delta = timedelta(days=1)
                current_date = start_date
                while current_date <= end_date:
                    year = current_date.strftime("%Y")
                    month = current_date.strftime("%m")
                    day = current_date.strftime("%d")
                    url = f"{base_url_historical}{year}/{month}/{day}/traces/{icao_suffix}/trace_full_{icao}.json"
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


    def get_traces(self, start_date=None, end_date=None, recent=False):
        """
        Fetch trace data from ADSBExchange.

        Parameters:
        - start_date (date or None): Start date for fetching data. Ignored if recent=True.
        - end_date (date or None): End date for fetching data. Ignored if recent=True.
        - recent (bool): If True, fetches the most recent trace instead of historical data.

        Returns:
        - DataFrame containing all collected flight traces.
        """
        urls = self.generate_urls(start_date, end_date, recent=recent)
        traces = []
        
        for url, icao in urls:
            print(f"Fetching data from: {url}")
            trace_df = self.fetch_trace_data(url, icao)
            
            if trace_df is not None and not trace_df.empty:
                traces.append(trace_df)
                ts = pd.to_datetime(trace_df["timestamp"].iloc[0]).strftime('%b %-d, %Y')
                print(f"✅ Data found for {icao}.")
            else:
                print(f"❌ No data for {icao} on {url}.")
        
        if traces:
            return pd.concat(traces).reset_index(drop=True).sort_values("timestamp")
        else:
            print("No valid trace data collected.")
            return pd.DataFrame()



    def process_flight_data(self, df, mapping_info=None, filter_ground=True, threshold_seconds=3600, timezone=None):
        df = df.sort_values(['icao', 'timestamp', 'time'])
        df["time"] = pd.to_numeric(df["time"], errors="coerce")
        df = df.dropna(subset=["time"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["point_time"] = df["timestamp"] + pd.to_timedelta(df["time"], unit="s")
        
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                df["point_time_local"] = df["point_time"].dt.tz_localize("UTC").dt.tz_convert(tz)
            except Exception as e:
                raise ValueError(f"Invalid timezone specified: {e}")
        
        if "details" in df.columns:
            details_df = pd.json_normalize(df["details"], errors="ignore")
            if "flight" in details_df.columns:
                df["call_sign"] = details_df["flight"].str.strip().ffill().fillna("UNKNOWN")
            else:
                df["call_sign"] = "UNKNOWN"
            overlapping_cols = details_df.columns.intersection(df.columns).tolist()
            details_df = details_df.drop(columns=overlapping_cols, errors="ignore")
            df = df.drop(columns=["details"]).join(details_df, how="left")
        else:
            df["call_sign"] = "UNKNOWN"

        df["time_diff"] = df.groupby(["icao", "call_sign"])["point_time"].diff().dt.total_seconds()
        df["new_leg"] = (df["time_diff"] > threshold_seconds).astype(int)
        df["leg_id"] = df.groupby(["icao", "call_sign"])["new_leg"].cumsum() + 1
        df["flight_leg"] = df["call_sign"].fillna("UNKNOWN") + "_leg" + df["leg_id"].astype(str)
        
        if filter_ground:
            df = df.query('altitude != "ground"').copy()
        
        output_columns = [
            "point_time", "altitude", "ground_speed", "heading", "lat", "lon",
            "icao", "call_sign", "leg_id", "flight_leg"
        ]
        if "point_time_local" in df.columns:
            output_columns.append("point_time_local")
        
        return gpd.GeoDataFrame(
            df[output_columns],
            geometry=gpd.points_from_xy(df.lon, df.lat)
        ).set_crs(epsg=4326)


    
    def create_linestrings(self, gdf, flight_leg_column="flight_leg", point_time_column="point_time"):
        """
        Given a GeoDataFrame of flight trace points, group the data by flight_leg,
        create a LineString for each leg, and return a new GeoDataFrame.

        Parameters:
        gdf (GeoDataFrame): The GeoDataFrame of flight points.
        flight_leg_column (str): The name of the flight leg column (default: "flight_leg").
        point_time_column (str): The name of the time column (default: "point_time").

        Returns:
        GeoDataFrame: Processed flight leg lines.
        """
        if flight_leg_column not in gdf.columns:
            raise KeyError(f"Expected column '{flight_leg_column}' not found in DataFrame.")

        if point_time_column not in gdf.columns:
            raise KeyError(f"Expected column '{point_time_column}' not found in DataFrame.")

        legs = []
        for flight_leg, group in gdf.groupby(flight_leg_column):
            group = group.sort_values(point_time_column)  # Ensure chronological order
            points = list(group.geometry)
            geometry = LineString(points) if len(points) > 1 else points[0]

            # Handle missing columns
            row_data = {
                flight_leg_column: flight_leg,
                "icao": group["icao"].iloc[0] if "icao" in group.columns else None,
                "call_sign": group["call_sign"].iloc[0] if "call_sign" in group.columns else None,
                "flight_date_pst": group["flight_date_pst"].iloc[0] if "flight_date_pst" in group.columns else None,
                "leg_id": group["leg_id"].iloc[0] if "leg_id" in group.columns else None,
                "geometry": geometry
            }

            legs.append(row_data)

        gdf_lines = gpd.GeoDataFrame(legs, crs=gdf.crs)
        return gdf_lines






    def export_flight_data(self, gdf, base_path, export_format="geojson"):
        """
        Export flight data as GeoJSON or Shapefile.

        Parameters:
        gdf (GeoDataFrame): The GeoDataFrame of flight points.
        base_path (str): The base path for saving the files.
        export_format (str): Either "geojson" (default) or "shp".
        """
        if export_format == "geojson":
            point_file = f"{base_path}_points.geojson"
            line_file = f"{base_path}_lines.geojson"
            gdf.to_file(point_file, driver="GeoJSON")
            print(f"GeoJSON exported: {point_file}")

            gdf_lines = self.create_linestrings(gdf, flight_leg_column="flight_leg")
            gdf_lines.to_file(line_file, driver="GeoJSON")
            print(f"GeoJSON exported: {line_file}")

        elif export_format == "shp":
            shp_dir = f"{base_path}_shp"
            os.makedirs(shp_dir, exist_ok=True)

            point_file = f"{shp_dir}/flight_traces_points.shp"
            line_file = f"{shp_dir}/flight_traces_lines.shp"

            # Define a column renaming map for Shapefile (ensuring `point_time` is included)
            shapefile_col_map = {
                "flight_leg": "fl_leg",
                "point_time": "pt_time",
                "timestamp_pst": "tm_pst",
                "flight_date_pst": "fl_date",
                "ground_speed": "gr_speed",
                "icao": "icao",
                "call_sign": "c_sign",
                "altitude": "alt",
                "heading": "head",
                "lat": "lat",
                "lon": "lon",
                "leg_id": "leg_id"
            }

            # Rename columns only if they exist
            gdf = gdf.rename(columns={k: v for k, v in shapefile_col_map.items() if k in gdf.columns})

            # Convert datetime columns to strings (Shapefile doesn't support datetime)
            datetime_cols = ["pt_time", "tm_pst", "fl_date"]
            for col in datetime_cols:
                if col in gdf.columns:
                    gdf[col] = gdf[col].astype(str)

            gdf.to_file(point_file, driver="ESRI Shapefile")
            print(f"Shapefile exported: {point_file}")

            # Use the correct column name for grouping in create_linestrings()
            flight_leg_column = "flight_leg" if "flight_leg" in gdf.columns else "fl_leg"
            point_time_column = "point_time" if "point_time" in gdf.columns else "pt_time"

            # Process LineStrings using the correct column
            gdf_lines = self.create_linestrings(gdf, flight_leg_column, point_time_column)
            gdf_lines.to_file(line_file, driver="ESRI Shapefile")
            print(f"Shapefile exported: {line_file}")

        else:
            raise ValueError("Unsupported export format. Use 'geojson' or 'shp'.")




    def plot_flights(self, gdf, geometry_type='points', figsize=(10,10), pad_factor=0.2, zoom=None, fig_filename=None):
        """
        Plot flight activity from a GeoDataFrame with a basemap, coloring different flight legs distinctly.
        
        Parameters:
        gdf (GeoDataFrame): The GeoDataFrame containing flight trace points or lines.
        geometry_type (str): 'points' or 'lines' – determines what geometry to plot.
        figsize (tuple): Figure size for the plot.
        pad_factor (float): Fraction by which to expand the bounds for additional context.
        zoom (int or None): Optional zoom level override for the basemap.
        fig_filename (str or None): If provided, the plot will be saved to this PNG file.
        """
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        gdf_plot = gdf.to_crs(epsg=3857)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        unique_legs = gdf_plot["flight_leg"].unique()
        cmap = plt.get_cmap("tab10", len(unique_legs))
        norm = mcolors.Normalize(vmin=0, vmax=len(unique_legs))
        colors = {leg: cmap(norm(i)) for i, leg in enumerate(unique_legs)}
        
        if geometry_type == 'points':
            for leg, group in gdf_plot.groupby("flight_leg"):
                group.plot(ax=ax, marker='o', color=colors[leg], markersize=5, label=leg)
        elif geometry_type == 'lines':
            for leg, group in gdf_plot.groupby("flight_leg"):
                group.plot(ax=ax, linewidth=2, color=colors[leg], label=leg)
        else:
            raise ValueError("geometry_type must be either 'points' or 'lines'")
        
        xmin, ymin, xmax, ymax = gdf_plot.total_bounds
        x_pad = (xmax - xmin) * pad_factor
        y_pad = (ymax - ymin) * pad_factor
        extent = [xmin - x_pad, ymin - y_pad, xmax + x_pad, ymax + y_pad]
        
        ax.set_xlim(extent[0], extent[2])
        ax.set_ylim(extent[1], extent[3])
        
        if zoom is not None:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=zoom, reset_extent=False)
        else:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, reset_extent=False)
        
        ax.set_axis_off()
        ax.legend()
        plt.tight_layout()
        plt.title("Flight sketch")
        
        if fig_filename:
            os.makedirs(os.path.dirname(fig_filename), exist_ok=True)
            plt.savefig(fig_filename, dpi=300, bbox_inches='tight')
            print(f"Figure saved as {fig_filename}")
        
        plt.show()


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
        print(f"✅ CSV uploaded to s3://{bucket_name}/{csv_object_name}")
        
        # Convert timestamp columns to ISO 8601 strings for JSON serialization
        gdf_json = gdf.copy()
        for col in gdf_json.select_dtypes(include=["datetime64"]).columns:
            gdf_json[col] = gdf_json[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Drop non-serializable columns before exporting to GeoJSON
        geojson_str = gdf_json.to_json()
        
        self.s3_client.put_object(
            Bucket=bucket_name, 
            Key=geojson_object_name, 
            Body=geojson_str.encode('utf-8')
        )
        print(f"✅ GeoJSON uploaded to s3://{bucket_name}/{geojson_object_name}")