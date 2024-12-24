# https://github.com/joric/maps/wiki/Stalker-2

from quicktex.s3tc.bc1 import * # pip install quicktex
from PIL import Image
import os,sys

export_dir = 'C:/Temp/Exports'

assets = [
    { 
        'path': 'Stalker2/Content/GameLite/FPS_Game/UIRemaster/UITextures/PDA/WorldMap/T_WorldMap_UDIM.uasset',
        'size': [65536, 65536],
        'tile_size': 128,
        'tile_border': 4,
    },
    {
        'path': 'MyProject/Content/stalker2_map_joric_8k_mod2.uasset',
        'size': [8192, 8192],
        'tile_size': 128,
        'tile_border': 4,
    },
]

asset = assets[0]

fname = os.path.join(export_dir, asset['path'].replace('.uasset','.ubulk'))
w, h = asset['size']
tw = th = asset['tile_size']
tb = asset['tile_border']

tiles_count = w//tw * h//th

f = open(fname, 'rb')
f.read(4) # first 4 bytes are reserved

bw = tw + tb*2
bh = th + tb*2

span_size = bw * bh * 4 // 8 # lossy PX_DXT1 encoding, 4 bits per pixel

def ReverseMortonCode2(x):
    x &= 0x55555555;
    x = (x ^ (x >> 1)) & 0x33333333
    x = (x ^ (x >> 2)) & 0x0f0f0f0f
    x = (x ^ (x >> 4)) & 0x00ff00ff
    x = (x ^ (x >> 8)) & 0x0000ffff
    return x

image = Image.new('RGB', (w, h))

for i in range(tiles_count):
    sys.stderr.write(f'processing tile {i+1} of {tiles_count}...   \r')

    data = f.read(span_size)
    texture = BC1Texture.from_bytes(data, bw, bh)
    image_bytes = BC1Decoder().decode(texture).tobytes()

    tile = Image.frombytes('RGBA', (bw, bh), image_bytes).convert('RGB')
    tile = tile.crop((tb, tb, bw-tb, bh-tb))

    x = ReverseMortonCode2(i) * tw
    y = ReverseMortonCode2(i >> 1) * th

    if h==65536: y = (y + 65536 - 8192) % 65536 # wrapping fix

    image.paste(tile, (x, y))

print()

print('saving preview...')
image.resize((1024,1024)).save('preview.jpg')

print('saving half-size image...')
image.resize((w//2,h//2)).save('half-size.jpg', quality=90)

# PIL cannot save 64k image in one piece. split in chunks

cw = w//512 # horizontal number of chunks
ch = h//512 # vertical number of chunks

iw = w//cw
ih = h//ch

for y in range(ch):
    for x in range(cw):
        name = f'chunks/{y}/{x}.jpg'
        os.makedirs(os.path.dirname(name), exist_ok = True)
        sys.stderr.write(f'saving {name}...  \r')
        image.crop((x * iw, y * ih, x * iw + iw, y * ih + ih)).save(name, quality=75)
