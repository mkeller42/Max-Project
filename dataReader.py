import json, sys

def dataRead():
  fileNum = sys.argv[1]
  dataList = []
  for i in range(int(int(fileNum)/10)):
    with open('./saved_data/dataRound' + str(i*10) + '.json', 'r') as f:
      dataList.append(json.load(f))
  return dataList
  
    

if __name__ == "__main__":
  dataList = dataRead()
  totalFailList = []
  
  failRates = json.loads(dataList[0]["failureRateWorldData"])
  for i in range(len(failRates)): #for column
    totalFailList.append(0)
    for d in dataList: #for dataFile (round)
      failRates = json.loads(d["failureRateWorldData"])

      if failRates[i][1] == 0:
        continue
      totalFailList[i] += float(failRates[i][0]/failRates[i][1])
    
  print("Total Failure Rates so far:")
  for d in range(len(failRates)):
    out =  "Column %s: "%(d)
    if failRates[d][1] == 0:
      print(out)
      continue
    elif d == len(failRates)/2 or d == len(failRates)/2-1:
      print("*" + out + str(float(failRates[d][0]/failRates[d][1])))
      continue
    print(out + str(float(failRates[d][0]/failRates[d][1])))