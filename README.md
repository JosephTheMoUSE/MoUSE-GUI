# MoUSE Desktop App
This repository contains MoUSE Desktop App. To install it follow the steps 
outlined below. If you are looking for a MoUSE Desktop App usage tutorial,
see [MoUSE wiki page](https://github.com/JosephTheMoUSE/MoUSE-docs/wiki). If 
you only want to install MoUSE Backend see 
[main MoUSE repository](https://github.com/JosephTheMoUSE/MoUSE#mouse).

## Installing MoUSE Desktop App
We assume that you are using Linux operating system and that you have already 
installed Python 3.8 on your computer. If that's not the case, you will find 
instructions how to do it in
[Beginner's Guide to Python](https://wiki.python.org/moin/BeginnersGuide).

1. Download the code from this repository.
   1. If you are familiar with git and GitHub just clone this repository to 
      your computer.
   2. If you are not familiar with git and GitHub, click green `Code` button 
      on the top of this page and then click `Download ZIP` button. When the 
      file is downloaded extract its contents. 
2. Open terminal and navigate to the directory with extracted files. 
3. Create Python virtual environment with following command: 
   `python3 -m venv .venv`.
4. Activate virtual environment: `source .venv/bin/activate`.
5. Generate GUI components with following command: `source regenerate_gui.sh`.
6. Install required packages: `pip install .`.
7. If you want to run MoUSE Desktop App, follow instructions in the next section.
   If you don't wish to continue, just deactivate the virtual environment, by 
   writing in the console: `deactivate`.

## Running MoUSE Desktop App
We assume that you installed MoUSE Desktop App according to above instructions.
1. Make sure that you are in the directory containing MoUSE Desktop App code 
   and that virtual environment is activated.
2. Run following command: `python3 ./src/mouseapp/main.py`. You should see the 
   MoUSE Desktop App window - you can now use MoUSE Desktop App.
3. When you finish using MoUSE Desktop App, deactivate virtual environment with 
`deactivate` command.
   