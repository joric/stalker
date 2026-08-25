import json
import re
import os
import shutil

export_dir = 'C:/Temp/Exports'

data = json.load(open('../data/markers.json'))

icons = set()

for o in data.get('prototypes',[]).values():
    icon = o.get('icon')
    if not icon or '/Game' not in icon: continue
    icons.add(icon)


missing_files = set()

for icon in icons:
    path = re.sub(r'^/Game', '', icon )
    asset = 'Stalker2/Content' + path
    src = export_dir + '/' + asset + '.png'
    if not os.path.exists(src):
        print('missing', src)
        missing_files.add(asset + '.asset')
    else:
        dest = '../images/icons/Game' + path + '.png'

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        print(f"Copied: {src} -> {dest}")

if missing_files:
    fname = 'missing_icons.txt'
    print(f'{len(missing_files)} missing files detected, saving to {fname}...')
    f = open(fname,'w')
    for name in missing_files:
        print(name, file=f)
