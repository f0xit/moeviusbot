# Helper Functions
from datetime import datetime
import json

# Timestamps for timing
def gcts():
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

# A tiny custom logger for console output and log-files
def log(inputstr):
    print('[' + gcts() + '] ' + inputstr)
    with open('logs/' + datetime.now().strftime('%Y-%m-%d') + '_moevius.log', 'a') as f:
        f.write('[' + gcts() + '] ' + inputstr + '\n')

# A quick and dirty load function for .json-files
def load_file(name):
    with open(f'{name}.json', 'r') as f:
        return json.load(f)