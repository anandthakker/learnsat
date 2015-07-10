#!/usr/bin/env sh
# Compute the mean image from the imagenet training lmdb
# N.B. this is available in data/ilsvrc12

EXAMPLE=temp
DATA=temp
TOOLS=$CAFFE_ROOT/build/tools

$TOOLS/compute_image_mean $EXAMPLE/learnsat_train_lmdb \
  $DATA/imagenet_mean.binaryproto

echo "Done."