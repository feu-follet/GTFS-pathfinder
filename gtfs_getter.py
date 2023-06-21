from requests import get
from os import remove,listdir
from zipfile import ZipFile

_FOLDER = "gtfs/"
_URL = 'https://eu.ftp.opendatasoft.com/sncf/gtfs/export-ter-gtfs-last.zip'

def get_latest():
    for file in listdir(_FOLDER):
        remove(_FOLDER+file)
    
    r = get(_URL, allow_redirects=True)
    open(_FOLDER+'gtfs_last.zip', 'wb').write(r.content)
    
    with ZipFile(_FOLDER+"gtfs_last.zip", 'r') as zObject:
        zObject.extractall(path=_FOLDER)
    
    remove(_FOLDER+'gtfs_last.zip')
