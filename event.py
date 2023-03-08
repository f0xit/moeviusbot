'''This module contains the event class'''
import logging

from discord import Member, User

from tools import json_tools


class Event:
    """This class is used for events like streams or coop sessions
    """

    def __init__(self, event_type: str) -> None:
        self.event_type = event_type
        self.event_time = ''
        self.event_game = ''
        self.event_members = {}

        self.load()

    def update_event(self, event_time: str, event_game: str) -> None:
        """Updates the event.

        Args:
            event_time (str): Format is HH:MM
            event_game (str): Name of the game played/streamed
        """
        self.event_time = event_time
        self.event_game = event_game

        self.save()

    def add_member(self, new_member: User | Member) -> None:
        """Adds a member to the event

        Args:
            new_member (User | Member): The added member
        """
        if new_member.id in self.event_members:
            return

        self.event_members[new_member.id] = new_member.display_name
        self.save()

    def reset(self) -> None:
        """Resets all instance attributes
        """
        self.event_time = ''
        self.event_game = ''
        self.event_members = {}

        self.save()

    def save(self) -> None:
        """Saves the event to a json-file
        """
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
        """Loads the event from a json-file if possible
        """
        if (data := json_tools.load_file(self.event_type + '.json')) is None:
            logging.error(
                'Event could not be loaded!'
            )
            return

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
