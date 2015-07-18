## Prepping the data

```sh
export LANDSAT=${HOME}/landsat
export LANDCOVER=${HOME}/landcover
export TEST_SIZE=2500

# chop up the landsat images
mkdir -p images/train
ls ${LANDSAT} | grep "^L" | parallel ./data/chop.py --output images/train/{}.{x}.{y}.TIF --size 128 --bands 123 ${LANDSAT}/{}/{}_B{band}.TIF

# for each chopped piece, grab the corresponding patch of the landcover raster
mkdir -p images/labels
ls images/train | sed 's/\.[0-9][0-9]*\.[0-9]*\.TIF//' | sort | uniq | parallel --bar ./data/query.py --output images/labels/ ${LANDCOVER}/nlcd_2011_landcover_2011_edition_2014_10_10.img --query images/train/{}*.TIF

# pull out a val set
mkdir -p images/val
ls images/train | shuf | head -n $TEST_SIZE | xargs -I{} mv images/train/{} images/val/

# generate file lists
ls images/val/ | sed 's/.*/& 0/' | shuf > images/val.txt
ls images/train/ | sed 's/.*/& 0/' | shuf > images/train.txt

# make parallel lists with the actual label-image name
cat images/val.txt | sed 's/TIF/labels.TIF/' > images/val-labels.txt
cat images/train.txt | sed 's/TIF/labels.TIF/' > images/train-labels.txt

# create leveldb and image means
./data/build_image_sets.py

# create label databases, parallel to the image ones
mkdir -p temp/classify
./data/build_label_set.py --output temp/classify/val-labels-lmdb --image-list images/val-labels.txt --image-root images/labels --size 128
./data/build_label_set.py --output temp/classify/train-labels-lmdb --image-list images/train-labels.txt --image-root images/labels --size 128 > temp/classify/classes.txt
```
