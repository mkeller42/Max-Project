from evogym import WorldObject, EvoSim, is_connected, get_full_connectivity
import numpy as np
import random

class Robot():
    
  def __init__(self, sample, genes, globalID, parScore) -> None:
    self.bitmask = []
    self.sensorGenes = []
    self.timeGenes = []
    self.ampGenes = []
    self.structure, self.connections = sample
    self.location = []
    self.trueLocation = []
    self.score = -99
    self.ID = globalID
    self.worldObject = self.createWorldObj()
    if (len(genes[0]) != 0):
      self.set_genes(genes[0], genes[1], genes[2], genes[3])
    self.parentFitness = parScore
    self.parentsIDs = None
    self.altscore = -99
    self.bottomSensor = -99


  def set_worlds(self, worlds):
    self.worlds = worlds

  def get_worlds(self, ):
    return self.worlds

  # returns robot voxel structure
  def get_structure(self, ):
    return self.structure
  
  # sets parent IDs
  def set_parIDs(self, ids):
    self.parentsIDs = ids

  # returns parent IDs
  def get_parIDs(self, ):
    return self.parentsIDs
  
  # returns parent score
  def get_par_score(self, ):
    return self.parentFitness
  
  # creates robot voxel structure
  def set_structure(self, structure):
    self.structure = structure
    self.set_connections(get_full_connectivity(structure))
    self.worldObject = self.createWorldObj()
  
  # returns robot voxel connections
  def get_connections(self, ):
    return self.connections

  # sets robot voxel connections
  def set_connections(self, connections):
    self.connections = connections

  # returns robot ID
  def get_id(self,):
    return self.ID

  # returns robot world location (y, x)
  def get_location(self, ):
    return self.location
  
  # sets robot world location (y, x)
  def set_location(self, l):
    self.location = l

  # returns robot world location (x, y)
  def get_true_location(self,):
    return self.trueLocation

  # sets robot world location (x, y)
  def set_true_location(self, l):
    self.trueLocation = l

  # returns robot score
  def get_score(self, ):
    return self.score

  # sets robot score
  def set_score(self, s):
    self.score = s

  # returns robot score in alt environment
  def get_altscore(self, ):
    return self.altscore

  # sets robot score in alt environment
  def set_altscore(self, s):
    self.altscore = s
  
  def get_genes(self,):
    return self.bitmask, self.ampGenes, self.timeGenes, self.sensorGenes
  
  def get_ampGenes(self, ):
    return self.ampGenes
  
  def get_timeGenes(self, ):
    return self.timeGenes
  
  def get_sensorGenes(self, ):
    return self.sensorGenes
  
  def get_bitmask(self, ):
    return self.bitmask
  
  def set_genes(self, bG, aG, tG, sG):
    self.bitmask = bG
    self.ampGenes = aG
    self.timeGenes = tG
    self.sensorGenes = sG

  def getWorldObj(self, ):
    return self.worldObject

  #createWorldObj function
  # creates/returns robot EvoGym WorldObject() for use in sim
  def createWorldObj(self, ):
    robObject = WorldObject()
    robObject.load_from_array(
      name = 'robot',
      structure = self.structure,
      connections = self.connections)
    return robObject
  
  #getCenterMass function
  # takes robot(self) and EvoGym sim (sim)
  # returns the coordinates for the calculated center of mass of the robot 
  # determined by average voxel positions
  def getCenterMass(self, sim):
    masses = sim.object_pos_at_time(sim.get_time(), 'robot')
    xavg = sum(masses[0])
    yavg = sum(masses[1])
    return [xavg/len(masses[0]), yavg/len(masses[1])]
  
  #setBottomSensor function
  # sets self.bottomSensor to the distance from the center Robot mass to the ground beneath it
  # bottomSensor = (distance-5)/5 to scale to robot height
  def setBottomSensor(self, distance):
    if (distance > 5):
      distance -= 5
    else:
      distance = 0
    distance /= 5
    self.bottomSensor = distance

  #returns bottomSensor value
  def getBottomSensor(self, ):
    return self.bottomSensor

  #count_actuators functin
  # returns int of number of actuators in robot
  def count_actuators(self):
    count = 0
    for _x in self.get_structure().flatten():
      if _x == 3 or _x == 4:
        count += 1
    return count

  #choiceAction function
  # determines which action function (evolvedAction, action, randomAction) to use for sim
  def choiceAction(self, steps, action):
    if action == "evolve":
      return self.evolvedAction(steps)
    elif action == "random":
      return self.randomAction()
    elif action == "oscillate":
      return self.standardAction(steps)
    return ValueError

  #evolvedAction function
  # takes int steps argument (functions as sime time)
  # returns array of gene-determined actions to be used as actuator values in action determination
  # (12/12/23) equation used uses bitmask, amp, time, sensor and sin wave 
  def evolvedAction(self, steps):
    sensor = self.getBottomSensor()
    action = []
    for i in range(len(self.structure)):
      for j in range(len(self.structure)):
        if self.structure[i][j] in [3,4]:
          ampValue = sensor * self.ampGenes[i][j] * self.bitmask[i][j]
          timeValue = sensor * self.timeGenes[i][j] * self.bitmask[i][j]
          sensorValue = sensor * self.sensorGenes[i][j] * self.bitmask[i][j]
          action.append(np.sin(sensorValue + (steps * timeValue)) * ampValue)  #I CHANGED IT SO THAT IT WASN'T * 0.1
    return np.array(action)
  
  #action function
  # takes int steps argument (functions as sim time)
  # returns array of sin-determined actions to be used as actuator values in action determination
  # REMOVES ABILITY FOR ROBOTS TO EVOLVE THEIR ACTIONS THROUGH GENES
  # (12/12/23) only used if program run with "oscillate" tag 
  def standardAction(self, steps):
    action = []
    for _ in range(self.count_actuators()):
      action.append(np.sin(steps/3 + (_*0.1))+1)
    return np.array(action)
  
  #randomAction function
  # returns array of random numbers to be used as actuator values in action determination
  # (12/12/23) only used if program is run with "random" tag (never been used)
  def randomAction(self):
    action = []
    for _ in range(self.count_actuators()):
      action.append(random.uniform(0.6, 1.6))
    return np.array(action)

  #valid function
  # takes new robot structure(shape)
  # returns True if shape is valid (no islands of voxels)
  def valid(self, shape):
    return (is_connected(shape) and
        (3 in shape or 4 in shape))
  
  #mutate function 
  # takes a clone of a robot(self) and a parent robot(parent)
  # modifies self to include structure and gene data from both self and parent
  # then mutates by changing one data point in either strucutre or genes randomly
  def mutate(self, parent):
    count = 0
    while count <= 5000:
      #create new set of data to modify
      new_shape = self.get_structure().copy()
      new_ampGenes = self.get_ampGenes().copy()
      new_timeGenes = self.get_timeGenes().copy()
      new_sensorGenes = self.get_sensorGenes().copy()
      new_bitmask = self.get_bitmask().copy()

      #set half of body/genes to co parent body/genes
      if parent != None:
        parent_shape = parent.get_structure()
        if random.random() > 0.5:
          rows = [2,3,4]
        else:
          rows = [3,4]
        for i in rows:
          new_shape[i] = parent_shape[i]
          new_ampGenes[i] = parent.get_ampGenes()[i]
          new_timeGenes[i] = parent.get_timeGenes()[i]
          new_sensorGenes[i] = parent.get_sensorGenes()[i]
          new_bitmask[i] = parent.get_bitmask()[i]

      #make MUTATION to body or genes
      pos = tuple(np.random.randint(0,4,2))
      if random.random() > 0.5:
        new_shape[pos] = np.random.randint(0,4)
      else:
        #choose which gene to update
        whichGene = random.random() * 4 
        rng  = np.random.default_rng()
        if (whichGene > 3):
          new_bitmask[pos] = abs(new_bitmask[pos]-1)
        elif (whichGene > 2):
          new_ampGenes[pos] += round(rng.normal(), 2)
        elif (whichGene > 1):
          new_timeGenes[pos] += round(rng.normal(), 2)
        else:
          new_sensorGenes[pos] += round(rng.normal(), 2)

      #check if mutation/crossbreeding resulted in functional structure
      if self.valid(new_shape):
        self.set_structure(new_shape)
        self.set_genes(new_bitmask, new_ampGenes, new_timeGenes, new_sensorGenes)
        break

      count += 1
    if count > 5000:
      raise Exception("Can't find a valid mutation after 5000 tries!")

  #generateRandomGenes function
  # takes an unused robot(self)
  # creates bitmask, sensor, time, and amp gene arrays
  # randomizes contents of these gene arrays and sets them to the defaults of self
  # (12/12/23) only used when creating robot from scratch, i.e. very beginning of sim
  def generateRandomGenes(self, ):
    #create gene arrays (same sizes as structure)
    sample = self.get_structure().copy()
    tempBitmask = sample.copy()
    tempSensorGenes = sample.copy()
    tempTimeGenes = sample.copy()
    tempAmpGenes = sample.copy()

    #loop through arrays and set data to random number [-6.28, 6.28]
    for i in range(len(tempBitmask)):
      for j in range(len(tempBitmask[i])):
        tempBitmask[i][j] = round(random.random())
        tempSensorGenes[i][j] = round((random.random()-0.5) * 2 * 6.28, 2)
        tempTimeGenes[i][j] = round((random.random()-0.5) * 2 * 6.28, 2)
        tempAmpGenes[i][j] = round((random.random()-0.5) * 2 * 6.28, 2)

    self.set_genes(tempBitmask, tempAmpGenes, tempTimeGenes, tempSensorGenes)
    
