from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

import discord


class PollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def buttons_from_choices(self, new_poll_id, choices) -> PollView:
        for choice in choices:
            self.add_item(PollButton(choice, new_poll_id))

        return self

    def buttons_from_collection(self, choices, votes, poll_id, iteration) -> PollView:
        for choice in choices.items():
            vote_count = len([item for row in votes.values() for item in row if item == choice[0]])

            iteration = int(iteration) + 1

            self.add_item(PollButton(choice, poll_id, vote_count, iteration))

        return self

    def deactivate_buttons_from_collection(self, choices, votes, poll_id) -> PollView:
        for choice in choices.items():
            vote_count = len([item for row in votes.values() for item in row if item == choice[0]])

            self.add_item(InactivePollButton(choice, poll_id, vote_count))

        return self


class PollButton(discord.ui.Button):
    def __init__(
        self,
        choice: tuple[str, str],
        poll_id: str,
        vote_count: int = 0,
        iteration: int = 0,
    ):
        self.choice_id = choice[0]
        self.choice_text = choice[1]
        self.poll_id = poll_id

        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"{self.choice_text} ({vote_count})",
            emoji=chr(0x1F1E6 + ord(self.choice_id) - 97),
            custom_id=f"moevius:poll:{self.poll_id}:choice:{self.choice_id}:iteration:{iteration}",
        )


class InactivePollButton(discord.ui.Button):
    def __init__(
        self,
        choice: tuple[str, str],
        poll_id: str,
        vote_count: int = 0,
    ):
        self.choice_id = choice[0]
        self.choice_text = choice[1]
        self.poll_id = poll_id

        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"{self.choice_text} ({vote_count})",
            emoji=chr(0x1F1E6 + ord(self.choice_id) - 97),
            disabled=True,
        )


class EventButtonAction(Enum):
    SAVE = "Ja, nur speichern."
    ANNOUNCE = "Ja, sofort ankündigen."
    ABORT = "Abbrechen."
    JOIN = "!join"


class EventButton(discord.ui.Button):
    def __init__(self, action: EventButtonAction):
        self.action = action

        if self.action == EventButtonAction.ABORT:
            style = discord.ButtonStyle.red
        else:
            style = discord.ButtonStyle.blurple

        super().__init__(style=style, label=self.action.value)

    async def callback(self, interaction: discord.Interaction):
        if self.view is None:
            return

        match self.action:
            case EventButtonAction.SAVE:
                await interaction.response.send_message(
                    "Alles klar, das Event wird gespeichert.",
                    ephemeral=True,
                )
                logging.info("Saving event by user [ID#%s]...", interaction.user.id)

            case EventButtonAction.ANNOUNCE:
                await interaction.response.send_message(
                    "Alles klar, das Event wird angekündigt.", ephemeral=True
                )
                logging.info("Announcing event by user [ID#%s]...", interaction.user.id)

            case EventButtonAction.ABORT:
                await interaction.response.send_message(
                    "Alles klar, das Event wird nicht gespeichert.", ephemeral=True
                )
                logging.info("Aborting event creation by user [ID#%s]...", interaction.user.id)

            case EventButtonAction.JOIN:
                await interaction.response.send_message(
                    "Alles klar, du wirst zum Event hinzugefügt.", ephemeral=True
                )
                logging.info("Joining event. by user [ID#%s]...", interaction.user.id)

        self.view.performed_action = self.action
        self.view.stop()
        logging.debug("Stopping view.")


class EventPreview(discord.ui.View):
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.performed_action: Optional[EventButtonAction] = None


class ViewBuilder:
    @classmethod
    def confirm_event_preview(cls) -> EventPreview:
        return (
            EventPreview()
            .add_item(EventButton(EventButtonAction.SAVE))
            .add_item(EventButton(EventButtonAction.ANNOUNCE))
            .add_item(EventButton(EventButtonAction.ABORT))
        )

    @classmethod
    def join_single_event(cls) -> discord.ui.View:
        return EventPreview(timeout=None).add_item(EventButton(EventButtonAction.JOIN))
