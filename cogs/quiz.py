"""Quiz module"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tools.check_tools import is_super_user
from tools.json_tools import load_file, save_file

if TYPE_CHECKING:
    from bot import Bot


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Quiz(bot))
    logging.info("Cog: Quiz geladen.")


class QuizError(Exception):
    pass


class Quiz(commands.Cog, name="Quiz"):
    """Quiz cog"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.player: discord.Member | None = None
        self.channel: discord.TextChannel | None = None
        self.game_stage: int = 0
        self.question: dict[str, dict] = {}
        self.quiz: list | None = None

        self.stages = [
            50,
            100,
            200,
            300,
            500,
            1000,
            2000,
            4000,
            8000,
            16000,
            32000,
            64000,
            125000,
            250000,
            500000,
            1000000,
        ]

        logging.debug("Game-Stages geladen.")

    async def get_random_question(self) -> None:
        """_summary_"""

        if self.quiz is None:
            msg = "Quiz data not found!"
            raise QuizError(msg)

        while True:
            question = random.SystemRandom().choice(self.quiz)

            if (
                self.stages[self.game_stage] >= question["range"][0]
                and self.stages[self.game_stage] <= question["range"][1]
            ):
                random.shuffle(question["answers"])

                self.question = {
                    "question": question["question"],
                    "category": question["category"],
                    "answers": dict(zip(["A", "B", "C", "D"], question["answers"], strict=True)),
                }

                return

    async def get_question_output(self) -> dict[str, str | discord.Embed] | None:
        """_summary_

        Returns:
            dict[str, Any]: _description_"""

        if not isinstance(self.question["answers"], dict):
            return None

        embed = discord.Embed(
            title=self.question["question"],
            colour=discord.Colour(0xFF00FF),
            description="\n".join([f"{a[0]}: {a[1]['text']}" for a in self.question["answers"].items()]),
        )
        return {
            "content": f"**Frage {self.game_stage + 1} - "
            f"{self.stages[self.game_stage]}🕊**\n"
            f"Kategorie: {self.question['category']}",
            "embed": embed,
        }

    async def check_answer(self, user_answer: str) -> None:
        if self.channel is None or not isinstance(self.question["answers"], dict):
            return

        if self.question["answers"][user_answer]["correct"]:
            await self.channel.send("✅ Richtig!\n")

            if self.game_stage == 15:  # noqa: PLR2004
                await self.channel.send(f"Du hast {self.stages[15]}🕊 gewonnen!!!")

                await self.update_ranking(self.stages[15])
                await self.stop_quiz()

                return

            if self.game_stage in [4, 9]:
                await self.channel.send(f"❗️ Checkpoint erreicht: {self.stages[self.game_stage]}🕊.")

            self.game_stage += 1

            await self.get_random_question()
            output = await self.get_question_output()

            if output is None or not (
                isinstance(output["content"], str) and isinstance(output["embed"], discord.Embed)
            ):
                return

            await self.channel.send(content=output["content"], embed=output["embed"])

        else:
            await self.channel.send("❌ Falsch!")

            correct_answer = next(answer for answer in self.question["answers"].items() if answer[1]["correct"])

            await self.channel.send(f"Die richtige Antwort ist {correct_answer[0]}: {correct_answer[1]['text']}")

            if self.game_stage <= 4:  # noqa: PLR2004
                await self.channel.send("Du verlässt das Spiel ohne Gewinn.")
                await self.update_ranking(0)
            elif self.game_stage > 9:  # noqa: PLR2004
                await self.channel.send(f"Du verlässt das Spiel mit {self.stages[9]}🕊.")
                await self.update_ranking(self.stages[9])
            elif self.game_stage > 4:  # noqa: PLR2004
                await self.channel.send(f"Du verlässt das Spiel mit {self.stages[4]}🕊.")
                await self.update_ranking(self.stages[4])

            await self.stop_quiz()

    async def stop_quiz(self) -> None:
        """_summary_"""

        self.player = None
        self.channel = None
        self.game_stage = 0

    async def update_ranking(self, amount: int) -> None:
        """_summary_

        Args:
            amount (int): _description_"""

        if self.player is None:
            return

        player_id = str(self.player.id)

        ranking = load_file("json/quiz_ranking.json")

        if not isinstance(ranking, dict):
            return

        ranking[player_id]["name"] = self.player.display_name
        ranking[player_id]["points"] = ranking[player_id].get("points") + amount
        ranking[player_id]["tries"] = ranking[player_id].get("tries") + 1

        save_file("json/quiz_ranking.json", ranking)

    @commands.group(name="quiz", brief="Startet eine Quiz Runde")
    async def _quiz(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is not None:
            return

        if self.player is not None:
            await ctx.send(
                "Aktuell läuft bereits ein Spiel mit "
                + self.player.display_name
                + ". Ein Super-User kann das laufende Spiel mit "
                + "!quiz stop beenden."
            )
            return

        if not isinstance(ctx.author, discord.Member) or not isinstance(ctx.channel, discord.TextChannel):
            return

        self.player = ctx.author
        self.channel = ctx.channel
        self.game_stage = 0

        quiz = load_file("json/quiz.json")

        if not isinstance(quiz, list):
            return

        self.quiz = quiz

        await ctx.send(
            "Hallo und herzlich Willkommen zu Wer Wird Mövionär! "
            f"Heute mit dabei: {self.player.display_name}."
            "Los geht's, Krah Krah!"
        )

        await self.get_random_question()
        output = await self.get_question_output()

        if output is None or not (isinstance(output["content"], str) and isinstance(output["embed"], discord.Embed)):
            return

        await ctx.send(content=output["content"], embed=output["embed"])

    @is_super_user()
    @_quiz.command(name="stop", aliases=["-s"], brief="Beendet das laufende Quiz.")
    async def _stop(self, ctx: commands.Context) -> None:
        if self.player is None:
            await ctx.send("Bist du sicher? Aktuell läuft gar kein Quiz, Krah Krah!")
            return

        await ctx.send(
            f"Das laufende Quiz wurde abgebrochen. {self.player.display_name} geht leider leer aus, Krah Krah!"
        )

        await self.stop_quiz()

    @_quiz.command(
        name="report",
        aliases=["-r"],
        brief="Meldet eine Frage als unpassend/falsch/wasauchimmer.",
        usage="report <Grund>",
    )
    async def _report(self, ctx: commands.Context, *args) -> None:  # noqa: ANN002
        with open("logs/quiz_report.log", "a+", encoding="utf-8") as file:  # noqa: ASYNC101, PTH123
            file.write(f"Grund: {' '.join(args)} - Frage: {self.question['question']}\n")

        await ctx.send("Deine Meldung wurde abgeschickt.")

        if self.player is None:
            return

        await self.get_random_question()
        output = await self.get_question_output()

        if output is None:
            return

        if not (isinstance(output["content"], str) and isinstance(output["embed"], discord.Embed)):
            return

        if self.channel is None:
            return

        await self.channel.send(content=output["content"], embed=output["embed"])

    @_quiz.command(name="rank", brief="Zeigt das Leaderboard an.")
    async def _rank(self, ctx: commands.Context) -> None:
        ranking = load_file("json/quiz_ranking.json")

        if not isinstance(ranking, dict):
            return

        sorted_ranking = dict(sorted(ranking.items(), key=lambda item: item[1]["points"], reverse=True))

        broken_users = []
        max_length = {"name": 0, "points": 0}
        for user_id, user_data in sorted_ranking.items():
            if (user := self.bot.get_user(int(user_id))) is None:
                broken_users.append(user_id)
                continue

            if (user_name := user.display_name) is None:
                broken_users.append(user_id)
                continue

            name_length = len(user_name)
            points = len(format(user_data["points"], ",d"))

            if max_length["name"] < name_length:
                max_length["name"] = name_length

            if max_length["points"] < points:
                max_length["points"] = points

        for user_id in broken_users:
            sorted_ranking.pop(user_id)

        await ctx.send(
            embed=discord.Embed(
                title="Punktetabelle Quiz",
                colour=discord.Colour(0xFF00FF),
                description="```"
                + "\n".join(
                    [
                        user.display_name.ljust(max_length["name"] + 4, " ")
                        + (format(item[1]["points"], ",d").replace(",", ".") + "🕊").rjust(max_length["points"] + 4, " ")
                        + (str(item[1]["tries"]) + "Versuche").rjust(14, " ")
                        for item in sorted_ranking.items()
                        if (user := self.bot.get_user(int(item[0]))) is not None
                    ]
                )
                + "```",
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """_summary_

        Args:
            message (discord.Message): _description_
        """
        if (
            self.channel is None
            or self.player != message.author
            or message.channel != self.channel
            or not isinstance(self.question["answers"], dict)
        ):
            return

        user_answer = message.content.title()

        match user_answer:
            case "A" | "B" | "C" | "D":
                await self.check_answer(user_answer)

            case "Q":
                await self.channel.send(
                    "Du verlässt das Spiel "
                    + (
                        "ohne Gewinn."
                        if self.game_stage == 0
                        else f"freiwillig mit {self.stages[self.game_stage - 1]}🕊."
                    )
                )

                if self.game_stage == 0:
                    await self.update_ranking(0)
                else:
                    await self.update_ranking(self.stages[self.game_stage - 1])

                correct_answer = next(answer for answer in self.question["answers"].items() if answer[1]["correct"])

                await self.channel.send(f"Die richtige Antwort ist {correct_answer[0]}: {correct_answer[1]['text']}")

                await self.stop_quiz()
