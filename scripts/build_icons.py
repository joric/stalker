import json
from pathlib import Path
import shutil

EXPORT_DIR = Path('C:/Temp/Exports')
DATA_FILE = Path('../data/markers.json')
MISSING_FILE = Path('missing_icons.txt')

data = json.loads(DATA_FILE.read_text(encoding='utf-8'))

icons = {
    o['icon']
    for o in data.get('prototypes', {}).values()
    if o.get('icon', '').startswith('/Game')
}

missing_files = set()

for icon in sorted(icons):
    rel_path = icon.removeprefix('/Game')
    asset = f'Stalker2/Content{rel_path}'
    src = EXPORT_DIR / f'{asset}.png'

    if not src.exists():
        print('missing', src)
        missing_files.add(f'{asset}.asset')
        continue

    dest = Path(f'../images/icons/Game{rel_path}.png')
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f'Copied: {src} -> {dest}')

if missing_files:
    print(f'{len(missing_files)} missing files detected, saving to {MISSING_FILE}...')
    MISSING_FILE.write_text('\n'.join(sorted(missing_files)) + '\n', encoding='utf-8')
