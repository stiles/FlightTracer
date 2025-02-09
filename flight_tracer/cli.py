import click
import os
import pandas as pd
import geopandas as gpd
from datetime import date
from flight_tracer import FlightTracer

@click.group()
def cli():
    """FlightTracer: Fetch, process, store and plot ADS-B Exchange flight data."""
    pass

@click.command()
@click.option('--icao', required=True, help='ICAO code of the aircraft')
@click.option('--start', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
@click.option('--output', default='data/', help='Directory to save raw data')
def fetch(icao, start, end, output):
    """Fetch raw flight trace data from ADS-B Exchange."""
    tracer = FlightTracer(aircraft_ids=[icao])
    raw_df = tracer.get_traces(start.date(), end.date())
    
    if raw_df.empty:
        click.echo("No flight data found.")
        return
    
    os.makedirs(output, exist_ok=True)
    filename = os.path.join(output, f"raw_{icao}_{start.date()}_{end.date()}.csv")
    raw_df.to_csv(filename, index=False)
    click.echo(f"Saved raw data to {filename}")

@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to raw flight data CSV')
@click.option('--filter-ground', is_flag=True, help='Exclude ground data from processing')
def process(input, filter_ground):
    """Process raw flight data into structured GeoDataFrame."""
    raw_df = pd.read_csv(input)
    if raw_df.empty or "icao" not in raw_df.columns:
        click.echo("Error: Invalid flight data. Ensure the CSV contains valid flight traces.")
        return
    
    gdf = FlightTracer.process_flight_data(None, raw_df, filter_ground=filter_ground)

    processed_filename = input.replace("raw_", "processed_").replace(".csv", ".geojson")
    gdf.to_file(processed_filename, driver="GeoJSON")
    click.echo(f"Processed data saved as {processed_filename}")


@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to processed flight data')
@click.option('--format', type=click.Choice(['csv', 'geojson', 'shp']), default='geojson', help='Output format')
def export(input, format):
    """Export processed data in different formats."""
    gdf = gpd.read_file(input)
    base_path = input.replace("processed_", "exported_").rsplit('.', 1)[0]
    
    if format == 'csv':
        output_file = f"{base_path}.csv"
        gdf.drop(columns='geometry', errors='ignore').to_csv(output_file, index=False)
    elif format == 'geojson':
        output_file = f"{base_path}.geojson"
        gdf.to_file(output_file, driver="GeoJSON")
    elif format == 'shp':
        output_file = f"{base_path}.shp"
        gdf["point_time"] = gdf["point_time"].dt.date
        gdf["flight_date_pst"] = gdf["flight_date_pst"].dt.date
        gdf = gdf.rename(columns={"flight_date_pst": "fl_dt_pst", "ground_speed": "speed"})
        gdf.to_file(output_file, driver="ESRI Shapefile")
    
    click.echo(f"Exported data as {output_file}")

@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to processed flight data')
@click.option('--bucket', required=True, help='AWS S3 bucket name')
@click.option('--aws-profile', default=None, help='AWS profile name for authentication')
def upload(input, bucket, aws_profile):
    """Upload processed data to AWS S3 with an optional AWS profile."""
    gdf = gpd.read_file(input)  # Load processed GeoDataFrame
    file_name = os.path.basename(input)

    from flight_tracer.core import FlightTracer  # Import inside function

    # Instead of requiring aircraft_ids, initialize for S3 only
    tracer = FlightTracer(aircraft_ids=["dummy"], aws_profile=aws_profile)  # Pass a dummy value

    if tracer.s3_client is None:
        click.echo("Error: AWS S3 client not initialized. Check your credentials or profile.")
        return

    tracer.upload_to_s3(gdf, bucket, f"flight_tracer/{file_name}", f"flight_tracer/{file_name}.geojson")

    click.echo(f"Uploaded {file_name} to S3 bucket {bucket} (AWS profile: {aws_profile if aws_profile else 'default'})")




@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to processed flight data')
@click.option('--output', required=True, type=click.Path(), help='Output image file for the plot')
def plot(input, output):
    """Plot flight paths with a basemap."""
    gdf = gpd.read_file(input)  # Load processed data

    from flight_tracer.core import FlightTracer  # Import inside function
    FlightTracer.plot_flights(None, gdf, geometry_type='points', fig_filename=output)

    click.echo(f"Saved flight map as {output}")




# Register commands
cli.add_command(fetch)
cli.add_command(process)
cli.add_command(export)
cli.add_command(upload)
cli.add_command(plot)

if __name__ == "__main__":
    cli()