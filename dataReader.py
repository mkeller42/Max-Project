import json, sys
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import csv
import bisect

##important info for this file
# when calling in terminal, need one argument.
# argument = round # you want to examine(will examine all rounds before as well for many functions)

#returns array of datafiles containing world_data to be used
def worldDataRead(fileNum):
  dataList = []
  for i in range(0, int(fileNum)+10, 10):
    with open('./example_data/round' + str(i) + '/world_data_round' + str(i) + '.json', 'r') as f:
      # print(i)
      dataList.append(json.load(f))
  return dataList

#returns array of datafiles containing robot_data to be used
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
    AStdTotal = round((AStdTotal / ACount), 2)
    AAltTotal = round(AAltTotal / ACount, 2)
    BStdTotal = round(BStdTotal / ACount, 2)
    BAltTotal = round(BAltTotal / ACount, 2)
    avgsPerRound.append([AStdTotal, AAltTotal, BStdTotal, BAltTotal])

  with open('data.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['AStd', 'AAlt', 'BStd', 'BAlt'])
    for r in avgsPerRound:
      filewriter.writerow([r[0], r[1], r[2], r[3]])

#TEST ON NEW DATA (FROM CLAUS)
#percentiles calculates percentiles of fitness for each group of robots for every 10th round for each group (a/b)
#writes it to the file dataPercentiles.csv
def percentiles(dataList):
  AGroup = ['0,', '1,', '2,', '3,', '4,', '5,', '6,', '7,']

  totalPercentilesA = []
  totalPercentilesB = []
  #loop through each dataFile
  for d in dataList:
    aScoreList = []
    bScoreList = []
    #create sorted list of robot scores for each envo
    for rob in d:
      if (rob[0:2] in AGroup):
        bisect.insort(aScoreList, d[rob][4][0])
      else:
        bisect.insort(bScoreList, d[rob][4][0])
    
    #determine number of robots and each 10th percetile value
    aLength = len(aScoreList)
    bLength = len(bScoreList)
    if (bLength < 128):
      totalPercentilesA.append([None,None,None,None,None,None,None,None,None,None,None])
      totalPercentilesB.append([None,None,None,None,None,None,None,None,None,None,None])
      continue
    percentileJumpA = float(aLength/10)
    percentileJumpB = float(bLength/10)
    APercentileScores = []
    BPercentileScores = []

    #use sorted score array to find 10th percetile scores for entire robot population
    for i in range(0,10):
      APercentileScores.append(round(aScoreList[round(i*percentileJumpA)], 2))
      BPercentileScores.append(round(bScoreList[round(i*percentileJumpB)], 2))
    APercentileScores.append(round(aScoreList[len(aScoreList)-1], 2))
    BPercentileScores.append(round(bScoreList[len(bScoreList)-1], 2))
    totalPercentilesA.append(APercentileScores)
    totalPercentilesB.append(BPercentileScores)

  #after all data collected, add to csv "dataPercentiles.csv"
  with open('dataPercentiles.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['A0', 'A10', 'A20', 'A30', 'A40', 'A50', 'A60', 'A70', 'A80', 'A90', 'A100', 
                         'B0', 'B10', 'B20', 'B30', 'B40', 'B50', 'B60', 'B70', 'B80', 'B90', 'B100', 'round'])
    for i in range(len(totalPercentilesA)):
      filewriter.writerow([totalPercentilesA[i][0], totalPercentilesA[i][1], totalPercentilesA[i][2], totalPercentilesA[i][3], totalPercentilesA[i][4], totalPercentilesA[i][5], 
                           totalPercentilesA[i][6], totalPercentilesA[i][7], totalPercentilesA[i][8], totalPercentilesA[i][9], totalPercentilesA[i][10], 
                           totalPercentilesB[i][0], totalPercentilesB[i][1], totalPercentilesB[i][2], totalPercentilesB[i][3], totalPercentilesB[i][4], totalPercentilesB[i][5], 
                           totalPercentilesB[i][6], totalPercentilesB[i][7], totalPercentilesB[i][8], totalPercentilesB[i][9], totalPercentilesB[i][10],
                           i*10])


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
  # print(avgsPerRound)

  # percentiles(robotDataList)

  # ancestryTree = getAncestryGraph(robotDataList, 222865)

