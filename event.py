#Event-Class

import json
from myfunc import log

class Event:
    name = ''
    time = ''
    game = ''
    
    def __init__ (self, name):
        self.name = name
        
    def updateStream(self, time):
        self.time = time
        self.save()
        
    def updateGame(self, time, game):
        self.time = time
        self.game = game
        self.save()
        
    def reset(self):
        self.time = ''
        self.game = ''
        self.save()
            
    def save(self):
        with open(self.name + '.json', 'w') as f:
            json.dump(self.__dict__, f)
            
    def load(self):
        try:
            with open(self.name + '.json', 'r') as f:
                self.time = json.load(f)['time']
                log(f'Event-Zeit für {self.name} wurde geladen: {self.time}')
                self.game = json.load(f)['game']
                log(f'Event-Name für {self.name} wurde geladen: {self.game}')

        except:
            pass
            log(f'Event {self.name} konnte nicht geladen werden und bleibt bei: {self.time} - {self.game}')