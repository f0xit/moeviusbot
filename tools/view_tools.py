"""This tool contains functions an classes that help working with discord views."""

from __future__ import annotations

from typing import Any

import discord

Choice = tuple[str, str]
Choices = list[Choice]


def emoji_from_asciilo(ch: str) -> str:
    """Transforms lowercase ascii chars into corresponding regional indicator."""
    return chr(0x1F1E6 + ord(ch) - 97)


class PollView(discord.ui.View):
    """Represents a special discord view that contains buttons for polls."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    def buttons_from_choices(self, new_poll_id: str, choices: Choices) -> PollView:
        """Populates the view with buttons from a list of choices. Returns itself for daisy chaining."""

        for choice in choices:
            self.add_item(PollButton(choice, new_poll_id))

        return self

    def buttons_from_collection(
        self, choices: dict[str, str], votes: dict[str, list], poll_id: str, iteration: Any
    ) -> PollView:
        """Populates the view with buttons from a collection. Returns itself for daisy chaining."""

        for choice in choices.items():
            vote_count = len([item for row in votes.values() for item in row if item == choice[0]])

            iteration = int(iteration) + 1

            self.add_item(PollButton(choice, poll_id, vote_count, iteration))

        return self

    def deactivate_buttons_from_collection(self, choices: dict[str, str], votes: dict[str, list]) -> PollView:
        """Populates the view with deactivated buttons. Returns itself for daisy chaining."""

        for choice in choices.items():
            vote_count = len([item for row in votes.values() for item in row if item == choice[0]])

            self.add_item(InactivePollButton(choice, vote_count))

        return self


class PollButton(discord.ui.Button):
    """Represents special discord buttons that are used in polls."""

    def __init__(
        self,
        choice: tuple[str, str],
        poll_id: str,
        vote_count: int = 0,
        iteration: int = 0,
    ) -> None:
        choice_id, choice_text = choice

        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"[{vote_count}] {choice_text}",
            emoji=emoji_from_asciilo(choice_id),
            custom_id=f"moevius:poll:{poll_id}:choice:{choice_id}:iteration:{iteration}",
        )


class InactivePollButton(discord.ui.Button):
    """Represents special discord buttons that are used in polls. Inactive by design."""

    def __init__(
        self,
        choice: tuple[str, str],
        vote_count: int = 0,
    ) -> None:
        choice_id, choice_text = choice

        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"[{vote_count}] {choice_text}",
            emoji=emoji_from_asciilo(choice_id),
            disabled=True,
        )
