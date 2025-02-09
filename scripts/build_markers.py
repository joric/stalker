# (c) 2024-2025 Joric, https://github.com/joric/maps/wiki/Stalker-2
# Needs data files to work, use FModel to extract subdirectores:
# * Stalker2/Content/GameLite/GameData
# * Stalker2/Content/GameLite/DLCGameData
# * Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap
# (export cfg as raw data (uasset), export umap files as json)

import json, re, glob, os, sys, time, copy
from collections import defaultdict
from collections import Counter
from io import StringIO
import traceback

cache_dir = 'C:/Temp/Exports'
cache_file = 'cache.json'
markers_file = '../data/markers.json'
world_path = 'Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP'

bp_classes = {
    'BP_Bed_OnBed_C':'EMarkerType::Bed',
    'BP_PlayerStash_C':'EMarkerType::PlayerStorage',
    'BP_TopazScanner':'EMarkerType::Scanner',
    'BP_Teleport_Portal_Bubble': 'EMarkerType::Teleport',

     # taken from Stalker2/Content/GameLite/Blueprints/Interactable
     # and Stalker2/Content/_STALKER2/GameDesign/InteractiveObjects

    'BP_Door': 'EMarkerType::Door',
    'BP_DoorView': 'EMarkerType::Door',
    'BP_InteractableDoor': 'EMarkerType::Door',
    'BP_BunkerDoor': 'EMarkerType::Door',
    'BP_TrainDoor': 'EMarkerType::Door',
    'BP_Stalker2Padlock': 'EMarkerType::PadLock',
    'BP_Stalker2Door': 'EMarkerType::Door',
    'BP_Stalker2PhysicsDoor': 'EMarkerType::Door',
    'BP_gen_security_door_': 'EMarkerType::Door',
    'BP_TrainDoor': 'EMarkerType::Door',
    'BP_DynamicObject_2states_final': 'EMarkerType::DynamicObject', # see BP_CodeLock_C_UAID_00D861D9738D06F901_1800936926

    'BP_CodeLock': 'EMarkerType::CodeLock',
    'BP_Cardlock': 'EMarkerType::CardLock',
    'BP_Lever': 'EMarkerType::Lever',
    'BP_Stalker2SimpleLever': 'EMarkerType::Lever',
    'BP_Stalker2TripleLever': 'EMarkerType::Lever',
    'BP_Padlock': 'EMarkerType::PadLock',
    'BP_Button': 'EMarkerType::Button',
    'BP_Latch': 'EMarkerType::Latch',
    'BP_Valve': 'EMarkerType::Valve',

    'BP_FusePanel': 'EMarkerType::FusePanel',
    'BP_BunkerHatch': 'EMarkerType::Door',

    'BP_Safe': 'EMarkerType::Container',
    'BP_Dalins_Safe': 'EMarkerType::Container',

    'BP_Trap': 'EMarkerType::Trap',

    'BP_Diesel_Generator': 'EMarkerType::Generator',

    'BP_ExplosivesPackage': 'EMarkerType::Explosives',

    'BP_OpeningContainer': 'EMarkerType::OpeningContainer',
    'BP_Turnstile':  'EMarkerType::Turnstile',
}

def parse_struct(reader, options={}):
    result = {}

    def parse_key(key):
        return f"[{len(result)}]" if key == "[*]" else key

    def parse_options(line):
        if '{' in line and line.endswith('}'):
            head, tail = map(str.strip, line.split('{'))
            vars = map(str.strip, tail[:-1].split(';'))
            return head, {key.strip(): value.strip() for s in vars if '=' in s for key,value in [s.split('=', 1)]}
        return line, {}

    def parse_value(value):
        value, options = parse_options(value) # remove {bskipref} etc.
        if not value or value == "empty" or value == "Empty" or value == "None":
            return None
        if re.match(r'^-?\d*\.?\d*f?$', value):
            return float(value[:-1] if value[-1]=='f' else value) if '.' in value or 'f' in value else int(value)
        return value

    while True:
        line = reader.readline()
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        if line.startswith("//"):
            options['comment'] = line[2:].strip()

        result.update(options)

        if line == "struct.end":
            return result

        if "struct.begin" in line:
            key = line.split(":")[0].strip()
            value, options = parse_options(line)
            result[parse_key(key)] = parse_struct(reader, options)

        elif "=" in line:
            key, value = map(str.strip, line.split("=", 1))
            result[parse_key(key)] = parse_value(value)

        options = {}

    return result

