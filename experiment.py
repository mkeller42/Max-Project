from evogym import WorldObject, EvoWorld, EvoSim, EvoViewer, sample_robot, get_full_connectivity, is_connected

import os, sys, time, random
import numpy as np
from functools import partial

import gym
import evogym.envs
import randomWorldGen

import robot
import environment
import json

import plotly.express as px
import multiprocessing as mp


##IMPORTANT INFO
##when running program, must put one of three vars after program call to run
## 1: "evolve": robots will evolve gene sequences to determine movement
## 2: "oscillate": robots will move on a sin wave and will not evolve movement
## 3: "random": robots will move completely randomly

#finds score of given robot
def scoreChecker(e):
  return e.get_score()

#finds open space for new offspring
def findOpenSpace(worldLocation, worldArray, maxSpaces):
  possibleSpaces = []
  finalSpaces = []
  ix = worldLocation[0]
  iy = worldLocation[1]
  possibleSpaces.extend([[ix+1, iy], [ix-1, iy], [ix, iy+1], [ix, iy-1]])
  for j in possibleSpaces:
    if (0<=j[0]<worldWidth)and(0<=j[1]<worldHeight) and (worldArray[j[0]][j[1]].getNumRobots() < maxSpaces):
      finalSpaces.append(j)
  return finalSpaces

def findOccupiedSpace(worldLocation, worldArray, maxSpaces):
  possibleSpaces = []
  finalSpaces = []
  ix = worldLocation[0]
  iy = worldLocation[1]
  possibleSpaces.extend([[ix+1, iy], [ix-1, iy], [ix, iy+1], [ix, iy-1]])
  for j in possibleSpaces:
    if (0<=j[0]<worldWidth)and(0<=j[1]<worldHeight) and (worldArray[j[0]][j[1]].getNumRobots() >= maxSpaces):
      finalSpaces.append(j)
  return finalSpaces

#calculate fitness (currently average voxel x-position)
def calcFitness(sim):
  score = 0
  size = 0
  for i in sim.object_pos_at_time(sim.get_time(), 'robot')[0]:
    size += 1
    score += i
  return (score)/size

#gets 'map' of world scores 
def worldData(worldArray, worldHeight):
  w = []
  for row in range(len(worldArray)):
    w.append([])
    for i in range(len(worldArray[worldHeight-1])):
      w[row].append(round(worldArray[row][i].get_score(), 2))
  return w

#removes the outcompeted robots from the program, stores in a list
def delDeadRobs(curDead, aliveRobots):
  for i in curDead:
    for j in range(len(aliveRobots)):
      if i.get_id() == aliveRobots[j].get_id():
        fossilizedRobots.append(i)
        del aliveRobots[j]
        break
  
  curDead = []
  return curDead, aliveRobots

#coverts world data into a json file
def write_json(new_data, filename, folder):
  desired_dir = "./saved_data/"+folder
  full_path = os.path.join(desired_dir, filename)
  with open(full_path, 'w') as f:
    json.dump(new_data, f)
  f.close()

def correctCord(cords):
  tempCords = [100,100]
  tempCords[0] = cords[1]
  tempCords[1] = cords[0]  
  return tempCords

#returns best scorer/score given a certain area of the worldmap(to find species)
def getBestScorer(worldArray, columns, worldHeight):
  bestScorer = None
  for i in columns:
    for j in range(worldHeight):
      if not worldArray[j][i].getRobot():
        continue
      elif not bestScorer:
        bestScorer = worldArray[j][i].getRobot()
      elif worldArray[j][i].get_score() > bestScorer.get_score():
        bestScorer = worldArray[j][i].getRobot()
  if bestScorer == None:
    return None
  return [bestScorer.get_structure().tolist(), bestScorer.get_genes().tolist()]

#finds available robot nearby to mix genes with to create offspring
def getParent(robot, worldArray, maxSpaces):
  parentRobot = None
  parentSpaces = findOccupiedSpace(robot.get_location(), worldArray, maxSpaces)

  if not parentSpaces:
    return None

  parentLoc = random.choice(parentSpaces)
  parentRobot = worldArray[parentLoc[0]][parentLoc[1]].getRobot()

  return parentRobot

