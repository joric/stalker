import json
from pathlib import Path
import shutil

exports = 'C:/Temp/Exports'
missing_file = 'missing_icons.txt'
markers = json.loads(Path('../data/markers.json').read_text(encoding='utf-8'))

icons = set()
for proto in markers.get('prototypes', {}).values():
    icon = proto.get('icon', '')
    if icon.startswith('/Game'):
        icons.add(icon)

missing = set()

for icon in sorted(icons):
    path = icon.removeprefix('/Game')
    asset = 'Stalker2/Content' + path
    src = f'{exports}/{asset}.png'

    if not Path(src).exists():
        print(f'missing {src}')
        missing.add(f'{asset}.uasset')
        continue

    dst = f'../images/icons/Game{path}.png'
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f'copied {src} -> {dst}')

if missing:
    print(f'{len(missing)} icons missing, writing list to {missing_file}')
    Path(missing_file).write_text('\n'.join(sorted(missing)) + '\n', encoding='utf-8')
