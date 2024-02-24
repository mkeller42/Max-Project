import json, sys
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import csv
import bisect

##important info for this file
# when calling in terminal, needs two arguments.
# argument 1 = round # you want to examine(will examine all rounds before as well for most functions)
# argument 2 = type of experiment. Options = trip_iso_ex, trip_ex, iso_ex, norm_ex 
# ^MUST BE EQUIVALENT TO EXPERIMENT TYPE   (triple isolated envos, triple envos, double isolated envos, double envos)

if sys.argv[2] == 'trip_iso_ex':
  AGroup = ['0,', '1,', '2,', '3,', '4,', '5,', '6,', '7,']
  no_env_list = ['8,', '17']
  BGroup = ['9,','10','11','12','13','14','15','16']
  CGroup = ['18','19','20','21','22','23','24','25']
  curr_ex = 1
elif sys.argv[2] == 'trip_ex':
  AGroup = ['0,', '1,', '2,', '3,', '4,', '5,', '6,', '7,']
  no_env_list = []
  BGroup = ['8,','9,','10','11','12','13','14','15']
  CGroup = ['16','17','18','19','20','21','22','23']
  curr_ex = 1
elif sys.argv[2] == 'iso_ex':
  AGroup = ['0,', '1,', '2,', '3,', '4,', '5,', '6,', '7,']
  no_env_list = ['8,']
  BGroup = ['9,','10','11','12','13','14','15','16']
  CGroup = []
  curr_ex = 0
elif sys.argv[2] == 'norm_ex':
  AGroup = ['0,', '1,', '2,', '3,', '4,', '5,', '6,', '7,']
  no_env_list = []
  BGroup = ['8,', '9,', '10', '11', '12', '13', '14', '15']
  CGroup = []
  curr_ex = 0