def load_cache():
    if os.path.exists(cache_file):
        print(f'{cache_file} exists ({os.path.getsize(cache_file)//1024//1024}Mb), loading records...')
        return json.load(open(cache_file,'r', encoding='utf-8'))
    else:
        print(cache_file, 'does not exist, parsing records...')
        return load_files()

def load_files():
    folders = [
        'Stalker2/Content/GameLite/GameData',
        'Stalker2/Content/GameLite/DLCGameData',
    ]
    total = 0
    processed = 0
    data = {}
    for folder in folders:
        g = list(glob.glob(os.path.join(cache_dir, f'{folder}/**/*.cfg'),recursive=True))
        total += len(g)
        print('found', total, '.cfg files in', folder)
        for filename in g:
            reader = open(filename,'r', encoding='utf-8-sig')

            try:
                result = parse_struct(reader)
            except Exception as e:
                print('exception at', filename)
                traceback.print_exc()
                exit(0)

            package_path = filename.replace(cache_dir+'\\', '').replace('\\','/')

            data[package_path] = result

            processed += 1
            sys.stderr.write(f'file {processed} of {total}    \r')

    print('writing data...')
    f = open(cache_file, 'w', encoding='utf-8')
    json.dump(data, f, indent=2, sort_keys=False)
    return data

def get_coordinates(data):
    pts = data
    if type(pts) is not dict: return None

    coord = [pts[k] for k in('PositionX','PositionY','PositionZ')if k in pts]
    if coord: return coord

    pts = data.get('WorldPosition',{})
    coord =  [pts[k] for k in('X','Y','Z')if k in pts]
    if coord: return coord

    pts = data.get('PlayerLocation',{})
    coord =  [pts[k] for k in('X','Y','Z')if k in pts]
    if coord: return coord

def get_item_properties(data, remap):
    return {v: data[k] for k,v in remap.items() if k in data}

def load_map(records, remap):
    entries = {}
    for key, data in records.items():
        if type(data) is not dict: continue
        sid = data.get('SID')
        if sid:
            entries[sid] = {}
            if 'refkey' in data:
                ref = data['refkey']
                if ref in records:
                    entries[sid].update(get_item_properties(records[ref], remap))
            entries[sid].update(get_item_properties(data, remap))
    return entries

def cleanup(prop):
    cleanup_map = {
        'comment': ['------------------------------------------', 'Location markers'],
        'clue': ['EmptyInherited'],
        'area': ['WorldMap_WP'],
    }

    for k, values in cleanup_map.items():
        for v in values:
            if prop.get(k)==v:
                del prop[k]


RANK_ANY = 'ERank::Any'
def get_rank_code(enum):
    rank_code = {
        'ERank::Newbie':'0',
        'ERank::Experienced':'1',
        'ERank::Veteran':'2',
        'ERank::Master':'3',
    }
    return rank_code.get(enum)

def add_spawns(data, prop):
    spawns = []

    for stash_sid in ('StashPrototypeSID', 'CorpseStashSID', 'PackOfItemsPrototypeSID'):
        stash = data.get(stash_sid)
        if stash:
            for s in stash.split(','):
                s = s.strip()
                spawns.append(s)

    for gs in (data.get('ItemGeneratorSettings')or{}).values():
        rank = gs.get('PlayerRank', RANK_ANY)
        prefix = get_rank_code(rank)
        for g in (gs.get('ItemGenerators')or{}).values():
            s = g.get('PrototypeSID')
            if s:
                s = s.strip()
                if prefix: s = prefix + ':' + s
                spawns.append(s)

    if spawns:
        prop['spawns'] = spawns


def export_prototypes(records):
    entries = {}
    # just export localization sids for now
    for key, config in records.items():
        if type(config) is not dict: continue
        lsid = config.get('LocalizationSID')
        if lsid:
            entries[key] = {'lsid':lsid, 'items': list((config.get('FittingWeaponsSIDs')or{}).values())}
    return entries

