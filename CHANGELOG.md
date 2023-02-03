# Changelog

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
