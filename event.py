#Event-Class

import json
from myfunc import log

class Event:
    def __init__ (self, event_type):
        self.event_type = event_type
        self.event_time = ''
        self.event_game = ''
        self.event_members = {}

        self.load()

    def update_event(self, event_time, event_game):
        self.event_time = event_time
        self.event_game = event_game

        self.save()

    def add_member(self, new_member):
        if new_member.id not in self.event_members.keys():
            self.event_members[new_member.id] = new_member.display_name
            self.save()

    def reset(self):
        self.event_time = ''
        self.event_game = ''
        self.event_members = {}

        self.save()

    def save(self):
        with open(self.event_type + '.json', 'w') as file:
            json.dump(self.__dict__, file)

        log(f'Event wurde gespeichert: {self.event_type} - {self.event_game} - '
            + f'{",".join(self.event_members.values())} - {self.event_time}')

    def load(self):
        try:
            with open(self.event_type + '.json', 'r') as file:
                data = file.read()

                self.event_time = json.loads(data)['eventTime']
                self.event_game = json.loads(data)['eventGame']
                self.event_members = json.loads(data)['eventMembers']

                log(f'Event wurde geladen: {self.event_type} - {self.event_game} - '
                    + f'{",".join(self.event_members.values())} - {self.event_time}')
        except IOError:
            log(f'Event {self.event_type} konnte nicht geladen werden!')
