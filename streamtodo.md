# ToDo-List für den Stream
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
- [ ] Add: Random Overwatch Charakter
    - !ow => Random Hero
    - !ow voice => jeder im Voice Random Hero
    - !ow role => Random Hero der Rolle
- [ ] Add: Ultimate getUser-Function (displayname=>name=>id) to fetch a user
- [ ] Add: Hier spricht Gott, gib Gandalf deinen Ring (Macht, dass Mövius was sagt)
- [x] Overview
- [x] Add: PS5-Kommando
- [x] Fix: !wurstfinger, fetch last msg
- [x] Fix: Vorschläge, wenn Urban Dict kein Ergebnis liefert
- [x] Fix: Api-Update abchecken
- [x] Add: Krah-Krah-Reaction bringt Faith als Belohnung

# Takeway Messages
- Klammern sind richtig und wichtig