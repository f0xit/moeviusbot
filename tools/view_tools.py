import logging
from enum import Enum
from typing import Optional

import discord


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
