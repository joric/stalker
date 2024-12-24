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

bw = tw + tb*2
bh = th + tb*2

span_size = bw * bh * 4 // 8 # lossy PX_DXT1 encoding, 4 bits per pixel

def MortonCode2(x):
    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555
    return x

def get_tile(x, y):
    if h == 65536: y = (y + 8192//th) % (65536//th)  # wrapping fix
    i = MortonCode2(x) | (MortonCode2(y) << 1)
    f.seek(4 + i * span_size, os.SEEK_SET)
    data = f.read(span_size)
    texture = BC1Texture.from_bytes(data, bw, bh)
    image_bytes = BC1Decoder().decode(texture).tobytes()
    tile = Image.frombytes('RGBA', (bw, bh), image_bytes).convert('RGB')
    return tile.crop((tb, tb, bw-tb, bh-tb))

# PIL cannot save 64k image in one piece. split in chunks

cw = 4 # horizontal number of chunks
ch = 4 # vertical number of chunks

iw = w//cw
ih = h//ch

nw = iw//tw
nh = ih//th

for cy in range(ch):
    for cx in range(cw):
        image = Image.new('RGB', (iw, ih))
        for tx in range(nw):
            for ty in range(nh):
                x = cx * nw + tx
                y = cy * nh + ty
                image.paste(get_tile(x, y), (tx * tw, ty * th))

        name = f'chunks/{cy}/{cx}.jpg'
        os.makedirs(os.path.dirname(name), exist_ok = True)
        sys.stderr.write(f'saving {name} ({iw}x{ih})...  \r')
        image.save(name, quality=85)
