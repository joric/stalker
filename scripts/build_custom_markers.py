import os
import json
from collections import Counter

cache_dir = 'C:/Temp/Exports'
world_path = 'Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP'
classes = ['BP_PlayerStash_C','BP_Bed_OnBed_C','BP_TopazScanner', 'BP_Teleport_Portal_Bubble']

counter = Counter()

def get_filename(package_path):
    return os.path.normpath(os.path.join(cache_dir,package_path))+'.json'

def get_cells(package_path):
    out = []
    filename = get_filename(package_path)
    data = json.load(open(filename, 'r'))
    for o in data:
        p = o.get('Properties',{})
        r = p.get('SubObjectsToCellRemapping',{})
        for t in r:
            key, cell = t['Key'], t['Value']
            for name in classes:
                if name in key:
                    out.append(cell)
                    counter[key.split('_UAID')[0]] += 1

                    package_path = os.path.join(world_path,'_Generated_', cell)
                    filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'

                    if not os.path.exists(filename):
                        print('NOT CACHED', cell, 'need for', key)
                        continue


    print('found items', counter)
    return out


def get_markers(cells):
    features = []
    for cell in cells:
        package_path = os.path.join(world_path,'_Generated_', cell)
        filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'

        if not os.path.exists(filename):
            print('missing', filename)
            continue

        data = json.load(open(filename, 'r'))
        for o in data:
            type = o['Type']
            if type == 'BP_Teleport_Portal_Bubble_C':
                target = o.get('Properties',{}).get('EndPoint',{}).get('Translation')
            if type in ('SkeletalMeshComponent','StaticMeshComponent','SceneComponent'):
                outer = o['Outer']
                if any(x in outer for x in classes):
                    c = o.get('Properties',{}).get('RelativeLocation',{})
                    if c:
                        coord = [float(c[a]) for a in ('X','Y','Z')]
                        #print('found', outer, 'in', cell)
                        features.append({
                            'type': 'Feature',
                            'geometry': {'type':'Point', 'coordinates': coord},
                            'properties': {
                                'title': outer.split('_UAID')[0],
                                'description': 'Custom::CustomItems',
                                'sid': outer,
                                'cell': cell,
                            }
                        })
                    if 'BP_Teleport_Portal_Bubble_C' in o['Outer'] and target:
                        delta = [target[t] for t in 'XYZ']
                        coord_target = [coord[t]+delta[t] for t in range(3)]
                        features.append({
                            'type': 'Feature',
                            'geometry': {'type':'Point', 'coordinates': coord_target},
                            'properties': {
                                'title': outer.split('_UAID')[0]+'_Target',
                                'description': 'Custom::CustomItems',
                                'sid': outer + '_Target',
                                'cell': cell,
                            }
                        })

    return features

# partitions are read from WorldMap_WP and then exported with FModel as json (one by one)

cells = set(get_cells(world_path))
features = get_markers(cells)

j = {"type": "FeatureCollection", 'features': features }

fname = 'markers_custom.json'
print(f'saving {len(features)} markers to "{fname}"...')

json.dump(j, open(fname,'w'), indent=2)


