#event.py

import json
#Event-Class
class Event:
    name = ''
    time = ''
    
    def __init__ (self, name):
        self.name = name
        
    def update(self, time):
        self.time = time
        
    def reset(self):
        self.time = ''
        
    def save(self):
        with open(self.name + '.json', 'w') as f:
            json.dump(self.__dict__, f)
            
    def load(self):
        with open(self.name + '.json', 'r') as f:
            self.time = json.load(f)['time']