from evogym import WorldObject, EvoSim, is_connected, get_full_connectivity
import numpy as np
import random

class Robot():
    
  def __init__(self, sample, globalID, parScore) -> None:
    self.structure, self.connections = sample
    self.location = []
    self.trueLocation = []
    self.score = -99
    self.ID = globalID
    self.worldObject = self.createWorldObj()
    self.genes = self.generateRandomGenes(self.structure)
    self.parentFitness = parScore
    self.parentsIDs = None
    self.altscore = -99

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
    return self.genes

  def createWorldObj(self, ):
    robObject = WorldObject()
    robObject.load_from_array(
      name = 'robot',
      structure = self.structure,
      connections = self.connections)
    return robObject
    
  def getWorldObj(self, ):
    return self.worldObject
  
  def count_actuators(self):
    count = 0
    for _x in self.get_structure().flatten():
      if _x == 3 or _x == 4:
        count += 1
    return count

  def choiceAction(self, steps, action):
    if action == "evolve":
      return self.evolvedAction(steps)
    elif action == "random":
      return self.randomAction()
    elif action == "oscillate":
      return self.action(steps)
    return ValueError

  def evolvedAction(self, steps):
    action = []
    for i in range(len(self.structure)):
      for j in range(len(self.structure)):
        if self.structure[i][j] in [3,4]:
          action.append(np.sin(steps/3 + (self.genes[i][j]*0.1)) + 1)
    return np.array(action)
  
  def action(self, steps):
    action = []
    for _ in range(self.count_actuators()):
      action.append(np.sin(steps/3 + (_*0.1))+1)
    return np.array(action)
  
  def randomAction(self):
    action = []
    for _ in range(self.count_actuators()):
      action.append(random.uniform(0.6, 1.6))
    return np.array(action)
  
  def valid(self, shape):
    return (is_connected(shape) and
        (3 in shape or 4 in shape))
  
  def mutate(self, old_shape, old_genes, parent):
    
    count = 0
      
    while count <= 5000:

      new_shape = old_shape
      new_genes = old_genes

      if parent != None:
        parent_shape = parent.get_structure()
        if random.random() > 0.5:
          for i in range(2, 5):
            new_shape[i] = parent_shape[i]
        else:
          for i in range(3, 5):
            new_shape[i] = parent_shape[i]

      pos = tuple(np.random.randint(0,4,2))
      if random.random() > 0.5:
        new_shape[pos] = np.random.randint(0,4)
      else:
        new_genes[pos] = random.random() * 6.28

      if self.valid(new_shape):
        robot = new_shape
        break

      count += 1
    if count > 5000:
      raise Exception("Can't find a valid mutation after 5000 tries!")
    
    
    return robot
  
  def generateRandomGenes(self, structure):
    genes = structure.copy()
    for i in genes:
      for j, val in enumerate(i):
        i[j] = round(random.random() * 6.28, 2)
    # print(genes)
    return genes
    

