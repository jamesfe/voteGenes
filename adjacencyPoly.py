import arcpy
import pickle
import random as r
import sys
import time

r.seed(time.time())

class precinct:
    def __init__(self, a, b, precID, adjacent):
        self.a = a
        self.b = b
        self.precID = precID
        self.adj = adjacent
    def findValids(self, blackList):
        return(self.adj-blackList)
    def __repr__(self):
        return(str(self.precID)+" has "+str(self.a)+", "+str(self.a)+" and is adj to: "+str(self.adj))

def printSol(inList):
##    print inList
    for k in range(0, len(inList)-1):
        print '"PREC_IDENT" IN '+str([i.precID for i in inList[k]]).replace("[", "(").replace("]", ")")
##            print '"PREC_IDENT" IN '+str([i.precID for i in solPool[sn]]).replace("[", "(").replace("]", ")")

def main(inShp):
##    featureDB, adjacencyDB = genAdjacency(inShp)
##    fFeat = open('fDB.pickle', 'wb')
##    pickle.dump(featureDB, fFeat)
##    fFeat.close()
##    aFeat = open('aDB.pickle', 'wb')
##    pickle.dump(adjacencyDB, aFeat)
##    aFeat.close()
    print "Loading data..."
    featureDB = pickle.load(open('fDB.pickle', 'rb'))
    adjacencyDB = pickle.load(open('aDB.pickle', 'rb'))
    ##tempSol = generateSolution(featureDB, adjacencyDB)
    numSols = 10
    print("Calculating "+str(numSols)+" solutions...")
    solMat = [genSol2(featureDB, adjacencyDB) for i in range(0, numSols)]
    for sol in range(0, len(solMat)):
        dPop = []
        solMD = []
        for k in solMat[sol]:
            totalPop = sum([r.a+r.b for r in k])
            numA = sum([r.a for r in k])
            numB = sum([r.b for r in k])
            solMD.append([totalPop, numA, numB])
            #print [totalPop, numA, numB],
        a0 = (sum([i[0] for i in solMD])*1.0)/len(solMD)
        a1 =  (sum([i[1] for i in solMD])*1.0)/len(solMD)
        a2 = (sum([i[2] for i in solMD])*1.0)/len(solMD)
        v0 = (sum([abs(i[0]-a0) for i in solMD])*1.0)/len(solMD)
        v1 = (sum([abs(i[1]-a1) for i in solMD])*1.0)/len(solMD)
        v2 = (sum([abs(i[2]-a2) for i in solMD])*1.0)/len(solMD)
        solMat[sol].append([v0,a1,a2])
        solMD = []
    r = min([i[5][0] for i in solMat])
    print "Min is: "+str(r)
    for k in solMat:
        if(k[5][0] == r):
            printSol(k)

def genSol2(fDB, aDB):
    precPool = []
    for k in fDB:
        precPool.append(precinct(k[1], k[2], k[0], set(aDB[k[0]])))
    rSols = 5
    solPool = [[] for i in range(rSols)]
    count = 0
    blackList = set()
    
    for k in range(rSols):
        target = precPool[r.randint(0, len(precPool)-1)]
        precPool.remove(target)
        solPool[k].append(target)
        blackList.add(target.precID)
        
    while(len(precPool)>0):
        count+=1
        if(count>5000):
            print "Counting break: "
            break
        for s in solPool:
            validPool = set()
            for prec in s:
                validPool = validPool.union(prec.findValids(blackList))
            validPool = list(validPool)
            if(len(validPool)>0):
                target = validPool[r.randint(0, len(validPool)-1)]
                for k in precPool:
                    if(k.precID==target):
                        tgtPrec = k
                ##print tgtPrec
                precPool.remove(tgtPrec)
                s.append(tgtPrec)
                blackList.add(tgtPrec.precID)
