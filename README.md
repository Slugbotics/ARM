# Getting Started

To use this project, new members should create a fork.

## 0) Pre-req installation
0.1) Install Python > 3.12 (*must be greater than 3.12*) \
0.2) If you are running Linux, make a venv. See instructions at the bottom.
0.3) run ```python -m pip install -r requirments.txt``` \
0.4) Install coppelia sim educational: https://www.coppeliarobotics.com/ \
0.5) Run ```python main.py --help``` which will setup a config file and show the parameters for the program.\
0.6) (optional for twitch streaming) Install OBS: https://obsproject.com/ \


## 1) Run
If you are running Linux, make sure to ```source venv/bin/activate```
Run ```python main.py --help``` to see the command line arguments.
If using the simulator, make sure CoppeliaSim is running our scene (double click on simulator/armSIM(3dof).ttt)

If you want to use twitch for video output (great for remote control!) you will need to open OBS and add a source
add "http://127.0.0.1:5000/video_feed" as a source, this is the POV arm camera. Review that everything looks good, then go live in OBS!

# Project structure

## Root
this directory contains the main file, the pip required packages and project wide documentation
|file|purpose|
|-|-|
|```main.py```| Run ```python main.py --help``` for more information.|
|```requirements.txt```| Run ```python -m pip install -r requirments.txt``` to install any dependancies.|
|```config.json```| a git ignored file that stores any device preferences or twitch api keys.|
|```startup.py```| A script that pops up a window to restart the arm. Used on the Pi touchscreen to avoid typing.|

## HALs
This discory is where the various hardware interface files will be, if you are using this program with the simulator or a physical arm, you will need to make sure a HAL (hardware interface layer) exists for your arm and is loaded in the main file.

## Vision
This is where the various vision solutions will live.
If you want to try another computer vision solution, make a new file following this guide: (your_name)_(solution_name).py
ex: aaron_opencv_postnet_object_identifier.py where my name is aaron, the soliton is postnet from opencv and this will identify objects.

## Controllers
This is where the mission planning logic exists.
These scripts will tie everything else together, they will take in the visual data from the selected vision solution, and will plan out how the arm will move, and actually issue movement commands to the arm.
Language interpretation things will go here.

## Modules
This directory is where most utility files will be, how does this program display images or communicate with twitch.

# ARM TEAM GIT STANDARDS:
## Forking
For most projects, make a fork of this project. When creating the fork, follow the naming convention of ```ARM-<module_name>``` Then later we can have you create a pull request on the main project, where we can incorporate those changes on the main project. 
## Branching
Branching is more for the physical arm project or modules that everyone needs.\
Create a new branch if you are working on a new module. For instance, if you were working on the text to speech model, you would create a new branch called 'text-to-speech', and work in that branch. Name your branches meaningfully. No a-test. If you think a single module needs multiple branches, name the branch ```<your_name>-<module_name>```. Only merge back into main once your module is fully tested.
## Commits
Commit OFTEN. You should at the least commit every time you do some work. Ideally everytime the program is working you make a commit.
## Commit Messages
Commit messages should be descriptive. If you added a function called FOO, your commit message should be something like "added function FOO". It should not be "a few changes" or "working on some stuff"
## Pulling
Always pull before you push. If you have a merge confict and don't feel equipped to handle it, ask someone who knows about git. Pull often to avoid merge conflicts.
## Rebasing
Don't.
## basic workflow:
#### You start working on armteam stuff:
git pull
#### You make some changes/write some code:
git pull
git add .
git commit -m "<your commit message here>"
git push
#### You are working on a new project/module:
git branch <your-project-name>
#### You want to switch branches:
git checkout <branch-name>

# Venv info
In Linux you need **v**irtual **env**iroment or venv for short to install pip packages. 
If you are confused about any of the following, *ask for help.* \
In Linux run the following:\
<code>
sudo apt update
sudo apt install python3.12
sudo apt install python3.12-venv
python3.12 -m venv venv
</code>\
Then pip install etc...
If you are running ubuntu, there are more steps including deadsnakes.