#!/usr/bin/env python

from os import path
import rasterio
import numpy
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

labels = {}

# caffe expects labels to be sequential, starting at 0
# https://groups.google.com/forum/#!msg/caffe-users/G_c3vTNjD_Y/3BOTn7T_uMQJ
for i, c in enumerate(classes):
    labels[c] = i

def summarize(memo, val):
    count, total = memo
    if val == 82:
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

    flatband = numpy.ndarray.flatten(band)
    count, total = reduce(summarize, flatband, (0, 0))
    # mode = numpy.bincount(flatband).argmax()

    if total == 0:
        continue
    
    label = 0
    if float(count)/total > 0.1:
        label=1
    print(path.basename(f) + ' ' + str(label))
