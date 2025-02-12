# gta2-gmp-rotator
Rotate an uncompressed GTA2 map by 90°, 180° or 270° clockwise.

##  How to use

- Requires python 3.X.X
- Requires an uncompressed gmp map

If your gmp file isn't uncompressed, open it in official DMA map editor and just click "save". If done correctly, your file will have more than 6 MB.

Now there is two ways to run the rotator:
1: Put your gmp file in root folder of "rotate_gmp.py" and edit "run.bat"
python rotate_gmp.py my_map.gmp [rotation]

2: Conversely you can put the path of your map:
python rotate_gmp.py [map path] [rotation]

where [rotation] = 0, 90, 180 or 270

The rotated map will be created on root folder of "rotate_gmp.py" with name "[your_map_name]_rotated.gmp".

Now open the rotated map and click "save compressed". <ins>**Be aware that GTA2 only load compressed maps**</ins>. 

(optional) Next you might remove the uncompressed data and thus reducing map size using GMP optmizer.

## What is rotated:

- Block positions
- Block tile lids
- Block tile sides
- All types of slopes
- Road arrows (green & red)
- Light coordinates
- Zone coordinates
