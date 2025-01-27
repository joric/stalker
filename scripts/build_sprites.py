from PIL import Image, ImageOps
import glob
import os

cache_dir = 'C:/Temp/Exports'

out_dir = '../images/sprites'

os.makedirs(out_dir, exist_ok = True)

folders = [
    'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr6/NotActive/Shadow',
    'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr7/NotActive/Shadow',
]

colors = {
    'red':(255,0,0),
    'cyan': (33,175,214),
    'purple': (255,0,255),
    'green': (0,255,0),
    'orange': (232,165,20),
    'violet': (136,133,197),
    'jade': (74,211,172),
    'khaki': (213,197,138),
    'green': (50,200,50),
}

tints = {
    'claws': colors['red'],
    'box': colors['cyan'],
    #'anomaly': colors['orange'],
    'character': colors['khaki'],
    'radiation': colors['orange'],
    #'bag': colors['green'],

    'Stahes': colors['violet'],
    'Dangerous': colors['jade'],
    'Anomaly': colors['jade'],
    'Follow': colors['jade'],
    'Habar': colors['jade'],
    'Radiation': colors['jade'],
    'Quest': colors['cyan'],
    'QuestGiver': colors['cyan'],
    'Camp': colors['orange'],

}

iconSize = 48

def crop_and_resize(img, size, resize=True, tint=None, crop=0):
    img_cropped = img #ImageOps.crop(img, border=0)

    if crop:
        ch = cw = crop # 80 # good size match
        w,h = img.size
        b = (w-cw)//2
        bbox = (b,b, w-b, h-b)
    else:
        bbox = img_cropped.getbbox()  # Get the bounding box of non-transparent areas
    
    if bbox:
        img_cropped = img_cropped.crop(bbox)
    else:
        print(f"Warning: {filename} appears to be fully transparent")

    #print(img_cropped.size)

    if resize:
        # Resize the image, maintaining aspect ratio
        image = ImageOps.pad(img_cropped, (size, size), method=Image.Resampling.LANCZOS)

    else:
        original_image = img_cropped

        original_width, original_height = original_image.size
        target_width, target_height = size, size

        # Calculate padding
        padding_left = max((target_width - original_width) // 2, 0)
        padding_top = max((target_height - original_height) // 2, 0)
        padding_right = max(target_width - original_width - padding_left, 0)
        padding_bottom = max(target_height - original_height - padding_top, 0)

        # Create a new image with the target size and padding color
        image = Image.new(original_image.mode, (target_width, target_height))

        # Paste the original image onto the center of the new image
        image.paste(original_image, (padding_left, padding_top))

    if tint:
        original = image
        pixels = original.load()
        tint_color = tint + (255,)
        for y in range(original.height):
            for x in range(original.width):
                r, g, b, a = pixels[x, y]
                r = int(r * (tint_color[0] / 255))
                g = int(g * (tint_color[1] / 255))
                b = int(b * (tint_color[2] / 255))
                pixels[x, y] = (r, g, b, a)

    return image

    #return ImageOps.pad(img_cropped, (iconSize, iconSize))

def process_file(filename, iconSize, resize=True, crop=0):
    # Open the image
    with Image.open(filename) as img:
        # Crop transparent areas
        name = os.path.basename(filename).split('_')[1]
        tint = tints.get(name)
        img_resized = crop_and_resize(img, iconSize, resize=True, tint=tint, crop=crop)
        # Save the resized image as PNG
        base_name = os.path.basename(filename)
        output_path = os.path.normpath(os.path.join(out_dir, base_name))
        img_resized.save(output_path, format='PNG')
        print(f"Saved: {output_path}")

for folder in folders:
    files = list(glob.glob(os.path.join(cache_dir, folder, '**', '*.png'), recursive=True))
    for filename in files:
        process_file(filename, iconSize, resize=True, crop=80)

# region sprite
region_dir = 'Stalker2/Content/GameLite/FPS_Game/UIRemaster/UITextures/WorldMap/RegionMarker'
filename = os.path.join(cache_dir, region_dir, 'T_NotActive_Region_Shadow.png')
process_file(filename, iconSize, resize=True, crop=84)

# cut the compass atlas
img_path = 'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/Textures/CompassMarker.png'
filename = os.path.normpath(os.path.join(cache_dir, img_path))

gw = 44
gh = 46
tw = 40
th = 44
iconSize2 = 32
nw = 5
nh = 4

tiles = [
    'claws','skull', 'bag', 'circle',
    'circle_locked','fire', 'radiation', 'lock',
    'exclamation', 'character', 'circle_dot', 'question',
    'box', 'unlocked', 'anomaly', 'cave',
    'yen','repair','rest', 'misc',
]

def get_name(x,y):
    return tiles[x * nh + y]

with Image.open(filename) as img_atlas:
    for x in range(nw):
        for y in range(nh):
            img = img_atlas.crop((x*gw, y*gh, x*gw + tw, y*gh+th))
            name = get_name(x,y)
            tint = tints.get(name)
            img_resized = crop_and_resize(img, iconSize2, False, tint=tint)
            base_name = f'CompassMarker_{x}_{y}.png'
            output_path = os.path.normpath(os.path.join(out_dir, base_name))
            img_resized.save(output_path, format='PNG')
            print(f"Saved: {output_path}")
