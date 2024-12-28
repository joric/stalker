import os
import json

classes = ['BP_PlayerStash_C','BP_Bed_OnBed_C']

def get_partitions(package_path):
    out = []
    filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'
    data = json.load(open(filename, 'r'))
    for o in data:
        p = o.get('Properties',{})
        r = p.get('SubObjectsToCellRemapping',{})
        for t in r:
            k,v = t['Key'], t['Value']
            if any(x in k for x in classes):
                out.append(v)
    return out


def get_markers(partitions):
    features = []
    for p in partitions:
        package_path = 'Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP/_Generated_/' + p
        filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'
        data = json.load(open(filename, 'r'))
        for o in data:
            type = o['Type']
            if type == 'SkeletalMeshComponent' or type == 'StaticMeshComponent':
                outer = o['Outer']
                if any(x in outer for x in classes):
                    c = o.get('Properties',{}).get('RelativeLocation',{})
                    coord = [float(c[a]) for a in ('X','Y','Z')]
                    print('found', outer, 'in', p)
                    features.append({
                        'type': 'Feature',
                        'geometry': {'type':'Point', 'coordinates': coord},
                        'properties': {
                            'title': outer.split('_UAID')[0],
                            'description': 'Custom::PersonalItems',
                            'sid': outer,
                            'cell': p,
                        }
                    })
    return features

# partitions are read from WorldMap_WP and then exported with FModel as json (one by one)

cache_dir = 'C:/Temp/Exports'
package_path = 'Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP'

partitions = set(get_partitions(package_path))

for p in partitions: print(p)

features = get_markers(partitions)

j = {"type": "FeatureCollection", 'features': features }

fname = 'markers_custom.json'
print(f'saving {len(features)} markers to "{fname}"...')

json.dump(j, open(fname,'w'), indent=2)


