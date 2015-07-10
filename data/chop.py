#!/usr/bin/env python

from pprint import pprint
import argparse
import numpy
import rasterio
from rasterio.warp import reproject, RESAMPLING, transform
from affine import Affine

def read_band(band_file):
    with rasterio.open(band_file) as src:
        band = src.read()
        crn = get_corners(src.affine, src.crs, src.shape, projection)

        dst_shape = src.shape

        y_pixel = abs(max(crn[1]) - min(crn[1])) / dst_shape[0]
        x_pixel = abs(max(crn[0]) - min(crn[0])) / dst_shape[1]
        dst_transform = (x_pixel, 0.0, min(crn[0]),
                        0.0, -y_pixel, max(crn[1]))

    new_band = numpy.empty(src.shape, dtype=numpy.uint16)
    reproject(band, new_band, src_transform=src.affine, src_crs=src.crs,
            dst_transform=dst_transform, dst_crs=projection, resampling=RESAMPLING.nearest)

    return (new_band, dst_transform)

def chop(bands, dst_transform, size, output_file, photometric):
    for y in range(0, bands.shape[1], size):
        for x in range(0, bands.shape[2], size):

            # crop a grid square ('patch')
            patch_affine = Affine(*dst_transform) * Affine.translation(x, y)
            patch = numpy.zeros((bands.shape[0], size, size), dtype=rasterio.uint16)
            my = min(y + size, bands.shape[1])
            mx = min(x + size, bands.shape[2])
            for i, band in enumerate(bands):
                patch[i, 0:my-y, 0:mx-x] = band[y:my, x:mx]


            if(numpy.max(patch) > 0):
                out = output_file.replace('{x}', str(x)).replace('{y}', str(y))
                with rasterio.open(out,
                                    mode='w', driver='GTiff',
                                    width=patch.shape[2],
                                    height=patch.shape[1],
                                    count=patch.shape[0],
                                    dtype=numpy.uint8,
                                    nodata=0,
                                    photometric=photometric,
                                    transform=patch_affine,
                                    crs=projection) as dst:
                    for i, band in enumerate(patch):
                        dst.write_band(i + 1, band.astype(rasterio.uint8))


def get_corners(affine, src_crs, shape, dst_crs):
    corners = [(0,0), (0, shape[0]), (shape[1], shape[0]), (shape[1], 0)]
    corners = [affine * p for p in corners]
    return transform(src_crs, dst_crs, [p[0] for p in corners], [p[1] for p in corners])

parser = argparse.ArgumentParser()
parser.add_argument('file', metavar='FILE', type=str, nargs=1)
parser.add_argument('--output', '-o', required=True)
parser.add_argument('--size', '-s', default=256)
parser.add_argument('--bands', default='432')
parser.add_argument('--projection', default='epsg:3857')
parser.add_argument('--photometric', default='rgb')

args = parser.parse_args()

projection = {'init': args.projection}

# TODO: check for {band} and {x} {y} in the file template arguments

with rasterio.drivers(CPL_DEBUG=True):
    bands = []
    for band in args.bands:
        band_file = args.file[0].replace('{band}', band)
        print('Reading: ' + band_file)
        (band_data, dst_transform) = read_band(band_file)
        bands.append(band_data)

    print('Chopping...')
    chop(numpy.array(bands), dst_transform, int(args.size), args.output, args.photometric)

    print('Done!')

