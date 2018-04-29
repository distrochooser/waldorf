# waldorf

![die alten](https://media.giphy.com/media/O6cLcNr9HD6yk/giphy.gif)

waldorf is the new backend of distrochooser.de and the successor of the rustlang based one.

## Motivation

Rust introduced some new language features, which are cool, but I do not have the time to learn them. Due some needed updates of some crates, it was necessary to update the base of the backend.

So I decided to move away from rust (sadly, but I need to) and use Python instead in a dockerized environment. This may cause a slightly worse performance but also better python until I master Rust.


## Technical stuff

Environment variable `PASS`: MySQL/ MariaDB password.