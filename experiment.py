from evogym import WorldObject, EvoWorld, EvoSim, EvoViewer, sample_robot, get_full_connectivity, is_connected

import os, sys, time, random
import numpy as np
from functools import partial

import gym
import evogym.envs
import randomWorldGen
# import tutorials

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

#finds open space for new offspring adjacent to worldLocation
def findOpenSpace(worldLocation, worldArray, maxSpaces):
  possibleSpaces = []
  finalSpaces = []
  ix = worldLocation[1]
  iy = worldLocation[0]
  possibleSpaces.extend([[iy, ix+1], [iy, ix-1], [iy+1, ix], [iy-1, ix]])
  for j in possibleSpaces:
    if ((j[1] in env_1_list) or (j[1] in env_2_list))and(0<=j[0]<worldHeight) and (worldArray[j[0]][j[1]].getNumRobots() < maxSpaces):
      finalSpaces.append(j)
  return finalSpaces

#finds occupied spaces adjacent to worldLocation
def findOccupiedSpace(worldLocation, worldArray, maxSpaces):
  possibleSpaces = []
  finalSpaces = []
  ix = worldLocation[1]
  iy = worldLocation[0]
  possibleSpaces.extend([[iy, ix+1], [iy, ix-1], [iy+1, ix], [iy-1, ix]])
  for j in possibleSpaces:
    if ((j[1] in env_1_list) or (j[1] in env_2_list))and(0<=j[0]<worldHeight) and (worldArray[j[0]][j[1]].getNumRobots() >= maxSpaces):
      finalSpaces.append(j)
  finalSpaces.append([iy,ix])
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

#removes the outcompeted robots from the program, stores in list curDead
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

#converts cords (y, x format) to tempCords (x, y format)
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
  return [bestScorer.get_structure().tolist(), [bestScorer.get_genes()[0].tolist(), 
                                                bestScorer.get_genes()[1].tolist(),
                                                bestScorer.get_genes()[2].tolist(),
                                                bestScorer.get_genes()[3].tolist()]]

#finds available robot nearby to mix genes with to create offspring
def getParent(robot, worldArray, maxSpaces):
  parentRobot = None
  parentSpaces = findOccupiedSpace(robot.get_location(), worldArray, maxSpaces)

  if not parentSpaces:
    return None

  parentLoc = random.choice(parentSpaces)
  parentRobot = worldArray[parentLoc[0]][parentLoc[1]].getRobot()

  return parentRobot

def findRobLocation(x, wA, m):
  locList = findOpenSpace(x.get_location(), wA, m)
      
  if not locList:
    locList = findOccupiedSpace(x.get_location(), wA, m)

  loc = random.choice(locList)
  x.set_location(loc)
  return x

#sims the robot in the world
def robotSim(robot):
  worlds = worldArray[robot.get_location()[0]][robot.get_location()[1]].getEvos()
  alt = False

  for world in worlds:
    robot.getWorldObj().set_pos(3, 2)
    world.add_object(robot.getWorldObj())

    sim = EvoSim(world)
    sim.reset()

    for i in range(numSteps):
      robot.setBottomSensor(calcBottomSensor(sim, robot))

      #if want to change how actions are decided, do it here
      curAction = robot.choiceAction(sim.get_time(), moveMethod)
      sim.set_action('robot', curAction)
      sim.step()

      

    #calculate scores
    curScore = calcFitness(sim)
    if curScore > robot.get_score() and alt==False:
      robot.set_score(curScore) 
    elif curScore > robot.get_altscore() and alt==True:
      robot.set_altscore(curScore)

    world.remove_object('robot')
    alt = True
  return robot

#calculates the distance from the center of mass of the robot to the nearest ground point 
def calcBottomSensor(sim, robot):
  distance = 100
  robotCenterCords = robot.getCenterMass(sim)
  groundCords = sim.object_pos_at_time(sim.get_time(), 'ground')
  for i in range(len(groundCords[0])):
    if (round(robotCenterCords[0]) == round(groundCords[0][i])):
      distance = robotCenterCords[1] - groundCords[1][i]
      break # i don't think it's possible to get a lower coord before a higher one using the built-in system, so you don't have to check 
  return distance


