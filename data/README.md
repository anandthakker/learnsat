## Prepping the data

```sh
export VALIDATION=LT50220292011187GNC01
# chop up the landsat images
ls ~/data/landsat | grep "^L" | grep -v $VALIDATION | parallel ../data/chop.py --output train/{}.{x}.{y}.TIF --size 128 --bands 123 ~/data/landsat/{}/{}_B{band}.TIF
../data/chop.py --output test/$VALIDATION.{x}.{y}.TIF --size 128 --bands 123 ~/data/landsat/$VALIDATION/$VALIDATION_B{band}.TIF
# for each chopped piece, grab the corresponding patch of the landcover raster
ls train/ | sed 's/\.[0-9][0-9]*\.[0-9]*\.TIF//' | sort | uniq | parallel --bar ../data/query.py --output labels/ ~/data/landcover/nlcd_2011_landcover_2011_edition_2014_10_10.img --query train/{}*.TIF
../data/query.py --output labels/ ~/data/landcover/nlcd_2011_landcover_2011_edition_2014_10_10.img --query test/*.TIF
# generate label output files
ls images/train/ | parallel -n 1000 ./data/labels.py --labels images/labels/ {} > temp/train.txt
ls images/test/ | parallel -n 1000 ./data/labels.py --labels images/labels/ {} > temp/test.txt
# create leveldb and image means
./data/create-image-sets.sh
./data/image_mean.sh
```