##    for sn in range(rSols):
##        print '"PREC_IDENT" IN '+str([i.precID for i in solPool[sn]]).replace("[", "(").replace("]", ")")
    return(solPool)
            
def generateSolution(fDB, aDB):
    reqParts = [(2, 1, 2), (1,2,3)] ## we want 1>2 3 times and 2>1 2 times
    blackList = set()
    validList = set()
    currentSolution = set()
    currentASum = 0
    currentBSum = 0
    totalSolution = []
    for req in reqParts:
        print "Req 2: ", req[2]
        while(req[2]>0):
            currentSolution = set()
            blackList = set()
            currentASum = 0
            currentBSum = 0            
            for i in range(0, len(totalSolution)):
                blackList = blackList.union(set(totalSolution[i]))
            currentASum = 0
            currentBSum = 0
            noSolution = True
            while(len(currentSolution)==0):
                k = fDB[r.randint(0, len(fDB)-1)]
##                print req[0], req[1], k[req[0]], k[req[1]]
                if(k[0] not in blackList) & (k[req[0]] > k[req[1]]):
                    blackList.add(k[0])
                    currentSolution.add(k[0])
                    validList = validList.union(aDB[k[0]]) ## adjacency with this PREC_IDENT
                    currentASum = k[req[0]]
                    currentBSum = k[req[1]]
            count = 0
            print validList
            while(True):
                count+=1
                if(count>10000):
                    print "Forcibly Killing the program."
                    sys.exit()
                if(count>5000):
                    noSolution = True
                    print currentSolution
                    
                    print "Count Fail."
                    count = 0
                    break
                if(len(validList)==0):
                    if(currentASum+currentBSum>50000):
                        noSolution = False
                        print currentSolution
                        print "Ding!"
                        break
                    else:
                        noSolution = True
                        print currentSolution                        
                        print "ValidList Fail."
                        break
                pA = list(validList)[r.randint(0, len(validList)-1)]
##                print "Proposed addition: ",pA
                pA = fDB[[i for i in range(len(fDB)) if(fDB[i][0]==pA)][0]]
                if(currentASum+pA[req[0]] > currentASum+pA[req[1]]):
                    currentSolution.add(pA[0])
##                    print "Adding ",pA[0]
                    blackList.add(pA[0])
                    currentASum+=pA[req[0]]
                    currentBSum+=pA[req[1]]
                    validList = set()
                    for i in currentSolution:
                        validList = validList.union(aDB[i])
                    validList = validList-blackList
##                print validList
            if(not noSolution):
                totalSolution.append([currentSolution])
                req[2]-=1
                print "Exit: ", totalSolution
            print "out"
        
    

def genAdjacency(inShp):
    sCursor = arcpy.SearchCursor(inShp)
    featureDB = []
    for n in sCursor:
        cPtList = []
        nParts = n.getValue("Shape").partCount
        for i in range(0, nParts):
            shape = n.getValue("Shape").getPart(i)
            for pt in shape:
                x = int(pt.X)
                y = int(pt.Y)
                cPtList.append((x,y))
        dem = int(n.getValue("ObamaBiden"))
        rep = int(n.getValue("McCainPali"))
        prec = int(n.getValue("PREC_IDENT"))
        featureDB.append((prec, dem, rep, set(cPtList)))
    print len(featureDB)
    attribData = [(i[0], i[1], i[2]) for i in featureDB]
    adjacencyDB = dict()
    for k in attribData:
        adjacencyDB[k[0]] = []
    for i in range(0, len(featureDB)):
        print featureDB[i][0]
        for j in range(i+1, len(featureDB)):
            if(len(featureDB[i][3].intersection(featureDB[j][3]))>0):
                adjacencyDB[featureDB[i][0]].append(featureDB[j][0])
                adjacencyDB[featureDB[j][0]].append(featureDB[i][0])

    return(featureDB, adjacencyDB)
    

if(__name__=="__main__"):
    main('./FFXVotes_DissJoin.shp')
