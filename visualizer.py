import os, sys
import json
import numpy as np

import imageio
from pygifsicle import optimize

from evogym import EvoSim, EvoViewer, WorldObject, get_full_connectivity
import randomWorldGen

# FIXME: Parametrize this
x, y, gen, wt = sys.argv[1:5]
generation = int(gen)
x = int(x)
y = int(y)

if wt == "B":
    world_file = "hill_env.json"
else:
    world_file = "flat_env.json"




filename = "./saved_data/round{}/robot_data_round{}.json".format(generation, generation)
worldSeed = 3
rcell = "{},{}".format(x,y)
wx, wy = x, y
# wx, wy = 7, 7
nsteps = 600
on_screen = True

def main():
    # Load the robot and the world
    with open(filename, "r") as in_f:
        rdata = json.loads(in_f.read())

    # beware horrible hack ahead, please FIX ME.
    _rshape = rdata[rcell][0]
    _rgenes = rdata[rcell][1]

    shape = np.array(_rshape)
    # print(_rgenes)
    # print(type(_rgenes))
    genes = np.array(_rgenes)

    # printing genes
    # pgenes = [(_x*0.1)%3.141569 for _x in genes]
    # print(pgenes)
    
    robot = WorldObject()
    robot.load_from_array(name = "robot",
                        structure = shape)

    world, _ = randomWorldGen.randomizer(os.path.join('world_data',
                                                      world_file),
                                         wx+1, wy+1, worldSeed)      

    # Run the robot
    robot.set_pos(3, 2)
    world.add_object(robot)
    
    sim = EvoSim(world)
    sim.reset()

    viewer = EvoViewer(sim, resolution = (800,400))
    viewer.track_objects('ground')

    frames = []

    score = -100
    
    # print(genes)
    # print(shape)

    for steps in range(nsteps):
        action = []
        for i in range(5):
            for j in range(5):
                if shape[i][j] in [3,4]:
                    action.append(np.sin(steps/3 + (genes[i][j]*0.1)) + 1)

        # print(action)

        sim.set_action('robot', np.array(action))
        sim.step()

        
        if on_screen:
            viewer.render(mode="screen")
        # else:
        #   frames.append(viewer.render(mode="img"))


        _score = 0
        _size = 0
        for i in sim.object_pos_at_time(sim.get_time(), 'robot')[0]:
            _size += 1
            _score += i
        score = max((_score)/_size, score)

    print(score)
    


    # visualize


if __name__ == "__main__":
    main()
