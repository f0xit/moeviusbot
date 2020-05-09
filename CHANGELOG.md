# Changelog

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