else:
  print("Error: incorrect experiment type. Try again")

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
#returns a datafile (data.csv) that contains the average scores and avergae alt scores of robots in each group, sorted by round
def compareScores(dataList):

  avgsPerRound = []
  for d in dataList:
    ACount = 0
    AStdTotal = 0
    AAltTotal = 0

    BCount = 0
    BStdTotal = 0
    BAltTotal = 0

    CCount = 0
    CStdTotal = 0
    CAltTotal = 0
    for rob in d:
      if (rob[0:2] in AGroup):
        ACount += 1
        AStdTotal += d[rob][4][0]
        AAltTotal += d[rob][4][1]
      elif (rob[0:2] in BGroup):
        BCount += 1
        BStdTotal += d[rob][4][0]
        BAltTotal += d[rob][4][1]
      elif (rob[0:2] in CGroup):
        CCount += 1
        CStdTotal += d[rob][4][0]
        CAltTotal += d[rob][4][1]
    try:
      AStdTotal = round((AStdTotal / ACount), 2)
      AAltTotal = round(AAltTotal / ACount, 2)
      BStdTotal = round(BStdTotal / ACount, 2)
      BAltTotal = round(BAltTotal / ACount, 2)
      CStdTotal = round(CStdTotal / ACount, 2)
      CAltTotal = round(CAltTotal / ACount, 2)
    except (ZeroDivisionError):
      continue
    avgsPerRound.append([AStdTotal, AAltTotal, BStdTotal, BAltTotal, CStdTotal, CAltTotal])

  with open('altEnvoData.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['AStd', 'AAlt', 'BStd', 'BAlt', 'CStd', 'CAlt'])
    for r in avgsPerRound:
      filewriter.writerow([r[0], r[1], r[2], r[3], r[4], r[5]])

#TEST ON NEW DATA (FROM CLAUS)
#percentiles calculates percentiles of fitness for each group of robots for every 10th round for each group (a/b)
#writes it to the file dataPercentiles.csv
def percentiles(dataList):

  totalPercentilesA = []
  totalPercentilesB = []
  totalPercentilesC = []
  #loop through each dataFile
  for d in dataList:
    aScoreList = []
    bScoreList = []
    cScoreList = []
    #create sorted list of robot scores for each envo
    for rob in d:
      if (rob[0:2] in AGroup):
        bisect.insort(aScoreList, d[rob][4][0])
      elif (rob[0:2] in BGroup):
        bisect.insort(bScoreList, d[rob][4][0])
      elif (rob[0:2] in CGroup):
        bisect.insort(cScoreList, d[rob][4][0])
    #determine number of robots and each 10th percetile value
    aLength = len(aScoreList)
    bLength = len(bScoreList)
    cLength = len(cScoreList)

    if (curr_ex == 1): #if a triple envo experiment
      if (cLength < 128 or bLength < 128):
        totalPercentilesA.append([None,None,None,None,None,None,None,None,None,None,None])
        totalPercentilesB.append([None,None,None,None,None,None,None,None,None,None,None])
        totalPercentilesC.append([None,None,None,None,None,None,None,None,None,None,None])
        continue
    else: #if a double envo experiment
      totalPercentilesC.append([None,None,None,None,None,None,None,None,None,None,None])
      if (bLength < 128 or aLength < 128):
        totalPercentilesA.append([None,None,None,None,None,None,None,None,None,None,None])
        totalPercentilesB.append([None,None,None,None,None,None,None,None,None,None,None])
        continue
    percentileJumpA = float(aLength/10)
    percentileJumpB = float(bLength/10)
    percentileJumpC = float(cLength/10)
    APercentileScores = []
    BPercentileScores = []
    CPercentileScores = []

    #use sorted score array to find 10th percetile scores for entire robot population
    for i in range(0,10):
      APercentileScores.append(round(aScoreList[round(i*percentileJumpA)], 2))
      BPercentileScores.append(round(bScoreList[round(i*percentileJumpB)], 2))
      CPercentileScores.append(round(cScoreList[round(i*percentileJumpC)], 2))
    APercentileScores.append(round(aScoreList[len(aScoreList)-1], 2))
    BPercentileScores.append(round(bScoreList[len(bScoreList)-1], 2))
    CPercentileScores.append(round(cScoreList[len(cScoreList)-1], 2))
    totalPercentilesA.append(APercentileScores)
    totalPercentilesB.append(BPercentileScores)
    totalPercentilesC.append(CPercentileScores)

  #after all data collected, add to csv "dataPercentiles.csv"
  with open('dataPercentiles.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['A0', 'A10', 'A20', 'A30', 'A40', 'A50', 'A60', 'A70', 'A80', 'A90', 'A100', 
                         'B0', 'B10', 'B20', 'B30', 'B40', 'B50', 'B60', 'B70', 'B80', 'B90', 'B100', 
                         'C0', 'C10', 'C20', 'C30', 'C40', 'C50', 'C60', 'C70', 'C80', 'C90', 'C100', 'round'])
    for i in range(len(totalPercentilesA)):
      filewriter.writerow([totalPercentilesA[i][0], totalPercentilesA[i][1], totalPercentilesA[i][2], totalPercentilesA[i][3], totalPercentilesA[i][4], totalPercentilesA[i][5], 
                           totalPercentilesA[i][6], totalPercentilesA[i][7], totalPercentilesA[i][8], totalPercentilesA[i][9], totalPercentilesA[i][10], 
                           totalPercentilesB[i][0], totalPercentilesB[i][1], totalPercentilesB[i][2], totalPercentilesB[i][3], totalPercentilesB[i][4], totalPercentilesB[i][5], 
                           totalPercentilesB[i][6], totalPercentilesB[i][7], totalPercentilesB[i][8], totalPercentilesB[i][9], totalPercentilesB[i][10],
                           totalPercentilesC[i][0], totalPercentilesC[i][1], totalPercentilesC[i][2], totalPercentilesC[i][3], totalPercentilesC[i][4], totalPercentilesC[i][5], 
                           totalPercentilesC[i][6], totalPercentilesC[i][7], totalPercentilesC[i][8], totalPercentilesC[i][9], totalPercentilesC[i][10],
                           i*10])

