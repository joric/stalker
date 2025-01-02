import os,sys,json,glob,re
import re
from collections import defaultdict

cache_dir = 'C:/Temp/Exports'

class UnrealCFGParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}

    def parse(self):
        stack = []
        current_section = self.data
        pending_comment = None  # Tracks comments preceding a section

        with open(self.filepath, "r", encoding="utf-8-sig") as file:  # Handle BOM
            for line in file:
                line = line.strip()

                if not line:
                    continue  # Skip empty lines

                if line.startswith("//"):
                    # Capture the comment
                    pending_comment = line.lstrip("//").strip()
                elif "struct.begin" in line:
                    # Start a new nested structure
                    name, attributes = self._parse_struct_begin(line)

                    # Initialize the section
                    if name not in current_section:
                        current_section[name] = p = {}
                        if pending_comment:
                            p['comment'] = pending_comment
                        if attributes:
                            p['attributes'] = attributes
                        p['data'] = {}

                    # Reset pending_comment and update the stack
                    pending_comment = None
                    stack.append(current_section)
                    current_section = current_section[name]["data"]
                elif "struct.end" in line:
                    # End the current structure
                    if stack:
                        current_section = stack.pop()
                else:
                    if "=" in line:
                        # Parse key-value pairs with type conversion
                        key, value = map(str.strip, line.split("=", 1))
                        converted_value = self._convert_type(value)
                        if converted_value is not None:  # Exclude empty values
                            current_section[key] = converted_value

        return self.data

    def _parse_struct_begin(self, line):
        """Parses a 'struct.begin' line to extract the structure name and its attributes."""
        parts = line.split(":", 1)
        name = parts[0].strip()
        attributes = {}
        if len(parts) > 1 and "{" in parts[1]:
            attr_string = parts[1].split("{", 1)[1].split("}", 1)[0]
            attributes = dict(
                map(str.strip, attr.split("=")) for attr in attr_string.split(";") if "=" in attr
            )
        return name, attributes

    def _convert_type(self, value):
        """
        Detects the type of the input value and converts it to int, float, or None.
        Excludes empty values.
        """
        if not value:  # Exclude empty strings
            return None
        if value == "None":  # Convert "None" to Python None
            return None

        # Only handle numbers with 'f' suffix (without affecting strings)
        if re.match(r"^-?\d*\.?\d*f$", value):  # Match float-like values with 'f' at the end
            return float(value[:-1])  # Remove the 'f' and convert to float
    
        # If it's a valid number (int or float)
        if re.match(r"^-?\d*(\.\d+)?$", value):  # Match numbers
            return float(value) if '.' in value else int(value)

        return value


# -----------------------------------------------------------------

