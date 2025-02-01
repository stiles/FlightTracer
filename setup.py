# setup.py
from setuptools import setup, find_packages

setup(
    name="FlightTracer",
    version="0.1.0",
    author="Matt Stiles",
    author_email="matt.stiles@gmail.com",
    description="A Python package to fetch and process flight historical and current aircraft trace data from ADS-B Exchange.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/stiles/FlightTracer",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "geopandas",
        "boto3"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
