import logging
import tools.json_tools as json_tools
from discord import User, Member


class Event:
    def __init__(self, event_type: str) -> None:
        self.event_type = event_type
        self.event_time = ''
        self.event_game = ''
        self.event_members = {}

        self.load()

    def update_event(self, event_time: str, event_game: str) -> None:
        self.event_time = event_time
        self.event_game = event_game

        self.save()

    def add_member(self, new_member: User | Member) -> None:
        if new_member.id not in self.event_members.keys():
            self.event_members[new_member.id] = new_member.display_name
            self.save()

    def reset(self) -> None:
        self.event_time = ''
        self.event_game = ''
        self.event_members = {}

        self.save()

    def save(self) -> None:
        if json_tools.save_file(self.event_type + '.json', self.__dict__):
            logging.info(
                'Event saved. Type: %s - Name: %s - Time: %s - Members: %s',
                self.event_type,
                self.event_game,
                self.event_time,
                '.'.join(self.event_members.values())
            )
        else:
            logging.error(
                'Event could not be saved! Type: %s - Name: %s - Time: %s - Members: %s',
                self.event_type,
                self.event_game,
                self.event_time,
                '.'.join(self.event_members.values())
            )

    def load(self) -> None:
        if (data := json_tools.load_file(self.event_type + '.json')) != None:
            self.event_time = data['event_time']
            self.event_game = data['event_game']
            self.event_members = data['event_members']

            logging.info(
                'Event loaded. Type: %s - Name: %s - Time: %s - Members: %s',
                self.event_type,
                self.event_game,
                self.event_time,
                '.'.join(self.event_members.values())
            )
        else:
            logging.error(
                'Event could not be loaded!'
            )