def export_stashes(records):
    entries = {}
    for key, config in records.items():
        if key in ['comment','empty']: continue
        data = type(config) is dict and config.get('ItemGenerators') or {}
        ranks = defaultdict(dict)

        for values in data.values():
            rank = values.get('Rank', RANK_ANY)
            loot = values.get('SmartLootParams',{})
            for field in ['PrimaryWeaponParams','GrenadesParams','ConsumablesParams', 'HealthParams', 'AttachParams']:
                params = loot.get(field) or {}
                for param in params.values():
                    ranks[rank] = {}
                    fields = {'ItemSetCount': 'count', 'MinSpawnChance':'min','MaxSpawnChance': 'max'}
                    ranks[rank].update({v: param[k] for k,v in fields.items() if k in param})

                    items = param.get('Items',{})

                    if items:
                        ranks[rank]['items'] = {}

                    for item in items.values():
                        name = item.get('ItemPrototypeSID')
                        fields = {'MinCount':'min', 'MaxCount':'max', 'Weight':'weight'}
                        ranks[rank]['items'][name] = {v: item[k] for k,v in fields.items() if k in item}

        entries['gen_' + key] = ranks
    return entries

def export_packs(records):
    entries = {}
    for key, config in records.items():
        if key in ['comment','empty']: continue
        data = type(config) is dict and config.get('PackOfItemsSettings') or {}
        ranks = defaultdict(dict)
        for values in data.values():
            rank = values.get('PlayerRank', RANK_ANY)
            items = values.get('Items',{})
            for item in items.values():
                name = item.get('ItemPrototypeSID')
                weight = item.get('Weight')
                if weight:
                    ranks[rank][name] = weight
        entries['gen_' + key] = ranks
    return entries

gen_remap = {
    'MinCount':'min',
    'MaxCount':'max',
    'Chance':'chance',
    'Weight':'weight',
    'MinDurability': 'min_durability',
    'MaxDurability': 'max_durability',
    'AmmoMinCount': 'min_ammo',
    'AmmoMaxCount': 'max_ammo',
}

def export_generators(records):
    entries = {}

    for key, config in records.items():
        if key in ['comment','empty']: continue
        sid = type(config) is dict and config.get('SID')
        if not sid:
            continue

        entry = defaultdict(dict)

        data = type(config) is dict and config.get('ItemGenerator') or {}

        if not data:
            data = config.get('MoneyGenerator')
            if data:
                name = "Money"
                item = data
                entry[name] = {v: item[k] for k,v in gen_remap.items() if k in item}
                entries[sid] = entry
            if not data:
                refkey = config.get('refkey')
                if refkey:
                    entries['gen_' + sid] = { 'gen_' + refkey: {} }

            continue

        for values in data.values():
            if type(values) is not dict: continue
            items = values.get('PossibleItems') or {}
            for item in items.values():
                name = item.get('ItemPrototypeSID')
                if not name:
                    name = item.get('ItemGeneratorPrototypeSID')
                    if not name: continue
                    name = 'gen_' + name;
                entry[name] = {v: item[k] for k,v in gen_remap.items() if k in item}

        entries['gen_' + sid] = entry

    return entries

def get_filename(package_path):
    return os.path.normpath(os.path.join(cache_dir,package_path))+'.json'

bp_counter = Counter()
bp_missing_files = []

def get_bp_cells(package_path):
    out = []
    filename = get_filename(package_path)
    data = json.load(open(filename, 'r', encoding='utf-8-sig'))
    for o in data:
        p = o.get('Properties',{})
        r = p.get('SubObjectsToCellRemapping',{})
        for t in r:
            key, cell = t['Key'], t['Value']
            for name in bp_classes:
                if name in key:
                    out.append(cell)

                    package_path = os.path.join(world_path,'_Generated_', cell)
                    filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'

                    if not os.path.exists(filename):
                        #print('NOT CACHED', cell, 'need for', key)
                        continue

    #print('found items', counter)
    return out

