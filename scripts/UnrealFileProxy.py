# (c) 2025 Joric, https://github.com/joric/stalker
# install UE4Parse module: pip install git+https://github.com/MinshuG/pyUE4Parse.git
# install dependencies: pip install mathutils aes
# see wiki for more info https://github.com/joric/stalker/wiki

from UE4Parse.Assets.Objects.FGuid import FGuid
from UE4Parse.Provider import DefaultFileProvider, MappingProvider
from UE4Parse.Versions import EUEVersion, VersionContainer
from UE4Parse.Encryption import FAESKey
import logging, gc, json, gc, os, sys, csv, argparse, tempfile

class UnrealFileProxy:
    def __init__(self, path, key='0x'+'0'*64, usmap_file=None, version=None):

        print("Loading", path)

        logging.getLogger("UE4Parse").setLevel(logging.ERROR)
        aeskeys = { FGuid(0,0,0,0): FAESKey(key), }
        gc.disable()
        version = EUEVersion.LATEST
        provider = DefaultFileProvider(path, VersionContainer(version))
        provider.initialize()
        provider.submit_keys(aeskeys)
        provider.load_localization("en")
        gc.enable()

        if usmap_file:
            provider.mappings = usmap_file

        print('Total files in paks', sum(1 for x in provider.files))

        self.provider = provider

    def load(self, path):
        package = self.provider.try_load_package(path)
        if package is not None:
            #print('Loading', path)
            return package.get_dict()
        else:
            print('Could not load', path)

    def save_json(self, path, filename):
        # fails with "UE4Parse\Assets\Exports\World.py", line 30, in GetValue
        # props["PersistentLevel"] = self.PersistentLevel.GetValue() AttributeError: 'UWorld' object has no attribute 'PersistentLevel'
        # d = p.load('Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP.umap')
        data = self.load(path)

        #print('saving', filename)

        directory_to_create = os.path.dirname(filename)
        os.makedirs(directory_to_create, exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def save_paths(self, filename):
        paths = []
        for key, entry in self.provider.files:
            name = ''.join([key, os.path.splitext(entry.Name)[-1]])
            '''
            if type(entry) is FIoStoreEntry:
                x = {
                    'name': name,
                    #'type': type(entry),
                    'pak': entry.ContainerName,
                    'size': entry.Length,
                    'encrypted': entry.Encrypted,
                }
            else:
                x = {
                    'name': name,
                    #'type': type(entry),
                    'pak': entry.Container.FileName,
                    'size': entry.Size,
                    'encrypted': entry._Encrypted,
                }
            '''
            #paths.append(name)#' '.join(str(x[key]) for key in('size','pak','name')))

            if '_Generated_' in name:
                paths.append(name)

        print('saving', len(paths), 'paths')
        with open('filenames.txt', 'w') as f:
            f.write('\n'.join(paths))

def main():
    p = UnrealFileProxy(
        'E:/Games/S.T.A.L.K.E.R. 2.Heart.of.Chornobyl.Ultimate.Editon-InsaneRamZes/Stalker2/Content/Paks',
        '0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386',
        'D:/Shared/Tools/Hacking/Games/UE/FModel/Stalker2.Mappings.usmap',
    )

    p.save_json('Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP/_Generated_/Architecture_L0_X-10Y-1_DL0.umap', 'out.json')
    p.save_paths('filenames.txt')


if __name__ == '__main__':
    main()

