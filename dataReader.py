import json, sys
import networkx as nx
import matplotlib.pyplot as plt

##important info for this file
# when calling in terminal, need one argument.
#argument = round # you want to examine(will examine all rounds before as well)

def worldDataRead(fileNum):
  dataList = []
  for i in range(0, int(fileNum)+10, 10):
    with open('./example_data/round' + str(i) + '/world_data_round' + str(i) + '.json', 'r') as f:
      # print(i)
      dataList.append(json.load(f))
  return dataList

def robotDataRead(fileNum):
  dataList = []
  for i in range(0, int(fileNum)+10, 10):
    with open('./example_data/round' + str(i) + '/robot_data_round' + str(i) + '.json', 'r') as f:
      # print(i)
      dataList.append(json.load(f))
  return dataList

def getFailRates(dataList):
  totalFailList = []
  finalString = ""
  
  for i in range(len(dataList[0]["failureRateWorldData"])): #for each column
    totalFailList.append(0)
    for d in dataList: #for each dataFile (round)
      failRates = d["failureRateWorldData"]

      if failRates[i][1] == 0:
        continue
      totalFailList[i] += float(failRates[i][0]/failRates[i][1])
    totalFailList[i] = totalFailList[i] / len(dataList)
    
  finalString += "Total Failure Rates so far:\n"
  for d in range(len(totalFailList)):
    out =  "Column %s: "%(d)
    if d == 7 or d == 8:
      finalString += "*"
    finalString += out + str(totalFailList[d]) + "\n"

  finalString += "* = boundary between two 'biomes'\n"
  return finalString

def getNewFitness(dataFile):
  finalString = ""

  # print(dataFile)
  
  finalString += "Avg. new robot score per column: (round "+str(dataFile["round"])+")\n"
  for i in range(len(dataFile["avgNewFitness"])):
    if i == 7 or i == 8:
      finalString += "*"
    finalString += "Column "+ str(i) + ": " + str(dataFile["avgNewFitness"][i]) + "\n"

  finalString += "* = boundary between two 'biomes'\n"
  return finalString

def getAvgScoreDiff(dataList, fileNum):
  finalString = "Average Score Difference from Parent by Column (up to Round " + str(fileNum) + ")\n"
  cols = []

  for col in range(len(dataList[0]["avgFitnessDiff"])):
    cols.append(0)
    for d in dataList:
      cols[col] += d["avgFitnessDiff"][col]
    cols[col] = cols[col] / len(dataList)
    if col == 8 or col == 7:
      finalString += "*"
    finalString += "Column " + str(col) + ": " + str(cols[col]) + "\n"
  
  return finalString

def getAncestryGraph(dataList, robotID):
  #return graph of ancestry
  G = nx.Graph()
  curGen = robotID
  # print(curGen)

  #for loop in dataList:
  count = 2530
  for f in reversed(dataList):
    #find robot id in most recent dataList
    while True:
      for rob in f:
        #if id == id
        if f[rob][2] == curGen:
          curRob = f[rob]
          curParents = curRob[3]
          
          #add node + edges to graph
          G.add_nodes_from(curParents, facecolor='R0')
          G.add_edges_from([(curRob[2], curParents[0]), (curRob[2], curParents[1])])
          #set robot as parents (original parent)
          curGen = curParents[0]
          continue
      count -= 10
      break
    #find parents' ids of robot
    
    #repeat

  nx.draw(G, with_labels=True)
  plt.savefig("tree.png")
  return nx.write_graphml(G, "example_graph")



if __name__ == "__main__":
  fileNum = sys.argv[1]
  indexNum = int(int(fileNum)/10)
  worldDataList = worldDataRead(fileNum)
  robotDataList = robotDataRead(fileNum)
  
  # failRates = getFailRates(worldDataList)
  # print(failRates)

  # fitLevels = getNewFitness(worldDataList[indexNum])
  # print(fitLevels)

  # avgScoreDiffs = getAvgScoreDiff(worldDataList, fileNum)
  # print(avgScoreDiffs)

  ancestryTree = getAncestryGraph(robotDataList, 222865)

