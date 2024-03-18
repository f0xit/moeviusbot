from __future__ import annotations

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
