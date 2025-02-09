import click
import os
import geopandas as gpd
from datetime import date
from flight_tracer import FlightTracer

@click.group()
def cli():
    """FlightTracer: Fetch, process, and analyze ADS-B Exchange flight data."""
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
    filename = f"{output}/raw_{icao}_{start.date()}_{end.date()}.csv"
    raw_df.to_csv(filename, index=False)
    click.echo(f"Saved raw data to {filename}")

@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to raw flight data CSV')
@click.option('--filter-ground', is_flag=True, help='Exclude ground data from processing')
def process(input, filter_ground):
    """Process raw flight data into structured GeoDataFrame."""
    raw_df = gpd.read_file(input)
    tracer = FlightTracer()
    gdf = tracer.process_flight_data(raw_df, filter_ground=filter_ground)
    
    processed_filename = input.replace("raw_", "processed_")
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
        gdf.to_csv(f"{base_path}.csv", index=False)
    elif format == 'geojson':
        gdf.to_file(f"{base_path}.geojson", driver="GeoJSON")
    elif format == 'shp':
        gdf.to_file(f"{base_path}.shp", driver="ESRI Shapefile")
    
    click.echo(f"Exported data as {base_path}.{format}")

@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to processed flight data')
@click.option('--bucket', required=True, help='AWS S3 bucket name')
def upload(input, bucket):
    """Upload processed data to AWS S3."""
    tracer = FlightTracer()
    file_name = os.path.basename(input)
    tracer.upload_to_s3(gpd.read_file(input), bucket, f"flight_tracer/{file_name}", f"flight_tracer/{file_name}.geojson")
    click.echo(f"Uploaded {file_name} to S3 bucket {bucket}")

@click.command()
@click.option('--input', required=True, type=click.Path(exists=True), help='Path to processed flight data')
@click.option('--output', required=True, type=click.Path(), help='Output image file for the plot')
def plot(input, output):
    """Plot flight paths with a basemap."""
    gdf = gpd.read_file(input)
    tracer = FlightTracer()
    tracer.plot_flights(gdf, geometry_type='points', fig_filename=output)
    click.echo(f"Saved flight map as {output}")

cli.add_command(fetch)
cli.add_command(process)
cli.add_command(export)
cli.add_command(upload)
cli.add_command(plot)

if __name__ == "__main__":
    cli()
