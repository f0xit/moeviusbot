# ToDo-List

## High Priority

- [ ] Moving every Cog to it's own file. Currently missing:
  - [ ] Reminder
  - [x] Fun
- [ ] Rethinking the event mechanics from the ground up
  - [ ] Saving the date as proper timestamp to allow events more than 24 hours ahead
  - [ ] Storing events in two seperate files: Upcoming and past
- [ ] Moving the checks to a seperate file that knows the Bot's settings

## Medium Priority

- [ ] Add: Poll-Command
  - !poll new \[public/private/secret\] "Abstimmung" "123" "456" "789"
    - => Neue Umfrage mit A: 123, B: 456 oder C: 789
    - Poll hat ID für Tracking, wird ausgegeben
  - !vote A => Abstimmung für A bei der letzten Poll
    - bei private/secret Poll, Abstimmung nur über DM an Bot
  - !poll show => Zwischenergebnis, wer hat abgestimmt
    - Bei public auch wer wie abgestimmt hat
    - Bei secret nur die Zahlen
  - !poll close => Endergebnis, wer hat abgestimmt
    - Bei private auch wer wie abgestimmt hat
    - Bei secret nicht
- [ ] Rebuilding the Ult analogous to the new faith system
- [ ] Adding default values to the settings file if something is missing

## Low Priority

- [ ] Add properties in responses to indicate a single random message or sending them all
- [ ] Add commands for super-users to add new requests and responses
- [ ] Add: Mövius-Say command
