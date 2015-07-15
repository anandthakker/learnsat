#!/usr/bin/env sh

DATA=$1
IMAGES_ROOT=$2
OUTPUT=$3
RESIZE_WIDTH=${4:-0}
RESIZE_HEIGHT=${5:-0}

TOOLS=$CAFFE_ROOT/build/tools

usage() {
  echo "Usage: $0 training_data.txt path/to/images path/to/output_lmdb [resize_width=0] [resize_height=0]"
  exit 1
}

if [ ! -d "$CAFFE_ROOT" ]; then
  echo "Error: couldn't find Caffe tools at: $TOOLS"
  echo "Set CAFFE_ROOT to the root path of the Caffe repo."
  usage
fi

if [ ! -f "$DATA" ]; then
  echo "Error: $DATA not found."
  usage
fi

if [ ! -d "$IMAGES_ROOT" ]; then
  echo "Error: $IMAGES_ROOT is not a directory."
  usage
fi

OUT_DIR=`dirname $OUTPUT`
if [ ! -d "$OUT_DIR" ]; then
  echo "Error: $OUT_DIR is not a directory."
  usage
fi

if [ -e "$OUTPUT" ]; then
  echo "Error: $OUTPUT already exists."
  usage
fi

echo "Creating $OUTPUT..."

GLOG_logtostderr=1 $TOOLS/convert_imageset \
    --resize_height=$RESIZE_HEIGHT \
    --resize_width=$RESIZE_WIDTH \
    --shuffle \
    $IMAGES_ROOT \
    $DATA \
    $OUTPUT

IMAGE_MEAN=${OUTPUT%/}_mean.binaryproto
GLOG_logtostderr=1 $TOOLS/compute_image_mean $OUTPUT $IMAGE_MEAN

echo "Done."
