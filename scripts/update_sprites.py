from PIL import Image, ImageOps
import glob
import os

cache_dir = 'C:/Temp/Exports'

out_dir = '../data/sprites'

folders = [
    'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr6/NotActive/Shadow',
    'Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr7/NotActive/Shadow',
]

os.makedirs(out_dir, exist_ok = True)

iconSize = 48

for folder in folders:
    files = list(glob.glob(os.path.join(cache_dir, folder, '**', '*.png'), recursive=True))

    for filename in files:
        print(f"Processing: {filename}")
        
        # Open the image
        with Image.open(filename) as img:
            # Crop transparent areas
            img_cropped = ImageOps.crop(img, border=0)
            bbox = img_cropped.getbbox()  # Get the bounding box of non-transparent areas
            
            if bbox:
                img_cropped = img_cropped.crop(bbox)
            else:
                print(f"Warning: {filename} appears to be fully transparent")
                continue
            

            print(img_cropped.size)

            # Resize the image to 64x64, maintaining aspect ratio
            img_resized = ImageOps.pad(img_cropped, (iconSize, iconSize), method=Image.Resampling.LANCZOS, centering=(0.5, 1.0))
            
            # Create output filename
            base_name = os.path.basename(filename)
            output_path = os.path.normpath(os.path.join(out_dir, base_name))
            
            # Save the resized image as PNG
            img_resized.save(output_path, format='PNG')
            print(f"Saved: {output_path}")
