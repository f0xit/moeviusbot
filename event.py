#Event-Class

import json
from myfunc import log

class Event:    
    def __init__ (self, name):
        self.name = name
        self.time = ''
        self.game = ''
        self.members = {}
        
    def updateStream(self, time):
        self.time = time
        self.save()
        
    def updateGame(self, time, game):
        self.time = time
        self.game = game
        self.save()

    def addMember(self, member):
        self.members[member.id] = member.display_name
        self.save()
        
    def reset(self):
        self.time = ''
        self.game = ''
        self.members = {}
        self.save()
            
    def save(self):
        with open(self.name + '.json', 'w') as f:
            json.dump(self.__dict__, f)
            
    def load(self):
        try:
            with open(self.name + '.json', 'r') as f:
                data = f.read()
                self.time = json.loads(data)['time']
                log(f'Event-Zeit für {self.name} wurde geladen: {self.time}')
                if self.name == 'game':
                    self.game = json.loads(data)['game']
                    log(f'Event-Game für {self.name} wurde geladen: {self.game}')
                self.members = json.loads(data)['members']
                log(f'Event-Members für {self.name} wurden geladen: {self.members}')
        except:
            pass
            log(f'Event {self.name} konnte nicht geladen werden und bleibt bei: {self.time} - {self.game}')