if __name__ == '__main__':

  # ??
  # print(fg())

  globalID = 1 #ID variable for keeping track of robots
  moveMethod = sys.argv[1]


  worldWidth = 16 #seeds for generating each individual world randomly (used together) 
  worldHeight = 16 #maximum size of 99x99!
  worldSeed = 3 #seed for generating each entire collection of worlds randomly
  robotSeed = 3

  maxRobotsPerSpace = 1 #how many robots are allowed to occupy the same space
  mutationRate = 1 #how often offspring mutate

  simRunTime = 5000 #number of rounds the sim will run
  numCores = 12 #number of multiprocessing units will run
  numSteps = 150 #amount of 'time' for each sim
  extraRounds = 0 #used for added extra rounds when resuming sim

  worldArray = []
  curDead = []
  aliveRobots = []
  fossilizedRobots = []

  #lists for what COLUMNS each environment (1 or 2) should appear in
  #(will later expand to be more than columns)
  env_1_list = [0,1,2,3,4,5,6,7]
  no_env_list = [8]
  env_2_list = [9,10,11,12,13,14,15,16]
  total_env_list = [[env_1_list], [env_2_list]]

  #RESUMING A SIM INSTRUCTIONS
  #Take "_worlds.json" and whatever robot_data json file you need and put into resume_data folder
  #Rename robot_data file to "robot_data.json"
  #Run program with extra argument "resume"
  #Voila
  if len(sys.argv) == 3:
    #create previous worlds using _worlds.json
    print("Resuming Sim from Round "+ sys.argv[2])
    extraRounds = int(sys.argv[2])
    for i in range(worldHeight):
      worldArray.append([])
      for j in env_1_list + env_2_list:
        with open('./resume_data/_worlds.json', 'r') as f:
          worldInfo = json.load(f)
          # print(worldInfo["World [0,0]"])
        normWorld = worldInfo["World [" + str(j) + "," + str(i) + "]"][0]
        altWorld = worldInfo["World [" + str(j) + "," + str(i) + "]"][0]

        with open('temp_world.json', 'w') as outfile:
          json.dump(normWorld, outfile)
        norm = EvoWorld.from_json(os.path.join('temp_world.json'))
        with open('temp_world.json', 'w') as outfile:
          json.dump(altWorld, outfile)
        alt = EvoWorld.from_json(os.path.join('temp_world.json'))

        world = environment.World(norm, alt, j, i)
        worldArray[i][j] = world

        #add robots to each world using robot_data.json
        with open("./resume_data/robot_data.json", 'r') as f:
          robotInfo = json.load(f)
        #add robot to world if there's one already there
        if str(j) + "," + str(i) in robotInfo:
          rob = robotInfo[str(j) + "," + str(i)]
          newRob = robot.Robot((np.array(rob[0]), get_full_connectivity(np.array(rob[0]))), np.array(rob[1]), rob[2], None)
          newRob.set_location([i,j])
          newRob.set_true_location([j,i])
          newRob.parentsIDS = rob[3]
          world.setRobot(newRob)
          aliveRobots.append(newRob)

  #STARTING SIM FROM SCRATCH
  else:
    #generate random worlds and add them to array worldArray
    worldFile = {}
    for i in range(worldHeight):
      worldArray.append([])
      for j in range(worldWidth+1):
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
    
    #seeding world
    random.seed(robotSeed) 
    #create robot
    s1Robot = robot.Robot(sample_robot((5,5)), [[],[],[],[]], globalID, None)
    s1Robot.generateRandomGenes()
    s1Robot.set_location([4,16])
    s1Robot.set_true_location([16,4])
    s1Robot.parentsIDs = (-1, -1)
    curSim = robotSim(s1Robot)
    worldArray[1][1].setRobot(s1Robot)

    globalID += 1

    s2Robot = robot.Robot(sample_robot((5,5)), [[],[],[],[]], globalID, None)
    s2Robot.generateRandomGenes()
    s2Robot.set_location([4,0])
    s2Robot.set_true_location([0,4])
    s2Robot.parentsIDs = (-1, -1)
    curSim = robotSim(s2Robot)
    worldArray[1][1].setRobot(s2Robot)

    aliveRobots.append(s1Robot)
    aliveRobots.append(s2Robot)
  
  
  #START SIM
  for t in range(simRunTime):
    starttime = time.time()
    failureRates = []
    avgNewFitness = []
    avgFitnessDiff = []
    for i in env_1_list + env_2_list + no_env_list:
      failureRates.append([0,0])
      avgNewFitness.append(0)
      avgFitnessDiff.append(0)

    #REPRODUCTION
    newRobots = []
    for x in aliveRobots:
      #create offspring
      globalID += 1
      newRobot = robot.Robot((x.get_structure(), x.get_connections()), x.get_genes(), globalID, x.get_score())
      #determine if mutation occurs
      if random.random() < mutationRate:
        coParent = getParent(x, worldArray, maxRobotsPerSpace)
        newRobot.mutate(coParent)
        if coParent == None:
          newRobot.set_parIDs([x.get_id(), None])
        else:
          newRobot.set_parIDs([x.get_id(), coParent.get_id()])
      else:
        newRobot.set_structure(x.get_structure().copy())
      #adds the location as its parent's location, but doesn't put into world yet
      newRobot.set_location(x.get_location())
      newRobot.set_true_location([x.get_location()[1], x.get_location()[0]])
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
      roundfolder = 'round' + str(t + extraRounds)
      if not os.path.exists('./saved_data/'+roundfolder):
        os.mkdir('./saved_data/'+roundfolder)
      infoDict = {
        "round": (t + extraRounds),
        "totalRobots": len(aliveRobots),
        "totalDeadRobots": len(fossilizedRobots),
        "bestScoreWorld": worldData(worldArray, worldHeight),
        "topScore": aliveRobots[0].get_score(),
        "topRobot": aliveRobots[0].get_structure().tolist(),
        "topGenes": [aliveRobots[0].get_genes()[0].tolist(), 
                     aliveRobots[0].get_genes()[1].tolist(),
                     aliveRobots[0].get_genes()[2].tolist(),
                     aliveRobots[0].get_genes()[3].tolist()],
        "topRobotLocation": aliveRobots[0].get_true_location(),
        "env_1_BestScorer": getBestScorer(worldArray, env_1_list, worldHeight),
        "env_2_BestScorer": getBestScorer(worldArray, env_2_list, worldHeight),
        "failureRateWorldData": failureRates,
        "avgNewFitness": avgNewFitness,
        "avgFitnessDiff": avgFitnessDiff
      }
      write_json(infoDict, "world_data_round" + str(t + extraRounds) + ".json", roundfolder)

      robotDict = {}
      for x in aliveRobots:
        robotDict[str(x.get_true_location()[0]) + "," + str(x.get_true_location()[1])] = [x.get_structure().tolist(), 
                                                                                          [x.get_genes()[0].tolist(), 
                                                                                            x.get_genes()[1].tolist(),
                                                                                            x.get_genes()[2].tolist(),
                                                                                            x.get_genes()[3].tolist()],
                                                                                          x.get_id(),
                                                                                          x.get_parIDs(),
                                                                                          [x.get_score(),
                                                                                          x.get_altscore()]]
      write_json(robotDict, "robot_data_round" + str(t + extraRounds) + ".json", roundfolder)

      #print select data from each round to terminal
      print ("Round: " + str(t + extraRounds))
      print ("Total Runtime (s): {}".format(time.time() - starttime))
      print ("Total Robots: " + str(len(aliveRobots)))
      for i in worldData(worldArray, worldHeight):
        x = i.copy()
        # x.insert(env_2_list[0])
        print (x)
      print ("Top Score: " + str(aliveRobots[0].get_score()))
      print ("Top Scorer Location: " + str(aliveRobots[0].get_true_location()))
      print ("Top Scorer: \n" + str(aliveRobots[0].get_structure()))


    #code for creating heatmap
    # fig = px.imshow(bestScores, range_color=[-1,20])
    # fig.show()


  print ("sim over")

  #current robot record: ~14.2
