#!/usr/bin/env python
from subprocess import call

cmd = './data/create-image-sets.sh'
call([cmd, 'temp/test.txt', 'images/test/', 'temp/learnsat-val-lmdb'])
call([cmd,'temp/test-labels.txt', 'images/labels/', 'temp/learnsat-val-labels-lmdb'])

call([cmd, 'temp/train.txt', 'images/train/', 'temp/learnsat-train-lmdb'])
call([cmd,'temp/train-labels.txt', 'images/labels/', 'temp/learnsat-train-labels-lmdb'])

subsets = [512, 1024, 2048, 4096, 6144, 8192, 10240]
