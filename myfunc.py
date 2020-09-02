# Helper Functions
from datetime import datetime
import json
import os

# Timestamps for loggin
def gcts():
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

# Format time delta for uptime
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    d["minutes"] = str(d["minutes"]).zfill(2)
    d["seconds"] = str(d["seconds"]).zfill(2)
    return fmt.format(**d)

# A tiny custom logger for console output and log-files
def log(inputstr):
    print('[' + gcts() + '] ' + inputstr)
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs/' + datetime.now().strftime('%Y-%m-%d') + '_moevius.log', 'a+') as f:
        f.write('[' + gcts() + '] ' + inputstr + '\n')

# A quick and dirty load function for .json-files
def load_file(name):
    try:
        with open(f'{name}.json', 'r') as f:
            return json.load(f)
    except:
        log(f'File {name} konnte nicht geladen werden!')
        return {}

def save_file(name, content):
    try:
        with open(f'{name}.json', 'w') as f:
            json.dump(content, f)
    except:
        log(f'File {name} konnte nicht gespeichert werden!')