# Changelog

## 0.8.1

### Under the hood
As usual, most changes happened internally to achieve better type safety, improve the code style or performance or simply to try out new concepts.
- The main function in the main file is now asynchronous. https://github.com/f0xit/moeviusbot/commit/e872f9696430e6e0d0e262b8e1e29e048e5011e3
- All HTTP requests are now handled by a new helper tool that uses aiohttp. https://github.com/f0xit/moeviusbot/commit/383a3e47d37570ccf5620f989c625ea30571a5bf
- A new event_tools module was tested to improve many details in the reminder part of the bot. I'm still not sure wether .json-files are the way to go. Maybe a SQLite DB is the better option. https://github.com/f0xit/moeviusbot/commit/9bfa8033649470539cf38d8abd1b0196a2cc3280 https://github.com/f0xit/moeviusbot/commit/3e8fea320a7797b1b193c3c050565d9a64e4d756
- The gartic cog now uses a cache folder to achieve a cleaner root directory. https://github.com/f0xit/moeviusbot/commit/f6206e6bb04e61323d7553e5b6030cb08fd845c7
- The ps5 command has no longer a hard coded price for the PlayStation 5, it now fetches the actual price from Sony's website. https://github.com/f0xit/moeviusbot/commit/776ae7c524dbd35b44766560629b1115d94ed790
- I started to use ruff to improve the code style. https://github.com/f0xit/moeviusbot/commit/747f6c790910353e78d7e8672caa4cc03220001c https://github.com/f0xit/moeviusbot/commit/0a19ac22f59a6daac2ee11ab84edf010f086221e https://github.com/f0xit/moeviusbot/commit/0eb2d9aefce9639182bffc39357e973bb8be6e88
- Personally I'm a big fan of the result type in Rust so I started using a python package that implements this functionality https://github.com/f0xit/moeviusbot/commit/2ba3dcc16589d5d1751f550a3f8e0a81793bc2fe https://github.com/f0xit/moeviusbot/commit/233d1805c5450283763fe9b8105644c2d1fb2d7d https://github.com/f0xit/moeviusbot/commit/cbf34ad53178948d0340ad0332571e3dccb80e0b https://github.com/f0xit/moeviusbot/commit/5d7e2a9c46a2f2dc86fba4d8c6fdb788cd16bb52
- The file myfunc.py file is now gone. https://github.com/f0xit/moeviusbot/commit/c83ba30374f1a80fb8561df337cb9ab20c3ef271
  - The gcts function is no longer needed
  - The strfdelta function moved to the dt_tools module
- And of course many small things here and there

### Added
- Commands in the reminder cog are now hybrid commands which means, that they can be invoked also via slash. https://github.com/f0xit/moeviusbot/commit/99ec6d058542d26f5fcbd7db76937194d9d7fd1a
  - This is still a test, so bugs are likely to be encountered.
  - In the future, this can be expanded to other commands, but the reminder cog is by far the most used and useful one.
- There is now a separate dev_requirements.txt file that is only needed for working on the bot. It contains packages like ruff or bandit.

### Fixed
- Typos, mainly names of instance variables, left over from the big refactoring have been fixed

## 0.8 - Big refactoring

This is the first version bump since Oct '20. Many things were changed and added during that time. I'll try to list the results here.

### Under the hood

- The biggest change internally is the refactor I wanted to complete for literally years now.
  - Everything besides administration commands are now located in Cogs which can be (un-)loaded during runtime. This should make updating or fixing things easier in the future.
  - This also results in a hopefully clean class structure with reasonable dependencies, so each function and each cog only knows, what it needs to know. Additionally, I hope the garbage collector will do it's thing and keep memory consumption low.
- Many helper functions are now located in the tools directory.
- Logging is now finally based on the built-in python module. The old solution worked, but I hope that now the logs are actually helpful. At least a little.
- A huge part of the refactor was appropriate naming and working on the code-style. PEP 8 is the way.
- In the meantime, discord.py 2.0 released which brought some breaking changes with it. The resulting bugs should be fixed by now.

