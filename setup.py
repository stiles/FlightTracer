from setuptools import setup, find_packages

setup(
    name="flight_tracer",
    version="0.1.0",
    author="Your Name",
    author_email="you@example.com",
    description="A package to fetch and process flight trace data from ADS-B Exchange.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/flight_tracer",  # update with your repo URL
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
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)