#sims the robot in the world
def robotSim(robot):
  worlds = worldArray[robot.get_location()[0]][robot.get_location()[1]].getEvos()
  alt = False

  for world in worlds:
    robot.getWorldObj().set_pos(3, 2)
    world.add_object(robot.getWorldObj())

    sim = EvoSim(world)
    sim.reset()

    for i in range(100):
      #if want to change how actions are decided, do it here
      curAction = robot.choiceAction(sim.get_time(), moveMethod)
      sim.set_action('robot', curAction)
      sim.step()
      curScore = calcFitness(sim)
      if curScore > robot.get_score():
        if alt == True:
          robot.set_altscore(curScore)
        else:
          robot.set_score(curScore) 

    world.remove_object('robot')
    alt = True
  return robot

def findRobLocation(x, wA, m):
  locList = findOpenSpace(x.get_location(), wA, m)
      
  if not locList:
    locList = findOccupiedSpace(x.get_location(), wA, m)

  loc = random.choice(locList)
  x.set_location(loc)
  return x


if __name__ == '__main__':


  globalID = 1 #ID variable for keeping track of robots
  moveMethod = sys.argv[1]
  
  
  worldWidth = 16 #seeds for generating each individual world randomly (used together) 
  worldHeight = 16 #maximum size of 99x99!
  worldSeed = 3 #seed for generating each entire collection of worlds randomly
  robotSeed = 3

  maxRobotsPerSpace = 1 #how many robots are allowed to occupy the same space
  mutationRate = 1 #how often offspring mutate

  simRunTime = 1000 #number of rounds the sim will run
  numCores = 8 #number of multiprocessing units will run

  worldArray = []
  curDead = []
  aliveRobots = []
  fossilizedRobots = []

  #lists for what COLUMNS each environment (1 or 2) should appear in
  #(will later expand to be more than columns)
  env_1_list = [0,1,2,3,4,5,6,7]
  env_2_list = [8,9,10,11,12,13,14,15]
  total_env_list = [[env_1_list], [env_2_list]]

  #generate random worlds and add them to array worldArray
  worldFile = {}
  for i in range(worldHeight):
    worldArray.append([])
    for j in range(worldWidth):
      if j in env_1_list:
        evo, dataFile = randomWorldGen.randomizer(os.path.join('world_data', 'flat_env.json'), j+1, i+1, worldSeed)
        altevo, altdataFile = randomWorldGen.randomizer(os.path.join('world_data', 'hill_env.json'), j+1, i+1, worldSeed)
      elif j in env_2_list:
        evo, dataFile = randomWorldGen.randomizer(os.path.join('world_data', 'hill_env.json'), j+1, i+1, worldSeed)
        altevo, altdataFile = randomWorldGen.randomizer(os.path.join('world_data', 'flat_env.json'), j+1, i+1, worldSeed)
      world = environment.World(evo, altevo, j, i)
      worldArray[i].append(world)
      worldFile["World [" + str(j) + "," + str(i) + "]"] = dataFile, altdataFile
  write_json(worldFile, "_worlds.json", '')
  
  #I know I am using a preset seed here, but this actually fully randomizes it.
  #It isn't fully randomized otherwise? idk, but its currently NOT SEEDED
  random.seed(robotSeed) 

  s1Robot = robot.Robot(sample_robot((5,5)), globalID, None)
  s1Robot.set_location([1,1])
  s1Robot.set_true_location([1,1])
  curSim = robotSim(s1Robot)
  worldArray[1][1].setRobot(s1Robot)

  aliveRobots.append(s1Robot)
  
  
  
  for t in range(simRunTime):
    starttime = time.time()
    failureRates = []
    avgNewFitness = []
    avgFitnessDiff = []
    for i in range(worldWidth):
      failureRates.append([0,0])
      avgNewFitness.append(0)
      avgFitnessDiff.append(0)

    #REPRODUCTION
    newRobots = []
    for x in aliveRobots:
      #create offspring
      globalID += 1
      newRobot = robot.Robot((x.get_structure(), x.get_connections()), globalID, x.get_score())
      #determine if mutation occurs
      if random.random() < mutationRate:
        coParent = getParent(x, worldArray, maxRobotsPerSpace)
        newRobot.set_structure(newRobot.mutate(x.get_structure().copy(), x.get_genes().copy(), coParent))
        if coParent == None:
          newRobot.set_parIDs([x.get_id(), None])
        else:
          newRobot.set_parIDs([x.get_id(), coParent.get_id()])
      else:
        newRobot.set_structure(x.get_structure().copy())
      #adds the location as its parent's location, but doesn't put into world yet
      newRobot.set_location(x.get_location())
      newRobots.append(newRobot)


    #SIMULATION

    with mp.Pool(numCores) as p:
      ##1. Find the locations
      newRobots = p.map(partial(findRobLocation, wA=worldArray, m=maxRobotsPerSpace), newRobots)
      ## 2. Evaluate all robots
      newRobots = p.map(robotSim, newRobots)
    
    ## 3. Check for replacements
    for x in newRobots:
      loc = x.get_location()
      avgFitnessDiff[loc[1]] += x.get_score() - x.get_par_score()
      failureRates[loc[1]][1] += 1
      avgNewFitness[loc[1]] += x.get_score()
      localscore = worldArray[loc[0]][loc[1]].get_score()
      if localscore < 0 or localscore < x.get_score(): # replace
        if localscore > -99:
          curDead.append(worldArray[loc[0]][loc[1]].getRobot())
        xloc, yloc = x.get_location()
        x.set_true_location(correctCord([xloc, yloc]))
        worldArray[xloc][yloc].setRobot(x)
        aliveRobots.append(x)
      else:  # do not replace
        curDead.append(x)
        failureRates[loc[0]][0] += 1


    #update robot lists
    for i in range(len(avgNewFitness)):
      if failureRates[i][1] == 0:
        continue
      avgNewFitness[i] = avgNewFitness[i]/failureRates[i][1]
      avgFitnessDiff[i] = avgFitnessDiff[i]/failureRates[i][1]
    curDead, aliveRobots = delDeadRobs(curDead, aliveRobots)
    aliveRobots.sort(key=scoreChecker, reverse = True)


    #create save file of world state
    if t%10 == 0:
      roundfolder = 'round' + str(t)
      if not os.path.exists('./saved_data/'+roundfolder):
        os.mkdir('./saved_data/'+roundfolder)
      infoDict = {
        "round": t,
        "totalRobots": len(aliveRobots),
        "totalDeadRobots": len(fossilizedRobots),
        "bestScoreWorld": worldData(worldArray, worldHeight),
        "topScore": aliveRobots[0].get_score(),
        "topRobot": aliveRobots[0].get_structure().tolist(),
        "topGenes": aliveRobots[0].get_genes().tolist(),
        "topRobotLocation": aliveRobots[0].get_true_location(),
        "env_1_BestScorer": getBestScorer(worldArray, env_1_list, worldHeight),
        "env_2_BestScorer": getBestScorer(worldArray, env_2_list, worldHeight),
        "failureRateWorldData": failureRates,
        "avgNewFitness": avgNewFitness,
        "avgFitnessDiff": avgFitnessDiff
      }
      write_json(infoDict, "world_data_round" + str(t) + ".json", roundfolder)

      robotDict = {}
      for x in aliveRobots:
        robotDict[str(x.get_true_location()[0]) + "," + str(x.get_true_location()[1])] = [x.get_structure().tolist(), 
                                                                                          x.get_genes().tolist(),
                                                                                          x.get_id(),
                                                                                          x.get_parIDs(),
                                                                                          [x.get_score(),
                                                                                          x.get_altscore()]]
      write_json(robotDict, "robot_data_round" + str(t) + ".json", roundfolder)

      #print select data from each round to terminal
      print ("Round: " + str(t))
      print ("Total Runtime (s): {}".format(time.time() - starttime))
      print ("Total Robots: " + str(len(aliveRobots)))
      for i in worldData(worldArray, worldHeight):
        x = i.copy()
        x.insert(env_2_list[0], '|')
        print (x)
      print ("Top Score: " + str(aliveRobots[0].get_score()))
      print ("Top Scorer Location: " + str(aliveRobots[0].get_true_location()))
      print ("Top Scorer: \n" + str(aliveRobots[0].get_structure()))


    #code for creating heatmap
    # fig = px.imshow(bestScores, range_color=[-1,20])
    # fig.show()


  print ("sim over")

  #current robot record: ~14.2