But now: The Features!

### Added

- Faith on react: When a user reacts to a message using the :Moevius:-Emote, the author gets 10 faith points. This is hopefully much easier than using the command !faith add
- !zitat build_markov can take an argument for the model size, which defaults to 3. Higher number means more repetition but also more logical sentences. I think 3 is a good compromise.
- Random Overwatch Heroes: Users can use !ow or its derived commands to receive a random Overwatch hero to be played with.
- Additionally, !owpn presents you hero changes from the latest patch notes.
- Quiz! Users can play Wer Wird Mövionär and gain up to 1 million 🕊️! The questions are somewhat strange but users can report weird or wrong questions with the !quiz report command. The ranking of all players can be showed with !quiz rank.
- Gartic Phone highlights will be presented daily at 19:30 in their own channel. This stitches a promt and the corresponding image together for some weirdness. You can also ask for this with the !gartic command.
- If you want to imitate Schnenk's writing style, then try !schnenk. This is basically the inverse of the !wurstfinger command.

### Fixed

- To be fair: It's too much to count. This version was tested carefully but there can be bugs I will fix in minor versions.

### Removed

- The Ult-command is temporarily disabled for some intense refactoring. I decided to bump the version anyways, because most of the under-the-hood changes are completed.

## 0.7 - Quality of Life

### Added

- !ps5 is a fun command to compare a given number to the price of a PS5

### Fixed

- !wurstfinger now applies to the last message in a given channel
- !urbandictionary is now more respeonsive
  - When your search doesn't give a result, the bot presents you alternative search terms
  - If there are not even alternative terms, the bot will tell you

## 0.6

### Faith-Points

- Everybody get's points for using the bot!
- According to the Mövius-Lore, they are called Faith
- Points have no practical use. They're just a measurement of usage
  - Reminders or other useful things grant many points
  - Fun stuff grants less points
  - Administrating the bot grants no points at all
- Super users can grant faith manually for outstanding performances of a user
- Points are saved in a file to be restored when restarting the bot

### Ult Command

- The commands for ult, charge and adding charge are now combined
- ?ult shows the current charge
- !ult activates the ult
- Super users can control the charge with !ult add or !ult set

## 0.5.2

- Added some minor features for fun ... more easter eggs than anything else
- I hope this doesn't crash anything ...

## 0.5.1

- Now the squad-feature works along the game-reminder. Your squad will be informed, when you want to play
- The bot tries to avoid double mentions ... fingers crossed
- Added some exception-handling here and there
- Also logging for squads should now work
- Talking about logging ... I reworked some of the messages

## 0.5 - Squads

- Added a simple function to add users to a squad for each game
- You can of course remove them at any time
- Call you squad with "hey" and they will be notified
- There will be bugs ... fixes ahead

## 0.4.1

- Added charge-command
- Integrated the loop into a discord.ext.task

## 0.4

- Refactored most of the code to work with the bot-subclass of client for easier command-handling
- There will be bugs ... fixes ahead

## 0.3.2

- Added another easter egg
- Fixed some text-bugs
- Deleted some default files for saving, because the bot creates the needed files if they don't exist

## 0.3.1

- Fixed a bug when trying to join a game

## 0.3

- Added !join command to join a stream or a game and be mentioned when the event starts
- Added ?wer request to see, who already joined an event
- Redesigned the event class to members

## 0.2

- Added !game command analog to !stream to announce a time for coop playing
- Expanded the event class for this purpose
- Moved helper functions to myfunc.py

## 0.1.1

- Fixed a bug in loading stream reminder data from .json

## 0.1

### Added

- A changelog and software version numbering, starting right now and updated with every git push
- Started a proper readme file to tell a litte more about this repo and to better track project status

### Changed

- Refactored the setting file feature. It checks for the corresponding .json files, if they don't exist, it stops with the log to copy the .def file and remove that part from the filename.
