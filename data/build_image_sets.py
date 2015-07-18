#!/usr/bin/env python
from subprocess import call

cmd = './data/create-image-sets.sh'
# call([cmd, 'images/val.txt', 'images/val/', 'temp/learnsat-val-lmdb'])
# call([cmd, 'images/train.txt', 'images/train/', 'temp/learnsat-train-lmdb'])

with open('images/train.txt') as f:
    full_training = f.readlines()
labels = [l.replace('.TIF', '.labels.TIF') for l in full_training]

subsets = [512, 1024, 2048, 4096, 6144, 8192, 10240]
for size in subsets:
    subset_file = 'temp/train-' + str(size) + '.txt'
    with open(subset_file, mode='w') as f:
        f.writelines(full_training[:size])
    dbname = 'temp/learnsat-subset-' + str(size) + '-train-lmdb'
    call([cmd, subset_file, 'images/train/', dbname])
    labels_file = 'temp/train-' + str(size) + '-labels.txt'
    with open(labels_file, mode='w') as f:
        f.writelines(labels[:size])
    call([
        './data/build_label_set.py', '--output',
        'temp/classify/train-' + str(size) + '-labels-lmdb',
        '--image-list', labels_file,
        '--image-root', 'images/labels',
        '--size', '128'
        ])
