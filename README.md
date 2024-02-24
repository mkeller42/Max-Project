Authors: Max Keller
Dependencies: EvoGym, multiprocessing, *several other smaller extensions - see specific files for details*

# Max-Project
Max's work on the Evogym project. The project consists of a soft-bodied robot simulation that is designed for the purposes of studying speciation across a species in a closed environment. 
Outline of program: experiment.py takes in a specified world configuration and default world files and constructs a world map consisting of several different environments and robots (determined by the experiment type defined in the terminal command). The program then runs the simulation for a specified time period using parallel processing. All outputted data is stored in the saved_data folder.

# File Descriptions:
- experiment.py - the main code for the experiment/simulation. Contains the code for the creation and runnning of the simulation, and is the main file of the program. See more details in the file.
  - environment.py - class file for the simulation environments. Main purpose is to store information about each world object to be navigated by the robots.
    -randomWorldGen.py - file for creating randomized worlds for the simulation.
  - robot.py - class file for the simulation. Main purpose is to contain functions and information used to construct/manipulate robot objects over the course of the simulation.
- dataReader.py - main data analysis file. Contains several different functions which function to read datafiles from the "example_data" folder and return several varying analytical outputs.
- newGenTester.py - alternate data analysis/simulation file. Created for the purposes of manually creating and simulating creatures based off of creatures created during a 'nomral' simulation. Used for several data analysis purposes.

