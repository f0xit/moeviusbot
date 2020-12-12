import discord
from discord.ext import commands
import json
import random
import asyncio

from myfunc import log, load_file, gcts

def setup(bot):
    bot.add_cog(Quiz(bot))
    log("Cog: Quiz geladen.")

# Check for user is Super User
def isSuperUser():
    settings = load_file('settings')

    async def wrapper(ctx):
        return ctx.author.name in settings['super-users']
    return commands.check(wrapper)

class Quiz(commands.Cog, name='Quiz'):
    def __init__(self, bot):
        self.bot = bot

        self.player = None
        self.channel = None
        self.gameStage = 0
        self.question = None

        self.stages = [50, 100, 200, 300, 500,
                1000, 2000, 4000, 8000, 16000,
                32000, 64000, 125000, 250000, 500000, 1000000]

        log("Game-Stages geladen.")

    async def getRandomQuestion(self):
        while True:
            q = random.choice(self.quiz)
            
            if self.stages[self.gameStage] >= q['range'][0] and self.stages[self.gameStage] <= q['range'][1]:
                random.shuffle(q['answers'])

                self.question = {"question": q['question'],
                            "category": q['category'],
                            "answers": dict(zip(['A', 'B', 'C', 'D'], q['answers']))
                        }

                return

    async def getQuestionOutput(self):
        embed = discord.Embed(
                title=self.question['question'], 
                colour=discord.Colour(0xff00ff), 
                description="\n".join([
                        *map(lambda a: f"{a[0]}: {a[1]['text']}", 
                        self.question['answers'].items())
                    ])
            )
        return({
                "content": f"**Frage {self.gameStage + 1} - {self.stages[self.gameStage]}🕊**\nKategorie: {self.question['category']}",
                "embed": embed
            })

    async def stopQuiz(self):
        self.player = None
        self.channel = None
        self.gameStage = 0

    async def updateRanking(self, amount):
        ranking = {}
        id = str(self.player.id)

        try:
            with open(f'quiz_ranking.json', 'r') as f:
                ranking = json.load(f)
        finally:
            with open(f'quiz_ranking.json', 'w') as f:
                try:
                    ranking[id]['name'] = self.player.display_name
                    ranking[id]['points'] += amount
                    ranking[id]['tries'] += 1
                except KeyError:
                    ranking[id] = {
                        "name": self.player.display_name,
                        "points": amount,
                        "tries": 1
                    }

                json.dump(ranking, f)

    # Commands
    @commands.group(
        name='quiz',
        brief='Startet eine Quiz Runde'
    )
    async def _quiz(self, ctx):
        if ctx.invoked_subcommand is None:
            if self.player is not None:
                await ctx.send(f"Aktuell läuft bereits ein Spiel mit {self.player.display_name}. Ein Super-User kann das laufende Spiel mit !quiz stop beenden.")
            else:
                self.player = ctx.author
                self.channel = ctx.channel
                self.gameStage = 0

                with open(f'quiz.json', 'r') as f:
                    self.quiz = json.load(f)

                await ctx.send(f"Hallo und herzlich Willkommen zu Wer Wird Mövionär! Heute mit dabei: {self.player.display_name}. Los geht's, Krah Krah!")
                await self.getRandomQuestion()
                output = await self.getQuestionOutput()
                await ctx.send(content=output['content'], embed=output['embed'])
    
    @isSuperUser()
    @_quiz.command(
        name='stop',
        aliases=['-s'],
        brief='Beendet das laufende Quiz.'
    )
    async def _stop(self, ctx):
        if self.player is not None:
            await ctx.send(f"Das laufende Quiz wurde abgebrochen. {self.player.display_name} geht leider leer aus, Krah Krah!")
            await self.stopQuiz()
        else:
            await ctx.send("Bist du sicher? Aktuell läuft gar kein Quiz, Krah Krah!")

    @_quiz.command(
        name='report',
        aliases=['-r'],
        brief='Meldet eine Frage als unpassend/falsch/wasauchimmer.',
        usage='report <Grund>'
    )
    async def _report(self, ctx, *args):
        with open(f'logs/quiz_report.log', 'a+') as f:
            f.write(f"[{gcts()}] {ctx.author.name}: Grund: {' '.join(args)} - Frage: {self.question['question']}\n")

        await ctx.send("Deine Meldung wurde abgeschickt.")

        if self.player is not None:
            await self.getRandomQuestion()
            output = await self.getQuestionOutput()
            await self.channel.send(content=output['content'], embed=output['embed'])

    @_quiz.command(
        name='rank',
        brief='Zeigt das Leaderboard an.'
    )
    async def _rank(self, ctx):
        with open(f'quiz_ranking.json', 'r') as f:
            ranking = json.load(f)
            sortedRanking = {k: v for k, v in sorted(
                ranking.items(), key=lambda item: item[1]['points'], reverse=True
            )}

            maxlength = {"name": 0, "points": 0}
            for item in sortedRanking.items():
                name = len(self.bot.get_user(int(item[0])).display_name)
                points = len(format(item[1]['points'],',d'))

                if maxlength['name'] < name:
                    maxlength['name'] = name

                if maxlength['points'] < points:
                    maxlength['points'] = points

            embed = discord.Embed(
                title="Punktetabelle Quiz", 
                colour=discord.Colour(0xff00ff), 
                description="```" + "\n".join([
                    *map(
                        lambda a: (
                            f"{self.bot.get_user(int(a[0])).display_name}".ljust(maxlength['name'] + 4, ' ')
                            + f"{format(a[1]['points'],',d').replace(',','.')}🕊 ".rjust(maxlength['points'] + 4, ' ')
                            + f"{a[1]['tries']} Versuch{'' if a[1]['tries'] == 1 else 'e'}".rjust(14, ' ')
                        ), sortedRanking.items()
                    )
                ]) + "```"
            )

            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.player == message.author and message.channel == self.channel:
            userAnswer = message.content.title()

            if userAnswer in ['A', 'B', 'C', 'D']:
                if self.question['answers'][userAnswer]['correct']:
                    await self.channel.send("✅ Richtig!\n")

                    if self.gameStage == 15:
                        await self.channel.send(f"Du hast {self.stages[15]}🕊 gewonnen!!!")

                        await self.updateRanking(self.stages[15])
                        await self.stopQuiz()
                    else:
                        if self.gameStage == 4:
                            await self.channel.send(f"❗️ Checkpoint erreicht: {self.stages[4]}🕊.")
                        elif self.gameStage == 9:
                            await self.channel.send(f"❗️ Checkpoint erreicht: {self.stages[9]}🕊.")

                        self.gameStage += 1

                        await self.getRandomQuestion()
                        output = await self.getQuestionOutput()
                        await self.channel.send(content=output['content'], embed=output['embed'])
                else:
                    await self.channel.send("❌ Falsch!")

                    for a in self.question['answers'].items():
                        if a[1]['correct']:
                            await self.channel.send(f"Die richtige Antwort ist {a[0]}: {a[1]['text']}")

                    if self.gameStage <= 4:
                        await self.channel.send("Du verlässt das Spiel ohne Gewinn.")
                        await self.updateRanking(0)
                    elif self.gameStage > 9:
                        await self.channel.send(f"Du verlässt das Spiel mit {self.stages[9]}🕊.")
                        await self.updateRanking(self.stages[9])
                    elif self.gameStage > 4:
                        await self.channel.send(f"Du verlässt das Spiel mit {self.stages[4]}🕊.")
                        await self.updateRanking(self.stages[4])

                    await self.stopQuiz()
            elif userAnswer == "Q":
                if self.gameStage == 0:
                    await self.channel.send("Du verlässt das Spiel ohne Gewinn.")
                    await self.updateRanking(0)
                else:
                    await self.channel.send(f"Du verlässt das Spiel freiwillig mit {self.stages[self.gameStage - 1]}🕊.")
                    await self.updateRanking(self.stages[self.gameStage - 1])
                    
                for a in self.question['answers'].items():
                    if a[1]['correct']:
                        await self.channel.send(f"Die richtige Antwort ist {a[0]}: {a[1]['text']}")
                        
                await self.stopQuiz()