#UNFINISHED - CURRENTLY ONLY WORKS FOR TRIP_EXO EXPERIMENTS
# this function will take the robotDataList and return a "gene difference" value for both genes and body structure.
# initial idea: compares genes to highest scorer each round? to original robot?
def compareGenes(dataList):

  totalComparisonList = []
  final = []
  for i in range(len(AGroup) * 16 + len(BGroup) * 16 + len(CGroup) * 16):
    totalComparisonList.append([])

  

  for d in dataList:
    localList = totalComparisonList
    defGenes = None
    defStruct = None
    robEnvo = None
    for rob in d:
      if (rob[0:2] in AGroup):
        robEnvo = 1
      elif (rob[0:2] in BGroup):
        robEnvo = 2
      else:
        robEnvo = 3
      robCoords = [int(rob[0:6].split(',')[0]), int(rob[0:6].split(',')[1])]
      robIndex = (robCoords[1] * 24) + robCoords[0]
      structDiff = 0
      geneDiff = 0
      if defGenes == None:
        defStruct = d[rob][0]
        defGenes = d[rob][1]
      else:
        curStruct = d[rob][0]
        curGenes = d[rob][1]
        for row in range(len(curStruct)):
          for i in range(len(curStruct[row])):
            if curStruct[row][i] != defStruct[row][i]:
              structDiff += 1
        for gene in range(len(curGenes)):
          for row in range(len(curGenes[gene])):
            for i in range(len(curGenes[gene][row])):
              if abs(curGenes[gene][row][i] - defGenes[gene][row][i]) >= 1:
                geneDiff += 1
      localList[robIndex] = [structDiff, geneDiff, robEnvo, round(d[rob][4][0]-d[rob][4][1], 2)]
    final.append(localList.copy())


  with open('geneComparison.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['[0,0]','[0,1]','[0,2]','[0,3]','[0,4]','[0,5]','[0,6]','[0,7]','[0,8]','[0,9]','[0,10]','[0,11]','[0,12]','[0,13]','[0,14]','[0,15]','[0,16]','[0,17]','[0,18]','[0,19]','[0,20]','[0,21]','[0,22]','[0,23]',
                         '[1,0]','[1,1]','[1,2]','[1,3]','[1,4]','[1,5]','[1,6]','[1,7]','[1,8]','[1,9]','[1,10]','[1,11]','[1,12]','[1,13]','[1,14]','[1,15]','[1,16]','[1,17]','[1,18]','[1,19]','[1,20]','[1,21]','[1,22]','[1,23]',
                         '[2,0]','[2,1]','[2,2]','[2,3]','[2,4]','[2,5]','[2,6]','[2,7]','[2,8]','[2,9]','[2,10]','[2,11]','[2,12]','[2,13]','[2,14]','[2,15]','[2,16]','[2,17]','[2,18]','[2,19]','[2,20]','[2,21]','[2,22]','[2,23]',
                         '[3,0]','[3,1]','[3,2]','[3,3]','[3,4]','[3,5]','[3,6]','[3,7]','[3,8]','[3,9]','[3,10]','[3,11]','[3,12]','[3,13]','[3,14]','[3,15]','[3,16]','[3,17]','[3,18]','[3,19]','[3,20]','[3,21]','[3,22]','[3,23]',
                         '[4,0]','[4,1]','[4,2]','[4,3]','[4,4]','[4,5]','[4,6]','[4,7]','[4,8]','[4,9]','[4,10]','[4,11]','[4,12]','[4,13]','[4,14]','[4,15]','[4,16]','[4,17]','[4,18]','[4,19]','[4,20]','[4,21]','[4,22]','[4,23]',
                         '[5,0]','[5,1]','[5,2]','[5,3]','[5,4]','[5,5]','[5,6]','[5,7]','[5,8]','[5,9]','[5,10]','[5,11]','[5,12]','[5,13]','[5,14]','[5,15]','[5,16]','[5,17]','[5,18]','[5,19]','[5,20]','[5,21]','[5,22]','[5,23]',
                         '[6,0]','[6,1]','[6,2]','[6,3]','[6,4]','[6,5]','[6,6]','[6,7]','[6,8]','[6,9]','[6,10]','[6,11]','[6,12]','[6,13]','[6,14]','[6,15]','[6,16]','[6,17]','[6,18]','[6,19]','[6,20]','[6,21]','[6,22]','[6,23]',
                         '[7,0]','[7,1]','[7,2]','[7,3]','[7,4]','[7,5]','[7,6]','[7,7]','[7,8]','[7,9]','[7,10]','[7,11]','[7,12]','[7,13]','[7,14]','[7,15]','[7,16]','[7,17]','[7,18]','[7,19]','[7,20]','[7,21]','[7,22]','[7,23]',
                         '[8,0]','[8,1]','[8,2]','[8,3]','[8,4]','[8,5]','[8,6]','[8,7]','[8,8]','[8,9]','[8,10]','[8,11]','[8,12]','[8,13]','[8,14]','[8,15]','[8,16]','[8,17]','[8,18]','[8,19]','[8,20]','[8,21]','[8,22]','[8,23]',
                         '[9,0]','[9,1]','[9,2]','[9,3]','[9,4]','[9,5]','[9,6]','[9,7]','[9,8]','[9,9]','[9,10]','[9,11]','[9,12]','[9,13]','[9,14]','[9,15]','[9,16]','[9,17]','[9,18]','[9,19]','[9,20]','[9,21]','[9,22]','[9,23]',
                         '[10,0]','[10,1]','[10,2]','[10,3]','[10,4]','[10,5]','[10,6]','[10,7]','[10,8]','[10,9]','[10,10]','[10,11]','[10,12]','[10,13]','[10,14]','[10,15]','[10,16]','[10,17]','[10,18]','[10,19]','[10,20]','[10,21]','[10,22]','[10,23]',
                         '[11,0]','[11,1]','[11,2]','[11,3]','[11,4]','[11,5]','[11,6]','[11,7]','[11,8]','[11,9]','[11,10]','[11,11]','[11,12]','[11,13]','[11,14]','[11,15]','[11,16]','[11,17]','[11,18]','[11,19]','[11,20]','[11,21]','[11,22]','[11,23]',
                         '[12,0]','[12,1]','[12,2]','[12,3]','[12,4]','[12,5]','[12,6]','[12,7]','[12,8]','[12,9]','[12,10]','[12,11]','[12,12]','[12,13]','[12,14]','[12,15]','[12,16]','[12,17]','[12,18]','[12,19]','[12,20]','[12,21]','[12,22]','[12,23]',
                         '[13,0]','[13,1]','[13,2]','[13,3]','[13,4]','[13,5]','[13,6]','[13,7]','[13,8]','[13,9]','[13,10]','[13,11]','[13,12]','[13,13]','[13,14]','[13,15]','[13,16]','[13,17]','[13,18]','[13,19]','[13,20]','[13,21]','[13,22]','[13,23]',
                         '[14,0]','[14,1]','[14,2]','[14,3]','[14,4]','[14,5]','[14,6]','[14,7]','[14,8]','[14,9]','[14,10]','[14,11]','[14,12]','[14,13]','[14,14]','[14,15]','[14,16]','[14,17]','[14,18]','[14,19]','[14,20]','[14,21]','[14,22]','[14,23]',
                         '[15,0]','[15,1]','[15,2]','[15,3]','[15,4]','[15,5]','[15,6]','[15,7]','[15,8]','[15,9]','[15,10]','[15,11]','[15,12]','[15,13]','[15,14]','[15,15]','[15,16]','[15,17]','[15,18]','[15,19]','[15,20]','[15,21]','[15,22]','[15,23]'])
    for i in range(len(final)):
      filewriter.writerow(final[i])
      
  #do some stuff blah blah
  #add to file or something

  return


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

  # compareScores(robotDataList)  ## format = [AStandardScore, AAltScore, BStandardScore, BAltScore, CStandardScore, CAltScore]

  # percentiles(robotDataList)

  compareGenes(robotDataList)

  # ancestryTree = getAncestryGraph(robotDataList, 222865)

