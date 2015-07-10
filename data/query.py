#!/usr/bin/env python

import os
import sys
import numpy
from pprint import pprint
import argparse
from affine import Affine
import rasterio
from rasterio.warp import reproject, RESAMPLING, transform

def corners_from_shape(shape):
    return [(0,0), (0, shape[0]), (shape[1], shape[0]), (shape[1], 0)]

def get_corners(src_crs, affine, shape, dst_crs):
    corners = [affine * p for p in corners_from_shape(shape)]
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
parser.add_argument('--output', '-o')

argv = parser.parse_args()

query = {}
query_crs = None
query_pixel = None
xs = []
ys = []

with rasterio.open(argv.data[0]) as data:
    data_crs = data.crs
    data_affine = data.affine

    # for each file in the list of 'query' files, pull out the projection
    # metadata and save the corner coordinates, but transformed into the
    # *data*'s pixel coordinate space
    # Reason: we need bounds in the pixel coord space so we can choose a
    # window for the windowed read (the data is too huge to read the whole
    # thing).
    print('Reading query files.')
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

            pixel = src.affine[0], src.affine[4]
            if query_pixel:
                assert(query_pixel == pixel) 
            if query_crs:
                assert(query_crs['init'] == src.crs['init'])

            query_crs = src.crs
            query_pixel = pixel

    print('Reading data.')
    # these are in the data's pixel space
    ul = (min(xs), min(ys))
    lr = (max(xs), max(ys))
    window = ((ul[1], lr[1]), (ul[0], lr[0]))
    orig_cover = data.read(1, window=window)
    data_affine = data_affine * Affine.translation(ul[0], ul[1])


# reproject landcover data into query-rectangles' projection
print('Reprojecting landcover data.')

# project the corners into the target crs, and use the min/max x and y
# to determine an appropriately sized array to receive the reprojection
crn = get_corners(data_crs, data_affine, orig_cover.shape, query_crs)
newshape = ( (max(crn[1]) - min(crn[1])) / abs(query_pixel[1]),
             (max(crn[0]) - min(crn[0])) / abs(query_pixel[0]) )
# pixel (0,0) --> projection minX, maxY
dst_transform = Affine(query_pixel[0], 0.0, min(crn[0]),
                    0.0, query_pixel[1], max(crn[1]))
cover = numpy.empty(newshape, dtype=numpy.uint8)

reproject(orig_cover, cover, src_transform=data_affine, src_crs=data_crs,
        dst_transform=dst_transform,
        dst_crs=query_crs, resampling=RESAMPLING.mode)

# now that the target data is in the same projection as the query patches,
# grab the rectangle corresponding to each patch and write it to a file
for filename in query:
    patch = query[filename]
    #band = numpy.zeros(patch['shape'], dtype=rasterio.uint8)
    box = corners_from_shape(patch['shape'])
    box = [patch['affine'] * c for c in box]
    box = [~dst_transform * c for c in box]
    rows = min([b[1] for b in box]), max([b[1] for b in box])
    cols = min([b[0] for b in box]), max([b[0] for b in box])
    band = cover[rows[0]:rows[1], cols[0]:cols[1]]

    filename = os.path.basename(filename).replace('TIF', 'labels.TIF')
    filename = os.path.join(argv.output, filename)
    print('Writing ' + filename)
    with rasterio.open(filename, mode='w',
            driver='GTiff',
            width=band.shape[1],
            height=band.shape[0],
            count=1,
            dtype=rasterio.uint8,
            nodata=0,
            transform=patch['affine'],
            crs=query_crs) as dst:
        dst.write_band(1, band)

