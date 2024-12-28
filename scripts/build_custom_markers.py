import os
import json

def get_partitions(package_path):
    out = []
    filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'
    data = json.load(open(filename, 'r'))
    for o in data:
        p = o.get('Properties',{})
        r = p.get('SubObjectsToCellRemapping',{})
        for t in r:
            k,v = t['Key'], t['Value']
            if 'BP_PlayerStash_C' in k:
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
                if 'BP_PlayerStash_C' in outer or 'BP_Bed_OnBed_C' in outer:
                    c = o.get('Properties',{}).get('RelativeLocation',{})
                    coord = [float(c[a]) for a in ('X','Y','Z')]

                    print('found', outer)

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

# partitions exported with FModel as json

t='''MainGrid_L0_X2Y0_DL0
MainGrid_L0_X-48Y10_DL0
MainGrid_L0_X-2Y21_DLA8129FC2
MainGrid_L0_X-1Y22_DLC6C35766
MainGrid_L0_X12Y17_DL0
MainGrid_L0_X-16Y17_DL0
MainGrid_L0_X13Y-6_DL0
MainGrid_L0_X-15Y1_DL0
MainGrid_L0_X-28Y-39_DL0
MainGrid_L0_X31Y30_DL0
MainGrid_L0_X40Y33_DL0
MainGrid_L0_X37Y37_DL0
MainGrid_L0_X6Y38_DL0
MainGrid_L0_X-31Y-22_DL0'''

partitions = t.splitlines()

cache_dir = 'C:/Temp/Exports'
package_path = 'Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP'

#partitions = get_partitions(package_path)

features = get_markers(partitions)

j = {"type": "FeatureCollection", 'features': features }

fname = 'markers_custom.json'
print(f'saving {len(features)} markers to "{fname}"...')

json.dump(j, open(fname,'w'), indent=2)


