import discord


class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


class PollView(PersistentView):
    def __init__(self, new_poll_id, choices):
        super().__init__()

        for choice in choices:
            self.add_item(PollButton(choice, new_poll_id))


class PollButton(discord.ui.Button):
    def __init__(self, choice, poll_id, vote_count: int = 0, iteration: int = 0):
        self.choice_id = choice[0]
        self.choice_text = choice[1]
        self.poll_id = poll_id

        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"{self.choice_text} ({vote_count})",
            emoji=chr(0x1F1E6 + ord(self.choice_id) - 97),
            custom_id=f"moevius:poll:{self.poll_id}:choice:{self.choice_id}:iteration:{iteration}",
        )
