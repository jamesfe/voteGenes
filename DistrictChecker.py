"""district quick checker - by jim ferrara
james.ferrara@gmail.com

Set up parameters in toolbox as:

0: Layer File
1: Field (User picks field in which # of democrats per block live)
2: Field (Field in which # of reps per block live)
3: Field (Field in which district identifier is located)


"""

import arcpy

def message(x):
    arcpy.AddMessage(str(x))

def main(shp, dems, reps, district):
    message([shp, dems, reps, district])
    t = arcpy.SearchCursor(shp)
    districtTotals = dict()
    for k in t:
        dm = k.getValue(dems)
        rp = k.getValue(reps)
        tot = dm+rp
        dist = k.getValue(district)
        if(dist not in districtTotals):
            districtTotals[dist] = (tot, dm, rp)
        else:
            districtTotals[dist] = (districtTotals[dist][0]+tot, \
                                    districtTotals[dist][1]+dm, \
                                    districtTotals[dist][2]+rp)
    del t
    maxVal = max([districtTotals[i][0] for i in districtTotals])
    minVal = min([districtTotals[i][0] for i in districtTotals])
    message("Max District Population: "+str(maxVal))
    message("Min District Population: "+str(minVal))
    message("Minimum allowable: "+str(maxVal/3.0))
    message("Maximum allowable: "+str(minVal*3.0))
    for i in districtTotals:
        dl = districtTotals[i][2] - districtTotals[i][1]
        if(districtTotals[i][2]>districtTotals[i][1]):
            app = "REPUBLICAN"
        else:
            app = "DEMOCRAT"
        message("District "+str(i)+" has population "+str(districtTotals[i][0])+\
                " with "+str(districtTotals[i][1])+"/"\
                +str(districtTotals[i][2])+" dem/rep and overall "+app+" by "+str(dl))

if(__name__=="__main__"):
    main(arcpy.GetParameterAsText(0), arcpy.GetParameterAsText(1), \
         arcpy.GetParameterAsText(2), arcpy.GetParameterAsText(3))
