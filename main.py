#!/usr/bin/env python3
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
import pytest
import click
from fiona.errors import DriverError


sample_file = "test.geojson"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Create sample standalone polygons
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
        Polygon([(4, 0), (5, 0), (5, 1), (4, 1)]),
        Polygon([(6, 0), (7, 0), (7, 1), (6, 1)]),
        Polygon([(8, 0), (9, 0), (9, 1), (8, 1)]),
    ]

    # # Create sample intersecting polygons
    intersecting_polygons = [
        Polygon([(0, 2), (1, 2), (1, 3), (0, 3)]),
        Polygon([(0.5, 1.5), (1.5, 1.5), (1.5, 2.5), (0.5, 2.5)]),
        Polygon([(2, 2), (3, 2), (3, 3), (2, 3)]),
        Polygon([(2.5, 1.5), (3.5, 1.5), (3.5, 2.5), (2.5, 2.5)]),
        Polygon([(4, 2), (5, 2), (5, 3), (4, 3)]),
    ]

    # Create sample MultiPolygons
    multipolygons = [
        MultiPolygon([Point(6, 2).buffer(0.05), Point(6.05, 2).buffer(0.09)]),
        MultiPolygon([Point(8.5, 1.5).buffer(0.05),
                     Point(8.55, 1.5).buffer(0.09)]),
    ]

    # Create sample points
    points = [Point(0.5, 4), Point(3, 4), Point(
        6.5, 4), Point(9, 4), Point(4.5, 0.5)]

    # Create a sample GeoDataFrame
    geometry = polygons + intersecting_polygons + multipolygons + points
    gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:3857")

    # Save sample to file
    gdf.to_file(sample_file, driver="GeoJSON")

    yield

    # Remove sample file
    os.remove(sample_file)


# TODO: Task 1 - "Only Polygons"
#
# Sample GeoDataFrame consists of polygons, multipolygons and points.
#
# 1. Create a buffered points with radius equals to 0.01 meters
# 2. Explode MultiPolygons (it means that each MultiPolygon should be splitted into separate polygons)
#
# As result we need to get a GeoDataFrame with only polygons. Including polygons from sample GeoDataFrame and exploded MultiPolygons and buffered points.
# Imlement your code in test_task_one function
def test_task_one():

    sample_gdf = gpd.read_file(sample_file)
    processed_gdf: gpd.GeoDataFrame = None
    exp = sample_gdf.explode(index_parts=False, ignore_index=True)
    only_points = exp[exp.geometry.type == "Point"].buffer(0.01)
    # Rest of geometry types
    rest = exp[exp.geometry.type != "Point"]

    # Concatenate frames
    processed_gdf = pd.concat([rest.geometry, only_points.geometry])

    assert processed_gdf.geom_type.unique() == ["Polygon"]
    processed_gdf.to_file("./geojsons/task1.geojson", driver="GeoJSON")


intersection_pointers = {}
# TODO: Task 2 - "Intersections"
#
# Sample GeoDataFrame consists of polygons, multipolygons and points.
#
# 1. Find all intersections between geometries
#
# As result we need to get a GeoDataFrame with only intersected geometries.
# Imlement your code in test_task_two function


def test_task_two():

    gdf: gpd.GeoDataFrame = gpd.read_file(sample_file).explode(
        index_parts=False, ignore_index=True)
    intersections_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame()
    for i, row in gdf.itertuples():
        dist = enumerate(gdf.distance(row))
        for j, l in dist:
            if l == 0 and j != i:
                intersection_pointers[i] = []
                intersection_pointers[i].append(j)
                intersection = row.intersection(gdf.iloc[j]).to_frame().T
                intersections_gdf = pd.concat(
                    [intersections_gdf, intersection], axis=0, ignore_index=True)
    intersections_gdf = gpd.GeoDataFrame(
        geometry=intersections_gdf['geometry'], crs="EPSG:3857")
    assert len(intersections_gdf) == 10
    intersections_gdf.to_file("./geojsons/task2.geojson", driver="GeoJSON")


# TODO: Task 3 - "Intersections difference"
#
# Sample GeoDataFrame consists of polygons, multipolygons and points.
#
# 1. Find all intersections between geometries
# 2. Save difference between intersections
#
# As result we need to get a GeoDataFrame with only difference geometries.
# Imlement your code in test_task_three function


def test_task_three():

    # I used calculations from task 2 to save time and to keep code DRY
    gdf = gpd.read_file(sample_file).explode(
        index_parts=False, ignore_index=True)
    difference_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame()
    for i, j in intersection_pointers.items():
        for r in j:
            left = gpd.GeoSeries(gdf.iloc[i])
            right = gpd.GeoSeries(gdf.iloc[r])
            difference = left.difference(right).to_frame().T
            difference_gdf = pd.concat(
                [difference_gdf, difference], axis=0, ignore_index=True)
    assert len(difference_gdf) == 10
    difference_gdf = gpd.GeoDataFrame(
        geometry=difference_gdf['geometry'], crs="EPSG:3857")
    difference_gdf.to_file("./geojsons/task3.geojson", driver="GeoJSON")


@click.command()
@click.option(
    "--config-path",
    help="Path to config",
    required=False,
    default="test.geojson",
)
@click.option(
    "--output-path",
    help="Path to output",
    required=False,
    default="output.geojson",
)
def main(**kwargs):

    try:
        gdf = gpd.read_file(kwargs['config_path'])
    except DriverError:
        print('Invalid input file.')
        exit()
    rest = gdf[gdf.geometry.type == "Polygon"]
    rest.to_file(kwargs['output_path'], driver="GeoJSON")
    print("GeoDataFrame is written to ", kwargs['output_path'])


if __name__ == "__main__":
    main()