def get_bp_markers(cells):
    features = []
    #properties = {}
    cached_coord = {}
    cached_prop = {}

    for cell in cells:
        package_path = os.path.join(world_path,'_Generated_', cell)
        filename = os.path.normpath(os.path.join(cache_dir, package_path)) + '.json'

        if not os.path.exists(filename):
            bp_missing_files.append(filename)
            continue

        data = json.load(open(filename, 'r', encoding='utf-8-sig'))

        def add_prop(prop, p, name, k):
            value = p.get(name)
            if value:
                prop[k] = value

        # door references are cfg entries that refer to guids, usually via 'SignalReceiverGuid'
        def get_guid(prop, p, add_references=False):
            guid = p.get('Guid','').replace('-','')
            if guid:
                if add_references:

                    if guid in cached_guids:
                        k = 'references'
                        if k not in prop:
                            prop[k] = {}
                        prop[k].update(cached_guids[guid])

                    if guid in cached_items:
                        k = 'items'
                        if k not in prop:
                            prop[k] = {}
                        prop[k].update(cached_items[guid])

            return guid

        def add_key(prop, k, name, value):
            if k not in prop:
                prop[k] = {}
            prop[k][name] = value

        # collect all properties for matching classes, group by name
        for o in data:
            bp_type = o['Type']
            for class_name_prefix, marker_type in bp_classes.items():
                if bp_type.startswith(class_name_prefix):
                    name = o['Name']
                    #if name!='BP_DoorView_C_UAID_18C04D7E659CAACD01_1306808572': continue
                    cached_prop[name] = {'sid': name, 'uaid': name, 'type': 'ESpawnType::CustomMarker', 'name': marker_type, 'cell': cell}
                    prop = cached_prop[name]
                    p = o.get('Properties',{})

                    sp = name.split('_UAID_')
                    if len(sp)==2:
                        cname, uaid = sp
                        prop['sid'] = uaid

                    # use blueprint guid as sid for the blueprint items
                    guid = get_guid(prop, p)
                    if guid: prop['sid'] = guid

                    add_prop(prop, p, 'bUnbreakable', 'unbreakable')
                    add_prop(prop, p, 'bIsLocked', 'locked')
                    add_prop(prop, p, 'bBroken', 'broken')


                    c = p.get('EndPoint',{}).get('Translation')
                    if c:
                        prop['delta'] = [float(c[t]) for t in 'XYZ']

        # collect outer properties, i.e. all entries that list current class name as "outer"
        for o in data:
            outer = o.get('Outer')
            if outer in cached_prop:
                prop = cached_prop[outer]
                name = o.get('Name')
                bp_type = o['Type']
                p = o.get('Properties',{})

                add_prop(prop, p, 'CorrectCode', 'keycode') # BP_Cardlock property

                guid = get_guid(prop, p, True)

                # signal sender component (usually in BP_Cardlock)
                for e in p.get('Signals',[]):
                    ref = e.get('ReceiverComponentRef',{}).get('OtherActor',{}).get('SubPathString')
                    rcl = e.get('ReceiverComponentRef',{}).get('OtherActor',{}).get('AssetPathName')
                    guid = e.get('ReceiverGuid','').replace('-','')
                    if guid:
                        ref = (ref or 'null').split('.').pop()
                        rcl = (rcl or 'null').split('/').pop()
                        add_key(prop, 'actors', ref, guid)

                for e in p.get('ObjectsNeededToInteract',[]):
                    sid = e.get('PrototypeSID',{}).get('Value')
                    count = e.get('Count', 0)
                    once = e.get('bConsumeOnce')
                    if sid:
                        add_key(prop, 'items', sid, count)

                if not cached_coord.get(outer):
                    if bp_type in ['SceneComponent','SkeletalMeshComponent','StaticMeshComponent']:
                        if loc := p.get('RelativeLocation'):
                            cached_coord[outer] = [float(loc[t]) for t in 'XYZ']

    for name in cached_prop:
        prop = cached_prop[name]
        coord = cached_coord.get(name)
        if not coord: continue

        delta = prop.get('delta')
        if delta:
            prop['target'] = [coord[i]+delta[i] for i in range(3)]
            del prop['delta']

        cleanup_prop(prop)

        feature = {
            'type': 'Feature',
            'geometry': {'type':'Point', 'coordinates': coord},
            'properties': prop
        }
        features.append(feature)

    return features

cached_guids = defaultdict(dict)
cached_items = defaultdict(dict)

