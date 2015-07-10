#!/usr/bin/env python

import os
import sys
import numpy
from pprint import pprint
import argparse
from affine import Affine
import rasterio
from rasterio.warp import reproject, RESAMPLING, transform

def get_corners(src_crs, affine, shape, dst_crs):
    corners = [(0,0), (0, shape[0]), (shape[1], shape[0]), (shape[1], 0)]
    corners = [affine * p for p in corners]
    return transform(src_crs, dst_crs,
            [p[0] for p in corners],
            [p[1] for p in corners])

def project_query(src_crs, affine, shape, dst_crs, dst_affine):
    corners = get_corners(src_crs, affine, shape, dst_crs)
    corners = zip(corners[0], corners[1])
    corners = [ ~dst_affine * (c[0], c[1]) for c in corners ]
    return corners

parser = argparse.ArgumentParser()
parser.add_argument('data', metavar='data.TIF', type=str, nargs=1)
parser.add_argument('--query', metavar='query.TIF', type=str, nargs='+', required=True)

argv = parser.parse_args()

query = {}
query_crs = None
xs = []
ys = []

with rasterio.open(argv.data[0]) as data:
    data_crs = data.crs
    data_affine = data.affine

    for f in argv.query:
        with rasterio.open(f) as src:
            query[f] = {
                'affine': src.affine,
                'shape': src.shape,
                'crs': src.crs
            }

            crn = project_query(src.crs, src.affine, src.shape,
                    data_crs, data_affine)

            xs.extend([c[0] for c in crn])
            ys.extend([c[1] for c in crn])

            if query_crs:
                assert(query_crs['init'] == src.crs['init'])

            query_crs = src.crs

    ul = (min(xs), min(ys))
    lr = (max(xs), max(ys))
    window = ((ul[1], lr[1]), (ul[0], lr[0]))
    orig_cover = data.read(1, window=window)
    data_affine = data_affine * Affine.translation(ul[0], ul[1])

with rasterio.open('test-extraction.tif', mode='w',
        driver='GTiff',
        width=orig_cover.shape[1],
        height=orig_cover.shape[0],
        count=1,
        dtype=numpy.uint8,
        nodata=0,
        transform=data_affine * Affine.translation(ul[0], ul[1]),
        crs=data_crs) as dst:

    dst.write_band(1, orig_cover)

# reproject landcover data into query-rectangles' projection
crn = get_corners(data_crs, data_affine,
        orig_cover.shape, query_crs)

ypx = abs(max(crn[1]) - min(crn[1])) / orig_cover.shape[0]
xpx = abs(max(crn[0]) - min(crn[0])) / orig_cover.shape[1]
dst_transform = (xpx, 0.0, min(crn[0]), 0.0, -ypx, max(crn[1]))
cover = numpy.empty(orig_cover.shape, dtype=numpy.uint8)
print('Reprojecting landcover data.')
print(dst_transform)

reproject(orig_cover, cover, src_transform=data_affine, src_crs=data_crs,
        dst_transform=dst_transform,
        dst_crs=query_crs, resampling=RESAMPLING.mode)

with rasterio.open('test-reprojection.tif', mode='w',
        driver='GTiff',
        width=cover.shape[1],
        height=cover.shape[0],
        count=1,
        dtype=numpy.uint8,
        nodata=0,
        transform=Affine(*dst_transform),
        crs=query_crs) as dst:

    dst.write_band(1, cover)

# now that the target data is in the same projection as the query patches,
# we just need to grab the right rectangle for each patch and run whatever
# stats we want on it.


