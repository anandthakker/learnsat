#!/usr/bin/env python

from os import path
import rasterio
import numpy
from scipy import stats
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('data', metavar='data.TIF', type=str, nargs='+')
parser.add_argument('--labels', '-l')

argv = parser.parse_args()

classes = {
    11: 'Open Water',
    12: 'Perennial Ice/Snow',
    21: 'Developed, Open Space',
    22: 'Developed, Low Intensity',
    23: 'Developed, Medium Intensity',
    24: 'Developed High Intensity',
    31: 'Barren Land (Rock/Sand/Clay)',
    41: 'Deciduous Forest',
    42: 'Evergreen Forest',
    43: 'Mixed Forest',
    51: 'Dwarf Scrub',
    52: 'Shrub/Scrub',
    71: 'Grassland/Herbaceous',
    72: 'Sedge/Herbaceous',
    73: 'Lichens',
    74: 'Moss',
    81: 'Pasture/Hay',
    82: 'Cultivated Crops',
    90: 'Woody Wetlands',
    95: 'Emergent Herbaceous Wetlands'
}

def summarize(memo, val):
    count, total = memo
    if 21 <= val <= 24:
        count = count + 1
    if val in classes:
        total = total + 1

    return count, total


for f in argv.data:
    lf = path.basename(f).replace('.TIF', '.labels.TIF')
    lf = path.join(argv.labels, lf)
    if not path.exists(lf):
        continue

    with rasterio.open(lf) as src:
        band = src.read(1)

    count, total = reduce(summarize, numpy.ndarray.flatten(band), (0, 0))
    mode = stats.mode(band, axis=None)[0][0]

    if total == 0:
        continue

    if float(count)/total > .1:
        label = 1
    else:
        label = 0

    print(path.abspath(f) + ' ' + str(mode))
