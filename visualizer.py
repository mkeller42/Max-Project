import os, sys
import json
import numpy as np

import imageio
from pygifsicle import optimize

from evogym import EvoSim, EvoViewer, WorldObject, get_full_connectivity
import randomWorldGen

# FIXME: Parametrize this
filename = "tmp/dataRound50.json"
world_file = "hill_env.json" #"flat_env.json"
worldSeed = 42
x, y = 1, 2
nsteps = 400
on_screen = True

def main():
    # Load the robot and the world
    with open(filename, "r") as in_f:
        rdata = json.loads(in_f.read())

    # beware horrible hack ahead, please FIX ME.
    _rshape = rdata["env_2_BestScorer"].replace("\n","").replace(" ",",").replace(".","")
    _rgenes = rdata["topGenes"].replace("\n","").replace(" ",",").replace(",,",",")

    shape = np.array(json.loads(_rshape))
    genes = np.array(json.loads(_rgenes))
    
    robot = WorldObject()
    robot.load_from_array(name = "robot",
                        structure = shape)

    world, _ = randomWorldGen.randomizer(os.path.join('world_data',
                                                      world_file),
                                         x, y, worldSeed)      

    # Run the robot
    robot.set_pos(3, 2)
    world.add_object(robot)
    
    sim = EvoSim(world)
    sim.reset()

    viewer = EvoViewer(sim, resolution = (400,200))
    viewer.track_objects('ground')

    frames = []
    
    for steps in range(nsteps):
        action = []
        for i in range(5):
            for j in range(5):
                if shape[i][j] in [3,4]:
                    action.append(np.sin(steps/3 + (genes[i][j]*0.1)) + 1)

        sim.set_action('robot', np.array(action))
        sim.step()

        if on_screen:
            viewer.render(mode="screen")
        else:
            frames.append(viewer.render(mode="img"))

    


    # visualize


if __name__ == "__main__":
    main()
