# MoUSE Desktop App Installation Guide

This guide will help you install and run the MoUSE Desktop App on your computer. Before that, you should have installed MoUSE backend from the repo [MoUSE backend](https://github.com/JosephTheMoUSE/MoUSE). You do not need to open any files from GitHub manually – simply copy and paste the commands given below into your terminal. We assume (for the current moment of the process of developing this project) that you have already installed Python 3.11 (or newer) and the compatible version of Poetry (for dependency management) on your computer. If that's not the case, you will find 
instructions how to do it in [Beginner's Guide to Python](https://wiki.python.org/moin/BeginnersGuide) and [Beginner's Guide to Poetry](https://python-poetry.org/docs/). If you are looking for a MoUSE Desktop App usage tutorial, see the page [MoUSE wiki page](https://github.com/JosephTheMoUSE/MoUSE-docs/wiki).


### Step 1: Download the MoUSE Desktop App

1. If you know how to use GitHub, **clone the repository** using the commands below in the terminal/command prompt:
   ```bash
   cd path_to_the_folder_for_this_project

   git clone https://github.com/JosephTheMoUSE/MoUSE-GUI.git
   ```
2. If you're not familiar with GitHub:
   - Click the green **Code** button at the top of this page.
   - Select **Download ZIP** and save the file to your computer.
   - Once downloaded, **extract** the contents of the ZIP file.
   - Use the terminal to go to the folder where you extracted the files:
   ```bash
   cd path_to_your_extracted_folder
   ```

### Step 2: Install Python and Poetry

Ensure you have Python 3.11 (or newer) and the compatible version of Poetry installed on your computer.

### Step 3: Set Up the Virtual Environment and Dependencies

Now in the main project folder, set up a virtual environment and install the necessary dependencies using Poetry:

1. **Create the virtual environment** and install dependencies:
   ```bash
   poetry update
   poetry install
   ```
   
2. **Generate GUI components**:
   - **Windows users**:
   ```bash
   Set-ExecutionPolicy Unrestricted -Scope CurrentUser
   ./regenerate_gui.ps1
   ```
   - **Mac/Linux users**:  
   ```bash
   ./regenerate_gui.sh
   ```

### Step 4: Running MoUSE Desktop App

1. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

2. **Start the MoUSE Desktop App**:
   ```bash
   python3 ./src/mouseapp/main.py
   ```

You should now see the MoUSE Desktop App window, and you’re ready to use the application!

### Step 5: Deactivating the Virtual Environment

When you’re done using the MoUSE Desktop App, deactivate the virtual environment by typing:
```bash
exit
```

---

### Notes:
- This guide works for **Windows**, **Mac**, and **Linux** users. Simply follow the steps, and you’ll be up and running.
- If you encounter any issues, do not hesitate to contact us on our JosephTheMoUSE Github profile.
