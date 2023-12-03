import json, sys
import networkx as nx
import matplotlib.pyplot as plt
import csv

##important info for this file
# when calling in terminal, need one argument.
# argument = round # you want to examine(will examine all rounds before as well for some functions)

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

#compareScores takes the dataList defined by robotDataRead
#returns a datafile (data.csv) that contains the average scores and avergae alt scores of robots in each group, sorted by round descending
def compareScores(dataList):

  avgsPerRound = []
  AGroup = ['0,', '1,', '2,', '3,', '4,', '5,', '6,', '7,']
  BGroup = ['8,', '9,', '10', '11', '12', '13', '14', '15']

  for d in dataList:
    ACount = 0
    AStdTotal = 0
    AAltTotal = 0

    BCount = 0
    BStdTotal = 0
    BAltTotal = 0
    for rob in d:
      if (rob[0:2] in AGroup):
        ACount += 1
        AStdTotal += d[rob][4][0]
        AAltTotal += d[rob][4][1]
      elif (rob[0:2] in BGroup):
        BCount += 1
        BStdTotal += d[rob][4][0]
        BAltTotal += d[rob][4][1]
    AStdTotal = AStdTotal / ACount
    AAltTotal = AAltTotal / ACount
    BStdTotal = BStdTotal / ACount
    BAltTotal = BAltTotal / ACount
    avgsPerRound.append([AStdTotal, AAltTotal, BStdTotal, BAltTotal])

  with open('data.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['AStd', 'AAlt', 'BStd', 'BAlt'])
    for round in avgsPerRound:
      filewriter.writerow([round[0], round[1], round[2], round[3]])



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

  avgsPerRound = compareScores(robotDataList)  ## format = [AStandardScore, AAltScore, BStandardScore, BAltScore]
  print(avgsPerRound)

  # ancestryTree = getAncestryGraph(robotDataList, 222865)