def export_markers():

    out = []

    lookup = {}

    # preload marker prototypes for names/radius
    package_path = 'Stalker2/Content/GameLite/GameData/MarkerPrototypes.cfg'
    filename = os.path.normpath(os.path.join(cache_dir, package_path))
    parser = UnrealCFGParser(filename)
    cfg = parser.parse()
    for cfg_id, config in cfg.items():
        data = config.get('data',{})
        sid = data.get('SID')
        if sid:
            lookup[sid] = {}
            e = lookup[sid]
            remap = {'MarkerRadius':'radius', 'Title':'title', 'Description':'info'}
            for k,v in remap.items():
                if k in data and data[k]!=0 and data[k]!='Empty':
                    e[v] = data[k]

    folders = [
        'Stalker2/Content/GameLite/DLCGameData',
        'Stalker2/Content/GameLite/GameData',
    ]

    def getCoordinates(data):
        pts = data
        coord = [pts[k] for k in('PositionX','PositionY','PositionZ')if k in pts]
        if coord: return coord

        pts = data.get('WorldPosition',{}).get('data',{})
        coord =  [pts[k] for k in('X','Y','Z')if k in pts]
        if coord: return coord

        pts = data.get('PlayerLocation',{}).get('data',{})
        coord =  [pts[k] for k in('X','Y','Z')if k in pts]
        if coord: return coord

    def dataCleanup(data):
        # remove already used keys
        rk = ('PositionX','PositionY','PositionZ')
        if all(k in data for k in rk):
            for k in rk:
                del data[k]

        # remove scale section with default values
        rk = ('ScaleX','ScaleY','ScaleZ')
        if all(k in data and data[k]==1 for k in rk):
            for k in rk:
                del data[k]

        # remove zero rotators
        rk = ('RotatorAngleYaw','RotatorAnglePitch','RotatorAngleRoll')
        for k in rk:
            if k in data and data[k]==1:
                del data[k]

    ### Parse

    features = []

    for folder in folders:
        g = list(glob.glob(os.path.join(cache_dir, f'{folder}/**/*.cfg'),recursive=True))
        processed = 0
        total = len(g)
        rejected = [];

        print('found', total, '.cfg files in', folder)

        for filename in g:

            #if '409C17AD468C39F8C605079F41519092.cfg' not in filename: continue
            #if '4B56C32544C5470C2D7DFD89F59BBB8F' not in filename: continue
            #if 'C1EEB89C4D27EE16CAC1A2BC85378947' not in filename: continue
            #if 'D9D900F442E53F6922A64E939CB27E3B.cfg' not in filename: continue
            #if 'MarkerPrototypes.cfg' not in filename: continue
            #if 'FastTravelLocationPrototypes.cfg' not in filename: continue
            #if '105F11AB4ED95DD96B4D8BA45A8F2EB8.cfg' not in filename: continue

            # ignore all the files that don't have WorldMap_WP in the name

            # if 'WorldMap_WP' not in filename: continue # looks like it deletes some quests items we need, e.g. CA_Quest_Hub_Medic


            parser = UnrealCFGParser(filename)
            cfg = parser.parse()
            #print(json.dumps(cfg, indent=2))

            for cfg_id, config in cfg.items():

                data = type(config) is dict and config.get('data')
                if not data:
                    continue

                spawnType = data.get('SpawnType')
                shortName = spawnType and spawnType.split('::').pop() or data.get('Name') or data.get('SID') or 'Unnamed'

                titles = ('PackOfItemsPrototypeSID','SpawnedPrototypeSID','MarkerSID','ContextualActionSID','LairPrototypeSID','TriggerShape')
                title = next((data[t] for t in titles if t in data), shortName)

                description = spawnType or data.get('RegionType') or ('FastTravel' in filename and 'Custom::FastTravel') or 'Unknown'

                allowed_types = ['ESpawnType::Item','ESpawnType::Obj','ESpawnType::Marker','ESpawnType::Anomaly',
                    'ESpawnType::ElectroAnomaly','ESpawnType::AnomalySpawner','ESpawnType::SoapBubbleAnomaly'
                    'ESpawnType::LairSpawner','ESpawnType::Obj','ESpawnType::DeadBody','ESpawnType::ItemContainer'
                    'Custom::FastTravel','Region::'
                    ]

                #add_properties = True # adds config data to markers (disabled, because it's really a lot of data)
                add_properties = False

                #if all(s not in description for s in allowed_types): continue # filter markers (20k with this line, 60k without)


                if spawnType =='ESpawnType::DestructibleObject': continue # fuck destructible objects, too many


                coord = getCoordinates(data)
                if not coord or all(x==0 for x in coord):
                    rejected.append(1) # collect rejected later
                    continue

                name = os.path.split(filename)[1]

                prop = { 'title': title, 'description': description }

                #area = data.get('LevelName')
                #if area and 'WorldMap_WP' not in area:
                #    continue
                #if area: prop['area'] = area


                sid = data.get('SID')
                if sid:
                    prop['sid'] = sid

                '''
                dataCleanup(data) # remove unnecessary keys from config data

                if add_properties:
                    for key in data.keys():
                        s = data.get(key)
                        if s and type(s) is not dict:
                            prop[key] =  s

                #print(json.dumps(v, indent=2))

                #prop['config'] = config
                prop['file'] = filename.replace("\\","/").replace(cache_dir + '/Stalker2/Content/GameLite/','')
                '''

                clue = data.get('ClueVariablePrototypeSID')
                if clue and clue != 'EmptyInherited':
                    prop['clue'] = clue

                # ----------------
                # export references for item generators

                ranks = defaultdict(list)

                # don't need 'ItemSID', 'PackOfItemsPrototypeSID' - it's in the title
                for stash_sid in ('StashPrototypeSID', 'CorpseStashSID'):
                    stash = data.get(stash_sid)
                    if stash:
                        for x in stash.split(','):
                            ranks['any'].append(x.strip())

                gs = data.get('ItemGeneratorSettings',{}).get('data',{})
                for g in gs.values():
                    d = g.get('data',{}).get('ItemGenerators',{}).get('data',{})
                    rank = g.get('data',{}).get('PlayerRank','any')
                    if d:
                        protos = []
                        for t in d.values():
                            x = t.get('data',[]).get('PrototypeSID')
                            if x:
                                ranks[rank].append(x.strip())

                # let's encode it to tags

                rank_prefix = {
                    'ERank::Newbie':'0:',
                    'ERank::Experienced':'1:',
                    'ERank::Veteran':'2:',
                    'ERank::Master':'3:',
                }

                tags = []
                for rank, ids in ranks.items():
                    for s in ids:
                        tags.append( rank_prefix.get(rank,'')+s )

                if tags: prop['spawns'] = tags

                # ------------------

                # update marker properties from lookup
                for key in ['SpawnedPrototypeSID']:
                    if key in data and data[key] in lookup:
                        prop |= lookup[ data[key] ]
                        #print(prop)

                o = {'type':'Feature','geometry':{'type':'Point', 'coordinates': coord }, 'properties': prop};

                features.append(o)

            processed += 1
            sys.stderr.write(f'file {processed} of {total}, {len(features)} markers, {len(rejected)} rejected (no coordinates)   \r')

    print()
    print('collected %d markers, %d rejected' % (len(features), len(rejected)))
    print()

    out.extend(features)

    json_file = 'markers.json'
    print('writing "%s" ...' % json_file)
    json.dump({'type':'FeatureCollection','features': out}, open(json_file,'w'), indent=2)

if __name__ == '__main__':
    export_markers()
