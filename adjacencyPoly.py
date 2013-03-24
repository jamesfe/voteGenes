#import arcpy
import pickle
import random as r
import sys
import time
r.seed(time.time())

class precinct:
    """a class to store demographic and graph information about precincts"""
    def __init__(self, a, b, precID, adjacent):
        """initialization routine:
        a - demographic (dems) 
        b - demographic (reps)
        precID - PREC_IDENT from shapefile
        adjacent - list of adjacent PRECIDs"""
        self.a = a
        self.b = b
        self.precID = precID
        self.adj = adjacent
    def findValids(self, blackList):
        """ findValids - find valid, adjacent precincts
        blackList - set of non-valid precID values"""
        return(self.adj-blackList)
    def __repr__(self):
        return(str(self.precID)+" has "+str(self.a)+", "+str(self.a)+" and is adj to: "+str(self.adj))

class fullSol:
    def __init__(self):
        self.sList = []
    def addDistrict(self, dist):
        self.sList.append(singleSol(dist))
    def returnDistrictTotals(self):
        """returnDistrictTotals - returns a balance of a's and b's
            in short, if it returns x>0 there are x more a's than b's """
        balanceTotal = 0
        for k in self.sList:
            a,b = k.calcABTotals()
            if(a>b):
                balanceTotal+=1
            else:
                balanceTotal-=1
        return(balanceTotal)
    def printQuery(self):
        rt = ""
        for sol in self.sList:
            rt += sol.query()+"\n"
        return(rt)
    def popVariance(self):
        totalPop = sum([i.population() for i in self.sList])
        avgPop = (totalPop*1.0)/len(self.sList)
        totalVar = sum([abs(avgPop-i.population()) for i in self.sList])/len(self.sList)
        return(totalVar)
 
class singleSol:
    def __init__(self, precDataList):
        self.PDL = precDataList
        self.popVar = -1
        self.totA = -1
        self.totB = -1
    def population(self):
        return(sum([i.a+i.b for i in self.PDL]))
    def calcABTotals(self):
        self.totA = 0
        self.totB = 0    
        for k in self.PDL:
            if(k.a>k.b):
                self.totA+=1
            else:
                self.totB+=1
        return(self.totA, self.totB)
    def query(self):
        qstr = '"PREC_IDENT" IN '+str([i.precID for i in self.PDL]).replace("[", "(").replace("]", ")")
        return(qstr)

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
    print "Attempting solutions."
    t = 5
    s = fullSol() 
    count = 0
    while(t!=3):
        count+=1
        if(count>10000):
            print "Out of time."
            break
        if(count%100==0):
            print count,
        t, s = genTestSol(featureDB, adjacencyDB)

    print s.printQuery()
    print s.returnDistrictTotals()
    print s.popVariance()
    """
    numSols = 10000
    print("Calculating "+str(numSols)+" solutions...")
    solMat = [genSol2(featureDB, adjacencyDB) for i in range(0, numSols)]
    print("Solutions generated - moving on to evaluation...")
    solutions = []
    for sol in solMat:
        t = fullSol()
        for k in sol:
            t.addDistrict(k)
        solutions.append(t)
   
    for sol in solutions:
        abTot = sol.returnDistrictTotals()
        if(abTot==1):
            print "AB Total: ",abTot
            print sol.printQuery()
            print "Variance: ",sol.popVariance()
    """

def genTestSol(fDB, aDB):
    pSol = genSol2(fDB, aDB)
    tester = fullSol()
    for k in pSol:
        tester.addDistrict(k)
    return(tester.returnDistrictTotals(), tester)

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
    return(solPool)
        
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
