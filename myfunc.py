# Helper Functions
from datetime import datetime
import json
import os

# Timestamps for loggin
def gcts():
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

# Format time delta for uptime
def strfdelta(tdelta, fmt):
    delta = {"days": tdelta.days}
    delta["hours"], rem = divmod(tdelta.seconds, 3600)
    delta["minutes"], delta["seconds"] = divmod(rem, 60)
    delta["minutes"] = str(delta["minutes"]).zfill(2)
    delta["seconds"] = str(delta["seconds"]).zfill(2)
    return fmt.format(**delta)

# A tiny custom logger for console output and log-files
def log(inputstr):
    print('[' + gcts() + '] ' + inputstr)
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs/' + datetime.now().strftime('%Y-%m-%d') + '_moevius.log', 'a+') as file:
        file.write('[' + gcts() + '] ' + inputstr + '\n')

# A quick and dirty load function for .json-files
def load_file(name):
    try:
        with open(f'{name}.json', 'r') as file:
            return json.load(file)
    except IOError:
        log(f'File {name} konnte nicht geladen werden!')
        return {}

def save_file(name, content):
    try:
        with open(f'{name}.json', 'w') as file:
            json.dump(content, file)
    except IOError:
        log(f'File {name} konnte nicht gespeichert werden!')
