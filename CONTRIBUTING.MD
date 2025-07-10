## Contributions Welcome ##
## Setup ##

### Install the following programs ###
  1. git
  2. Python 3.11 or greater. If you go past 3.12 you may discover incompatiblites that we'd probably like to resolve. If that's not your jam stick with 3.11 or 3.12.
  3. Microsoft Visual Studio Code AKA VSCode. This is a free to use IDE that has very useful extenstions such as black, pylance, and a python debugger.
  4. git hub cli. This is optional but recommended.
  5. Factorio. If you end up editing fa_paths.py then you'll want/need to install the various different versions for testing and/or get other people to test those versions for you. Otherwise it shouldn't matter if you are using the Steam, MSI, or zip install.

### Setup Dev Environment ###
1. Fork this repo.
2. Clone it. If you are using the zip version I'd recommend cloning into the Factorio unziped folder so that there is a launcher directory inside Factorio's folder. This allows autodetection of the Facotrio install location while keeping the laucnher and factorio's files from mingling.
3. Open the folder in VSCode. This will probably prompt you if you trust the authors and to install recommened extenstions. Black is a formatter so all our code contributions have the same style and we never have to deal with formating changes obsuring real changes in diffs.
4. From the terminal run `python build.py`. This will automatcally setup and/or use a python virtual environment for you that will install all the module dependencies. It'll also build an executable but don't worry about that for now. VSCode should prompt you if you'd like to use the newly created virtual environment. You should accept.

### Run ###
Congrats you're setup and ready to test. You can run main.py and it should start up the launcher. Now you're ready to make changes and test them out.

### Tests ###
We have a few tests in a test subdirectory. We're just using the default unittest autodiscovery so files starting wtih test_ will be loaded.
