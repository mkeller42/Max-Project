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

offset = 8

def robotDataRead(fileNum):
  dataList = []
  for i in range(0, int(fileNum)+10, 10):
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
    filewriter.writerow(['AB-flat', 'AB-hill', 'AA-flat', 'AA-hill', 'BB-hill', 'BB-flat', 'round'])
    for d in dataList:
      print("check")
      tempScores = findNewScores(d)
      filewriter.writerow([tempScores[0], tempScores[1], tempScores[2], tempScores[3], tempScores[4], tempScores[5], round])
      round += 10

  return

#findNewScores takes a gen number (fileNum) and returns the avg [A,B] scores for crossbred Robots
def findNewScores(file):

  rdata = file
  worldSeed = 3
  numCores = 8
  numSteps = 300
  # wx, wy = 7, 7
  nsteps = 300
  envos = ["flat_env.json", "hill_env.json"]

  count = 0
  countA = 0
  countB = 0
  sumAScores = 0
  sumBScores = 0
  sumAScoresA = 0
  sumAScoresB = 0
  sumBScoresA = 0
  sumBScoresB = 0
  # Load the robot and the world
  newRobots = []
  newRobotsA = []
  newRobotsB = []

  for y in range(16):
    for x in range(8):

      par1cords = "{},{}".format(x, y)
      par2cords = "{},{}".format(x+offset, y)
      if rdata.get(par1cords) == None or rdata.get(par2cords) == None:
        continue
      count += 1
      _rshape = rdata[par1cords][0]
      _rgenes = rdata[par1cords][1]

      _r2shape = rdata[par2cords][0]
      shape2 = np.array(_r2shape)

      shape = np.array(_rshape)
      genes = np.array(_rgenes)

      #create new offspring from A and B parent
      shape = mutate(shape, genes, shape2)
      newRobot = robot.Robot(sample_robot((5,5)), [[],[],[],[]], 1, -100)  ##ERROR: I have not implemented the new robot code because I added genes, FIXME
      newRobot.set_genes(genes[0], genes[1], genes[2], genes[3])
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
  
  for y in range(16):
    for x in range(4):
      par1cordsA = "{},{}".format(x, y)
      par2cordsA = "{},{}".format(x+4, y)
      par1cordsB = "{},{}".format(x+offset, y)
      par2cordsB = "{},{}".format(x+offset+4, y)
      if rdata.get(par1cordsA) == None or rdata.get(par2cordsA) == None or rdata.get(par1cordsB) == None or rdata.get(par2cordsB) == None:
        continue
      countA += 1
      countB += 1
      _rshapeA = rdata[par1cordsA][0]
      _rgenesA = rdata[par1cordsA][1]
      _rshapeB = rdata[par1cordsB][0]
      _rgenesB = rdata[par1cordsB][1]

      _r2shapeA = rdata[par2cordsA][0]
      _r2shapeB = rdata[par2cordsB][0]
      shape2A = np.array(_r2shapeA)
      shape2B = np.array(_r2shapeB)

      shapeA = np.array(_rshapeA)
      genesA = np.array(_rgenesA)
      shapeB = np.array(_rshapeB)
      genesB = np.array(_rgenesB)

      #create new offspring from A and B parent
      shapeA = mutate(shapeA, genesA, shape2A)
      newRobotA = robot.Robot(sample_robot((5,5)), [[],[],[],[]], 1, -100)  ##ERROR: I have not implemented the new robot code because I added genes, FIXME
      newRobotA.set_genes(genesA[0], genesA[1], genesA[2], genesA[3])
      newRobotA.set_structure(shapeA)

      shapeB = mutate(shapeB, genesB, shape2B)
      newRobotB = robot.Robot(sample_robot((5,5)), [[],[],[],[]], 1, -100)  ##ERROR: I have not implemented the new robot code because I added genes, FIXME
      newRobotB.set_genes(genesB[0], genesB[1], genesB[2], genesB[3])
      newRobotB.set_structure(shapeB)

      #set rob worlds to parents' worlds
      # worlds = []
        
      worldA, _ = randomWorldGen.randomizer(os.path.join('world_data',
                                                          envos[0]),
                                              x, y, worldSeed)  
      worldB, _ = randomWorldGen.randomizer(os.path.join('world_data',
                                                          envos[1]),
                                              x, y, worldSeed) 
      newRobotA.set_worlds([worldA, worldB])
      newRobotsA.append(newRobotA)
      newRobotB.set_worlds([worldB, worldA])
      newRobotsB.append(newRobotB)

  # use multiprocessing to simulate robots for round
  with mp.Pool(numCores) as p:
    ## 2. Evaluate all robots
    newRobots = p.map(robotSim, newRobots)
    newRobotsA = p.map(robotSim, newRobotsA)
    newRobotsB = p.map(robotSim, newRobotsB)

  # collect rob scores for round
  for rob in newRobots:
    sumAScores += rob.get_score()
    sumBScores += rob.get_altscore()
  for rob in newRobotsA:
    sumAScoresA += rob.get_score()
    sumAScoresB += rob.get_altscore()
  for rob in newRobotsB:
    sumBScoresB += rob.get_score()
    sumBScoresA += rob.get_altscore()

  if (count) and (countA) and (countB):
    avgAScore = round(sumAScores / count, 2)
    avgBScore = round(sumBScores / count, 2)
    avgAScoreA = round(sumAScoresA / countA, 2)
    avgBScoreB = round(sumBScoresB / countB, 2)
    avgAScoreB = round(sumAScoresB / countA, 2)
    avgBScoreA = round(sumBScoresA / countB, 2)
    return [avgAScore, avgBScore, avgAScoreA, avgAScoreB, avgBScoreB, avgBScoreA]
  return[0,0,0,0,0,0]
        
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
      robot.setBottomSensor(experiment.calcBottomSensor(sim, robot))
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

