import os, sys
import json
import numpy as np
import csv

import imageio
from pygifsicle import optimize

from evogym import EvoSim, EvoViewer, WorldObject, get_full_connectivity, is_connected, sample_robot
import randomWorldGen
import random
import multiprocessing as mp

import experiment
import robot

def robotDataRead(fileNum):
  dataList = []
  for i in range(0, int(fileNum)+10, 20):
    with open('./example_data/round' + str(i) + '/robot_data_round' + str(i) + '.json', 'r') as f:
      # print(i)
      dataList.append(json.load(f))
  return dataList

#main function, takes dataList from robotDataRead and goes through every file, crossbreeds A/B robots and finds scores of children
def crossBreed(dataList):
  round = 0
  
  with open('crossbredRobotData.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['flatEnv', 'hillEnv', 'round'])
    for d in dataList:
      print("check")
      tempScores = findNewScores(d)
      filewriter.writerow([tempScores[0], tempScores[1], round])
      round += 50

  return

#findNewScores takes a gen number (fileNum) and returns the avg [A,B] scores for crossbred Robots
def findNewScores(file):

  rdata = file
  worldSeed = 3
  numCores = 12
  numSteps = 300
  # wx, wy = 7, 7
  nsteps = 300
  envos = ["flat_env.json", "hill_env.json"]

  count = 0
  sumAScores = 0
  sumBScores = 0
  # Load the robot and the world
  newRobots = []

  for y in range(16):
    for x in range(8):
      count += 1
      localScores = []

      par1cords = "{},{}".format(x, y)
      par2cords = "{},{}".format(x+8, y)
      # beware horrible hack ahead, please FIX ME.
      if rdata.get(par1cords) == None or rdata.get(par2cords) == None:
        continue
      _rshape = rdata[par1cords][0]
      _rgenes = rdata[par1cords][1]

      _r2shape = rdata[par2cords][0]
      shape2 = np.array(_r2shape)

      shape = np.array(_rshape)
      genes = np.array(_rgenes)

      #create new offspring from A and B parent
      shape = mutate(shape, genes, shape2)
      newRobot = robot.Robot(sample_robot((5,5)), 1, -100)
      newRobot.set_structure(shape)

      #set rob worlds to parents' worlds
      worlds = []
      for env in envos:
        
        world, _ = randomWorldGen.randomizer(os.path.join('world_data',
                                                          env),
                                              x, y, worldSeed)  
        worlds.append(world)
        newRobot.set_worlds(worlds)
      newRobots.append(newRobot)

  # use multiprocessing to simulate robots for round
  with mp.Pool(numCores) as p:
    ## 2. Evaluate all robots
    newRobots = p.map(robotSim, newRobots)

  # collect rob scores for round
  for rob in newRobots:
    sumAScores += rob.get_score()
    sumBScores += rob.get_altscore()
  avgAScore = sumAScores / count
  avgBScore = sumBScores / count
  return [avgAScore, avgBScore]
        
#robotSim: almost-copy of robotSim in experiment.py file
#change: uses robot.get_worlds to get the parent worlds
def robotSim(robot):
  alt = False

  for world in robot.get_worlds():
    robot.getWorldObj().set_pos(3, 2)
    world.add_object(robot.getWorldObj())

    sim = EvoSim(world)
    sim.reset()

    for i in range(300):
      #if want to change how actions are decided, do it here
      curAction = robot.choiceAction(sim.get_time(), "evolve")
      sim.set_action('robot', curAction)
      sim.step()
      curScore = experiment.calcFitness(sim)
      if curScore > robot.get_score() and alt==False:
        robot.set_score(curScore) 
      elif curScore > robot.get_altscore() and alt==True:
        robot.set_altscore(curScore)

    world.remove_object('robot')
    alt = True
  return robot

#mutate: identical to robot.py mutate
def mutate(old_shape, old_genes, parent_shape):
    
  count = 0
    
  while count <= 5000:

    new_shape = old_shape
    new_genes = old_genes

    if parent_shape.all() != None:
      if random.random() > 0.5:
        for i in range(2, 5):
          new_shape[i] = parent_shape[i]
      else:
        for i in range(3, 5):
          new_shape[i] = parent_shape[i]

    #TRUE MUTATION
    pos = tuple(np.random.randint(0,4,2))
    if random.random() > 0.5:
      new_shape[pos] = np.random.randint(0,4)
    else:
      new_genes[pos] = random.random() * 6.28

    if (is_connected(new_shape) and (3 in new_shape or 4 in new_shape)):
      robot = new_shape
      break

    count += 1
  if count > 5000:
    raise Exception("Can't find a valid mutation after 5000 tries!")
  
  
  return robot

if __name__ == "__main__":
  fileNum = sys.argv[1]
  robotDataList = robotDataRead(fileNum)
  crossBreed(robotDataList)

