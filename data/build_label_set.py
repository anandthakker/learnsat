#!/usr/bin/env python
from __future__ import print_function
import rasterio
import os
import sys
import lmdb
import caffe
import numpy
import skimage.io
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output')
parser.add_argument('--image-list')
parser.add_argument('--image-root')
parser.add_argument('--size', type=int, default=128)
parser.add_argument('--class-list-only', type=bool, nargs='?',
                    const=True, default=False)

args = parser.parse_args()

classes = {
    0: 'No Data',
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
print('label,description')
for i, c in enumerate(sorted(classes.keys())):
    labels[c] = i
    print(str(i) + ',' + classes[c].replace(',', ';'))

if args.class_list_only:
    sys.exit()

with open(args.image_list) as f:
    inputs = f.readlines()


def relabel(image, size=1):
    shape = (image.shape[0] / size, image.shape[1] / size)
    new_image = numpy.zeros((len(labels), shape[0], shape[1]))
    for i, j in numpy.ndindex(shape):
        patch_labels = {}
        total = 0.0
        for l in image[i * size: (i + 1) * size,
                       j * size: (j + 1) * size].flatten():
            total = total + 1.0
            if l in labels:
                patch_labels[labels[l]] = patch_labels.get(labels[l], 0) + 1.0

        for label in patch_labels:
            new_image[label, i, j] = patch_labels[label] / total

    return new_image

# in_ = inputs[149]
# im_file = os.path.join(args.image_root, in_.split(' ')[0])
# im = relabel(skimage.io.imread(im_file), args.size)
# print(im)
# sys.exit()

# Refuse to overwrite existing
if os.path.isdir(args.output):
    print('Output directory ' + args.output + ' already exists.')
    sys.exit()

in_db = lmdb.open(args.output, map_size=int(1e12))
with in_db.begin(write=True) as in_txn:
    for in_idx, in_ in enumerate(inputs):
        if in_idx % 1000 == 0:
            print('Processed %s images.' % in_idx, file=sys.stderr)
        im_file = os.path.join(args.image_root, in_.split(' ')[0])
        if os.path.exists(im_file):
            im = skimage.io.imread(im_file)
        else:
            print('Missing: ' + im_file, file=sys.stderr)
            im = numpy.zeros((128, 128))

        im = relabel(im, args.size)
        im_dat = caffe.io.array_to_datum(im)
        in_txn.put('{:0>10d}'.format(in_idx), im_dat.SerializeToString())

in_db.close()
