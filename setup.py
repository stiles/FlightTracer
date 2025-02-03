from setuptools import setup, find_packages

setup(
    name="flight_tracer",
    version="0.1.0",
    author="Matt Stiles",
    author_email="mattstiles@gmail.com",
    description="A package to fetch, process, store and plot aircraft trace data from ADS-B Exchange.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/stiles/flight_tracer",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "geopandas",
        "boto3",
        "matplotlib",
        "contextily",
        "shapely"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
    ],
    license="CC0-1.0",
    python_requires='>=3.7',
)
