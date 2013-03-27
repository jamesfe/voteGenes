#import arcpy
import pickle
import random as r
import sys, time, copy
from operator import itemgetter
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
        return(str(self.precID)+" has "+str(self.a)+", "+str(self.b)+" and is adj to: "+str(self.adj))

class fullSol:
    """a class to represent a full solution - a list of district solutions
        coupled with a bunch of functions to see how 'fit' they are."""
    def __init__(self):
        """init just creates an empty list for districts to go in """
        self.sList = []
    def addDistrict(self, dist):
        """ addDistrict adds dist to the current list of districts.
            no error checking to ensure you're not overlapping """
        self.sList.append(singleSol(dist))
    def returnDistrictTotals(self):
        """returnDistrictTotals - returns a balance of a's and b's
            in short, if it returns x>0 there are x more a's than b's """
        balanceTotal = 0
        for k in self.sList:
            a,b = k.calcABPopTotals()
            if(a>b):
                balanceTotal+=1
            else:
                balanceTotal-=1
        return(balanceTotal)
    def printQuery(self):
        """ returns ArcGIS queries that can be pasted into a layer for a quick check."""
        rt = ""
        for sol in self.sList:
            rt += sol.query()+"\n"
        return(rt)
    def popVariance(self):
        """What's the population variance for this solution? """
        totalPop = sum([i.population() for i in self.sList])
        avgPop = (totalPop*1.0)/len(self.sList)
        totalVar = sum([abs(avgPop-i.population()) for i in self.sList])/len(self.sList)
        return(totalVar)
    def printTable(self):
        """ Returns dictionary of precIDs (or PREC_IDENT, SHP attribute)
             as well as an enumeration of the district. """
        precTable = dict()
        for k in range(0, len(self.sList)):
            for prec in self.sList[k].PDL:
                if(prec.precID not in precTable):
                    precTable[prec.precID] = k
        return(precTable)
    def printABTotals(self):
        for k in self.sList:
            print k.calcABPopTotals(),
    def mutate1(self):
        """ Simple mutation.  Finds a border precinct and swaps 
            it with one of it's neighbors."""
        rList = r.randint(0, len(self.sList)-1)
        flipTgt, flipPtr = self.sList[rList].findFlipper1()
        ## flipTgt, flipPtr are int precIDs
        flipObject = 0
        #print "FT: ",flipTgt
        for ptr in self.sList[rList].PDL:
            if(ptr.precID==flipTgt):
                flipObject = ptr
                #print "FO: ",flipObject
                self.sList[rList].PDL.remove(flipObject)
                break
        for i in self.sList:
            if(flipPtr in [_.precID for _ in i.PDL]):
                ## we have found the solution we need to swap with
                for ptr in i.PDL:
                    #print ptr, flipObject
                    if(ptr.precID==flipPtr):
                        holdPtr = ptr
                        i.PDL.remove(holdPtr)
                        i.PDL.append(flipObject)
                        #print "HP: ",holdPtr
                        self.sList[rList].PDL.append(holdPtr)
                        break

    def mutate2(self):
        t = 0
        while(t<=5):
            rList = r.randint(0, len(self.sList)-1)
            t = len(self.sList[rList].PDL)
        tgtPDLLen = len(self.sList[rList].PDL)
        rListPI = set([i.precID for i in self.sList[rList].PDL])
        ct = 1
        targetFlip = 0
        while(ct==1):
            tgtObj = r.sample(self.sList[rList].PDL, 1)[0]
            if(len(tgtObj.adj-rListPI)>1):
                ct = 0
                targetFlip = tgtObj
                targetList = r.sample(tgtObj.adj, 1)[0]
                break
        ## hopefully targetFlip != 0
        tgtListNum = -1
        for i in [_ for _ in range(0, len(self.sList)) if _ != rList]:
            self.sList[i].retObjByPrecID(targetList)
            tgtListNum = i
        if(tgtListNum!=-1):
            self.sList[tgtListNum].PDL.append(targetFlip)
            self.sList[rList].PDL.remove(targetFlip)
    def fitness2(self):
        fmult = self.returnDistrictTotals()
        if(fmult<1):
            fmult = 1
        return(fmult*self.popVariance())


