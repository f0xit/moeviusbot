import discord

from tools.json_tools import DictFile


class PollView(discord.ui.View):
    def __init__(self, new_poll_id, choices):
        super().__init__(timeout=None)

        for choice in choices:
            self.add_item(PollButton(choice, new_poll_id))


class PollButton(discord.ui.Button):
    def __init__(self, choice, poll_id):
        self.choice_id = choice[0]
        self.choice_text = choice[1]
        self.poll_id = poll_id

        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"{self.choice_text} (0)",
            emoji=chr(0x1F1E6 + ord(self.choice_id) - 97),
            custom_id=f"moevius:poll:{self.poll_id}:choice:{self.choice_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)

        polls = DictFile("polls")

        votes = polls[self.poll_id]["votes"]

        if user_id not in votes:
            votes[user_id] = [self.choice_id]
        elif self.choice_id not in votes[user_id]:
            votes[user_id].append(self.choice_id)
        else:
            votes[user_id].remove(self.choice_id)

        vote_count = len([item for row in votes.values() for item in row if item == self.choice_id])
        self.label = f"{self.choice_text} ({vote_count})"

        polls.save()

        if interaction.message:
            await interaction.followup.edit_message(interaction.message.id, view=self.view)

        await interaction.followup.send("Stimmabgabe erfolgreich!", ephemeral=True)
