from PIL import Image, ImageOps
import glob
import os

cache_dir = 'C:/Temp/Exports'

out_dir = '../data/sprites'

os.makedirs(out_dir, exist_ok = True)

iconSize = 42

folders = [
    'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr6/NotActive/Shadow',
    'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr7/NotActive/Shadow',
]

def crop_and_resize(img, size, resize=True):
    img_cropped = ImageOps.crop(img, border=0)
    bbox = img_cropped.getbbox()  # Get the bounding box of non-transparent areas
    
    if bbox:
        img_cropped = img_cropped.crop(bbox)
    else:
        print(f"Warning: {filename} appears to be fully transparent")

    print(img_cropped.size)

    if resize:
        # Resize the image, maintaining aspect ratio
        return ImageOps.pad(img_cropped, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 1.0))

    original_image = img_cropped

    original_width, original_height = original_image.size
    target_width, target_height = size, size

    # Calculate padding
    padding_left = max((target_width - original_width) // 2, 0)
    padding_top = max((target_height - original_height) // 2, 0)
    padding_right = max(target_width - original_width - padding_left, 0)
    padding_bottom = max(target_height - original_height - padding_top, 0)

    # Create a new image with the target size and padding color
    new_image = Image.new(original_image.mode, (target_width, target_height))

    # Paste the original image onto the center of the new image
    new_image.paste(original_image, (padding_left, padding_top))

    return new_image


    #return ImageOps.pad(img_cropped, (iconSize, iconSize))

for folder in folders:
    files = list(glob.glob(os.path.join(cache_dir, folder, '**', '*.png'), recursive=True))

    for filename in files:
        print(f"Processing: {filename}")
        
        # Open the image
        with Image.open(filename) as img:
            # Crop transparent areas
            img_resized = crop_and_resize(img, iconSize)
            # Save the resized image as PNG
            base_name = os.path.basename(filename)
            output_path = os.path.normpath(os.path.join(out_dir, base_name))
            img_resized.save(output_path, format='PNG')
            print(f"Saved: {output_path}")

# cut the compass atlas
img_path = 'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/Textures/CompassMarker.png'
filename = os.path.normpath(os.path.join(cache_dir, img_path))
gw = 44
gh = 46
tw = 40
th = 44
iconSize2 = 32
with Image.open(filename) as img_atlas:
    for i in range(5):
        for j in range(4):
            img = img_atlas.crop((i*gw, j*gh, i*gw + tw, j*gh+th))

            img_resized = crop_and_resize(img, iconSize2, False)

            base_name = f'CompassMarker_{i}_{j}.png'
            output_path = os.path.normpath(os.path.join(out_dir, base_name))
            img_resized.save(output_path, format='PNG')
            print(f"Saved: {output_path}")



