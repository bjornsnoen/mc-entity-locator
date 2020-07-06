# Locate bad things in your minecraft world

## Installation
Clone this project to your machine using git

Initialize the project with a virtualenv

`$ python -m venv .venv`

`$ source .venv/bin/activate`

`$ pip install -r requirements.txt`

## Find the thing
When starting up your minecraft server, you may see java exceptions about things with invalid characters in their ids.
This will certainly happen if you attempt to upgrade an older world, where the rules were different and mods were wilder.
That's where the `finder.py` script is your friend. You give it the id of the item from the error message, and the location
of the world files (like $HOME/.minecraft/saves/world/region for the overworld), and it will find every instance of
that entity, along with its location. It will spit out a csv named `item_id.csv` containing region file and chunk file coordinates.

## Find all the things
If your world had lots of things going on in it, finding the things one at a time, restarting the game, finding the next id,
rinsing and repeating can take a long time. Fret not, that's where `lister.py` comes into play! It knows the (current) rules
for what things are allowed to be named in minecraft, and will find any thing that does not abide by those rules, and put
them all in their respective csv files!

## Ok, I have the locations in this weird csv format, what now?
Now you feed that file to my fork of [mcaselector](https://www.github.com/bjornsnoen/mcaselector).
You'll need to clone that project to a separate directory. Or a subdirectory, should work, haven't tested.
You're playing minecraft, so you probably have java installed, but you'll need a jdk to compile it. See [here](https://github.com/bjornsnoen/mcaselector#download-and-installation)

Once you have mcaselector and java you can run the deleter.py script. It will grab any csv file in the out directory,
figure out the block-id we're trying to delete based on the filename, and feed them to mcaselector. It will also
compile mcaselector for you using your system java if that needs to be done.
