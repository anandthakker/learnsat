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

# generate label output files
ls images/train/ | parallel -n 1000 ./data/labels.py --labels images/labels/ {} > temp/train.txt
ls images/val/ | parallel -n 1000 ./data/labels.py --labels images/labels/ {} > temp/val.txt

# shuffle the lines in each file
cat temp/train.txt | shuf > temp/train-shuffled.txt
mv temp/train-shuffled.txt temp/train.txt
cat temp/test.txt | shuf > temp/test-shuffled.txt
mv temp/test-shuffled.txt temp/test-shuffled.txt

# make parallel lists with the actual label-image name
cat temp/test.txt | sed 's/TIF/labels.TIF/' > temp/test-labels.txt
cat temp/train.txt | sed 's/TIF/labels.TIF/' > temp/train-labels.txt

# create leveldb and image means
```
