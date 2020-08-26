# Changelog

## 0.5.2
- Added some minor features for fun ... more easter eggs than anything else
- I hope this doesn't crash anything ...

## 0.5.1
- Now the squad-feature works along the game-reminder. Your squad will be informed, when you want to play
- The bot tries to avoid double mentions ... fingers crossed
- Added some exception-handling here and there
- Also logging for squads should now work
- Talking about logging ... I reworked some of the messages

## 0.5
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