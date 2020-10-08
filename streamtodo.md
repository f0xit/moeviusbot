# ToDo-List für den Stream
- [ ] Add: Poll-Command
    - !poll new "Abstimmung" "123" "456" "789" type=public(private/secret) channel=name/id
        - => Neue Umfrage mit A: 123, B: 456 oder C: 789
        - Poll hat ID für Tracking, wird ausgegeben
        - Bei private=True braucht Mövius nach einem Channel-Namen/Channel_ID
    - !poll A => Abstimmung für A bei der letzten Poll
        - !poll A id => Abstimmung für A bei Poll mit der id, falls offen
        - bei private Poll, Abstimmung nur über DM an Bot
    - !poll show => Zwischenergebnis, wer hat abgestimmt
        - Bei private auch wer wie abgestimmt hat
        - Bei secret nicht
    - !poll close => Endergebnis, wer hat abgestimmt
        - Bei private auch wer wie abgestimmt hat
        - Bei secret nicht
- [ ] Add: Random Overwatch Charakter
    - !ow - wenn User nicht im Voice ist => Random Hero
    - !ow - wenn User im Voice ist: Jeder im Voice => Random Hero
    - !ow role - Random Hero der Rolle
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