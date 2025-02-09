from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="flight-tracer",
    version="0.1.5",
    author="Matt Stiles",
    author_email="mattstiles@gmail.com",
    description="A package to fetch, process, store and plot aircraft trace data from ADS-B Exchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stiles/flight-tracer",
    packages=find_packages(include=["flight_tracer", "flight_tracer.*"]),
    install_requires=[
        "requests",
        "pandas",
        "geopandas",
        "boto3",
        "matplotlib",
        "contextily",
        "shapely",
        "click"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    license="CC0-1.0",
    python_requires=">=3.7",
    entry_points={
    "console_scripts": [
        "flight-tracer=flight_tracer.cli:cli",
    ],
},
)
