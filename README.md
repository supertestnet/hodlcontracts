# Hodl contracts
A non-custodial oracle and escrow system for the lightning network. Makes LN contracts more functional.

If you fire it up, be aware:

(1) you need lnd

(2) when you start the app go to localhost:5000/?user=alice

(3) enter a lightning invoice

(4) a bunch of contract junk will be dumped onto the screen, it can be ignored for now

(5) basically Alice has alerted the world that she wants to bet that the function is2even() will return true, where she gets money if it does

(6) next go to localhost:5000/?user=bob

(7) you'll see Alice's contract dumped onto the screen and a field where you can enter a lightning invoice to take the other side of the bet (oh and if you go to Bob's page first before Alice has created a contract, everything will crash)

(8) if you create multiple contracts it will only show the first one because I don't know how to do iteration in python -- consequently if you need to restart the process you'll have to delete the contracts.db file otherwise Bob can only ever take Alice's initial contract

(9) enter a new lightning invoice so that Bob's wallet can receive some money if is2even() returns false

(10) okay now Alice should pay Bob's hodl invoice and Bob should pay Alice's hodl invoice -- you can find them in the contract data that is dumped onto both of their screens. Alice's hodl invoice is first_party_hodl_invoice and Bob's is second_party_hodl_invoice

(11) now visit localhost:5000/check/?pmthash=abc...123 where abc...123 is Alice's invoice's payment hash, you can get it from the contract data that is dumped onto both user's screens (it is in the field first_party_pmthash)

(12) If nothing crashed the server should return a blank screen. Now you are done, is2even() returned true and Alice got Bob's money. Bob's invoice just sits there until it expires

(13) Bob can never win right now because the server doesn't yet know how to do payouts to Bob, only to Alice. I need it to do the same thing it does for Alice but for Bob if is2even() returns false
