#Helper Functions
from datetime import datetime

#This is how you Get your Complete TimeStamp
def gcts():
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

#This is how you log it
def log(inputstr):
    print('[' + gcts() + '] ' + inputstr)
    with open('logs/' + datetime.now().strftime('%Y-%m-%d') + '_moevius.log', 'a') as f:
        f.write('[' + gcts() + '] ' + inputstr + '\n')