def get_connections(data):
    out = set()
    for launch in (data.get('Launchers')or{}).values():
        for conn in (launch.get('Connections')or{}).values():
            sid = conn.get('SID')
            if sid:
                out.add(sid)
    return out

def cleanup_prop(prop):
    for k in ['items','references','actors']:
        if k in prop:
            value = prop[k]
            prop[k] = list(filter(lambda x:not re.match(r'^BP.*(VentBlades|_lamp|_Decal|_VFX|_spotlight)|^VolumeForEffects',x), value.keys()))
            if not prop[k]:
                del prop[k]

def export_markers(cache):
    features = []

    marker_proto = load_map(cache['Stalker2/Content/GameLite/GameData/MarkerPrototypes.cfg'], {'MarkerRadius':'radius', 'MarkType': 'name', 'Title':'title', 'Description':'description'})
    quest_proto = load_map(cache['Stalker2/Content/GameLite/GameData/ObjPrototypes/QuestObjPrototypes.cfg'], {'NPCPrototypeSID': 'npc', 'Faction': 'faction'})
    npc_proto = load_map(cache['Stalker2/Content/GameLite/GameData/NPCPrototypes.cfg'], {'NameTextKey': 'title', 'Rank': 'rank', 'NPCMarker': 'subtype'})

    item_proto = {}

    pfs=[
        'AmmoPrototypes.cfg',
        'ArmorPrototypes.cfg',
        'ArtifactPrototypes.cfg',
        'AttachPrototypes.cfg',
        'BlueprintPrototypes.cfg',
        'ConsumablePrototypes.cfg',
        'DetectorPrototypes.cfg',
        'GDItemPrototypes.cfg',
        'GrenadePrototypes.cfg',
        'KeyItemPrototypes.cfg',
        'QuestItemPrototypes.cfg',
        'WeaponPrototypes.cfg'
    ]

    for name in pfs:
        item_proto.update(  load_map(cache['Stalker2/Content/GameLite/GameData/ItemPrototypes/'+name], {'LocalizationSID':'lsid'}))

    # 1-st pass, collect references
    for package_path, package in cache.items():
        for sid, data in package.items():
            if type(data) is dict:

                for guid_prop in data:
                    if not guid_prop.endswith('Guid'): continue
                    guid = data.get(guid_prop)
                    if guid:
                        cached_guids[guid][sid] = guid

                        # add items, e.g. E03_MQ04_Key from Garbage_L_Factory_Camp_SendSignal_Basement_Entrance
                        for conn_sid in get_connections(data):
                            item_sid = (package.get(conn_sid)or{}).get('ItemPrototypeSID')
                            if item_sid:
                                cached_items[guid][item_sid] = guid

                # add markers/conditions/trigger
                for marker in (data.get('Markers')or{}).values():
                    for condition in (marker.get('Conditions')or{}).values():
                        for entry in condition.values():
                            guid = entry.get('Trigger')
                            if guid:
                                cached_guids[guid][sid] = guid

    # 2-nd pass, collect coordinates
    for package_path, package in cache.items():
        comment = package.get('comment')
        for sid, data in package.items():
            try:
                coord = get_coordinates(data)

                # skip markers without coordinates
                if not coord or coord==[0,0,0]: continue

                prop = {'sid': sid}

                if sid in cached_guids:
                    prop['references'] = cached_guids[sid]

                if sid in cached_items:
                    prop['items'] = cached_items[sid]

                refkey = data.get('refkey')
                if package.get(refkey):
                    template = copy.copy(package.get(refkey))
                    template.update(data)
                    data = template

                if refkey == 'base_region':
                    data['SpawnType'] = 'ESpawnType::Marker'
                    data['SpawnedPrototypeSID'] = 'EMarkerType::RegionMarker'

                remap = {
                    'SpawnType': 'type',
                    'SpawnedPrototypeSID': 'name',
                    'ClueVariablePrototypeSID': 'clue',
                    'LevelName': 'area',
                    'CloseDoorRadius': 'radius',
                    'SpawnInRadius': 'spawn_radius',
                    'RegionType': 'region',

                    # remap to name for now
                    'TriggerShape': 'name',
                    'VolumeDailySchedulePresetSID' : 'schedule',
                    'Radioactivity': 'radioactivity',
                    'ContextualActionSID': 'name',
                    'MarkerSID': 'name',
                }

                prop.update({v: data[k] for k,v in remap.items() if k in data})

                # skip some markers
                if not prop: continue
                if 'type' not in prop: continue
                if prop.get('type')=='ESpawnType::DestructibleObject': continue
                if prop.get('area') and 'WorldMap_WP' not in prop.get('area'): continue

                # update with prototype properties
                name = data.get('SpawnedPrototypeSID')
                if name:
                    prop |= marker_proto.get(name,{})
                    npc = quest_proto.get(name,{}).get('npc')
                    prop |= npc_proto.get(npc,{})
                    if faction := quest_proto.get(name,{}).get('faction'):
                        prop |= {'faction': faction}

                # set name and title for hubs
                if prop.get('type')=='ESpawnType::Hub':
                    name = data.get('MarkerSID')
                    if not name:
                        continue # skip null hubs
                    prop['name'] = name
                    prop['title'] = name if name.startswith('sid_') else f'sid_locations_{name}_name'

                # set title for region markers
                if prop.get('name')=='EMarkerType::RegionMarker':
                    prop['title'] = 'sid_locations_region_' + prop.get('sid') + '_name'

                # set title for items
                lsid = item_proto.get(name,{}).get('lsid')
                if lsid:
                    prop['lsid'] = lsid

                cleanup(prop)
                add_spawns(data, prop)

                cleanup_prop(prop)

                features.append({'type':'Feature','geometry': {'type':'Point', 'coordinates': coord }, 'properties': prop})
                #sys.stderr.write(f'added {len(features)} markers    \r')

            except Exception as e:
                print('exception at', package_path, sid)
                traceback.print_exc()
                exit(0)

    out = {"type": "FeatureCollection", "features": features}

    gen = {}
    gen.update(export_packs(cache['Stalker2/Content/GameLite/GameData/PackOfItemsGroupPrototypes.cfg']))
    gen.update(export_stashes(cache['Stalker2/Content/GameLite/GameData/StashPrototypes.cfg']))
    gen.update(export_generators(cache['Stalker2/Content/GameLite/GameData/ItemGeneratorPrototypes.cfg']))
    gen.update(export_generators(cache['Stalker2/Content/GameLite/GameData/ItemGeneratorPrototypes/Gamepass_ItemGenerators.cfg']))
    out['generators'] = gen

    # partitions are read from WorldMap_WP and then exported with FModel as json (one by one)
    cells = sorted(set(get_bp_cells(world_path))) # just "set" shuffles items on each commit
    features2 = get_bp_markers(cells)

    features.extend(features2)

    protos = {}
    protos.update(export_prototypes(cache['Stalker2/Content/GameLite/GameData/ItemPrototypes/BlueprintPrototypes.cfg']))
    out['prototypes'] = protos

    print(f'writing {markers_file} ({len(features)} features)...')
    f = open(markers_file, 'w', encoding='utf-8', newline='\n')
    json.dump(out, f, indent=2)