class singleSol:
    def __init__(self, precDataList):
        self.PDL = precDataList
        self.popVar = -1
        self.totA = -1
        self.totB = -1
    def retObjByPrecID(self, precID):
        for _ in self.PDL:
            if(_.precID==precID):
                return(_)
        return(-1)
    def findFlipper1(self):
        """ finds a precinct on the edge of the current solution that we can flip. """
        flipFound = 0
        flipPartner = 0 ## initialize
        while(flipFound==0): ## possibly a risk of infinite loop? everything has a boundary.
            tgtFlip = r.randint(0, len(self.PDL)-1)
            tgtAdjacents = self.PDL[tgtFlip].adj
            tgtFlip = self.PDL[tgtFlip].precID
            for k in self.PDL:
                if(k.precID in tgtAdjacents):
                    tgtAdjacents.remove(k.precID)
            if(len(tgtAdjacents)>0):
                tgtAdjacents = list(tgtAdjacents)
                flipPartner = tgtAdjacents[r.randint(0, len(tgtAdjacents)-1)]
                flipFound = 1
                break
        return(tgtFlip, flipPartner)
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
    def calcABPopTotals(self):
        self.totPopA = 0
        self.totPopB = 0
        for k in self.PDL:
            self.totPopA+=k.a
            self.totPopB+=k.b
        return(self.totPopA, self.totPopB)
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
    print time.asctime()
    start = time.time()
    print "Loading data..."
    featureDB = pickle.load(open('fDB.pickle', 'rb'))
    adjacencyDB = pickle.load(open('aDB.pickle', 'rb'))
    """
    generates some solutions...saves them 
    solList = []
    for i in range(0, 50):
        t, s = genTestSol(featureDB, adjacencyDB)
        if(t<5):
            solList.append(s)
    fitness = []
    for t in solList:
        fitness.append(t.returnDistrictTotals())
    fitness.sort()
    print fitness
        
    pickle.dump(solList, file('subSol.pickle', 'wb'))
    print time.asctime()
    print time.time()-start
    """
    solDB = []
    nOrgs = 100
    numMutes = 100
    newBlood = nOrgs/10
    for i in range(0, nOrgs):
        t,s = genTestSol(featureDB, adjacencyDB)
        solDB.append(s)
    print "Generated ",len(solDB), " solutions"
    for kMute in range(0, numMutes):
        avgOrgFitness = sum([i.fitness2() for i in solDB])/len(solDB)
        print avgOrgFitness
        rmList = []
        for t in range(0, nOrgs):
            if(solDB[t].fitness2() < avgOrgFitness-1):
                rmList.append(t)
        rmList.sort(reverse=True)
        for i in rmList:
            solDB.pop(i)
        for k in range(0, nOrgs-len(solDB)-newBlood):
            dc = copy.copy(solDB[k])
            dc.mutate2()
            solDB.append(dc)
        for k in range(0, newBlood):
            t,s = genTestSol(featureDB, adjacencyDB)
            solDB.append(s)
    t = []
    for _ in range(0, len(solDB)):
        t.append((solDB[_].fitness2(), _))
    t = sorted(t,  key=itemgetter(0))
    print solDB[t[0][1]].printQuery()

    """ first code to use mutate2:
    t,s = genTestSol(featureDB, adjacencyDB)
    print "Found solution: "
    print s.printQuery()
    print "Mutating: "
    count = 0
    startTime = time.time()
    fit = 100
    while(fit>=1):
        count+=1
        if(count>100):
            break
        s.mutate2()
        cF = fit
        fit = s.fitness2()
        if(cF!=fit):
            print "Current fitness: ",fit
    print "Mutated: "
    print s.printQuery()
    print "that took ", abs(time.time()-start)

    """
    """
## below code creates a large quantity of solutions for testing
    print "Attempting solutions."
    t = 5
    s = fullSol() 
    count = 0
    mainTable = dict()
    solList = []
    for p in featureDB:
        mainTable[p[0]] = []
    while(t!=-1):
        count+=1
        if(count>10000):
            print "Out of time."
            break
        if(count%100==0):
            print count,
        t, s = genTestSol(featureDB, adjacencyDB)
        if(t==1):
            solList.append(s)
            dTable = s.printTable()
            s.printABTotals()
            for k in dTable:
                mainTable[k].append(dTable[k])

    print s.printQuery()
    print s.returnDistrictTotals()
    print s.popVariance()
    tbOut = file("tbOutPop3.csv", 'w')
    fOut = ['d'+str(i) for i in range(0, len(mainTable[701]))]
    tbOut.write("PREC_ID,"+str(fOut).replace("[", "").replace("]", "").replace("'", "")+"\n")
    for ct in range(0, len(solList)):
        print ct, solList[ct].popVariance()
        
    for i in mainTable:
        tbOut.write(str(i)+","+str(mainTable[i]).replace("[", "").replace("]", "")+"\n")
        
    tbOut.close()
    """
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
    """creates a solutiona nd returns it and it's total district weights to the user"""
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