def test():
    # Example usage
    input_text = """
    // taken from Stalker2/Content/GameLite/GameData/DialogChainPrototypes.cfg
    [0] : struct.begin
    SID = Empty
    ID = 0
    Factions: struct.begin
        [*] = None{bskipref}
    struct.end
    struct.end
    [1] : struct.begin {refkey=[0]}
    SID = HumanoidRestrictions
    ID = 2
    Factions: struct.begin
        [*] = Bandits
        [*] = Monolith
        [*] = Duty
    struct.end
    struct.end
    """
    string_io = StringIO(input_text)

    #string_io = open('parser_test1.cfg','r')
    #string_io = open('parser_test2.cfg','r')
    string_io = open('parser_test3.cfg','r')
    #string_io = open('cfg/MarkerPrototypes.cfg','r')
    #string_io = open('cfg/ItemGeneratorPrototypes.cfg','r', encoding='utf-8-sig')

    result = parse_struct(string_io)
    print(json.dumps(result, indent=2, sort_keys=False))

if __name__ == '__main__':
    #test()
    tm = time.time()
    data = load_cache()
    export_markers(data)
    if bp_missing_files: print(len(bp_missing_files), 'cell files missing')
    #print('bp_counter', bp_counter)
    print(f'finished in {time.time()-tm:f} seconds')

