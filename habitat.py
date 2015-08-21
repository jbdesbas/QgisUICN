from geopandas import *
import pandas as pd
from copy import deepcopy
import matplotlib.pyplot as plt

shp='/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Habitat/mos_picardie/mos_picardie.shp'

habs={'Prairies':[2311,2312],'Plages':[3313,3314,3312,3311],'Pelouse':[3211,3321],'Parcs':[2220,1411,1421,1412,2113],'Marais':[4110],'Landes':[3220,3222],'Fourres':[3241,3242],'Forets':[3111,3112,3113,3121,3131,3123,3122,3132],'Estrans':[5220,4211,4230,4212],'Eau douce stagnante':[5122,5123,5121],'Eau courante':[5112,5111],'Culture':[2111,2210,2112,2420],'Mer':[5230],'Artificiel':[1124,1215,1113,1123,1122,1222,1211,1424,1221,1330,1121,1213,1112,1212,1111,1240,1311,1320,1331,1312,1422,1216,1423,1214,1125,1230]}




data = GeoDataFrame.from_file(shp)
data=data[data.CLC4_1992.notnull()] #Pour virer les enregistremetn foireux

data['CLC4_1992']=data['CLC4_1992'].astype('float32')
data['CLC4_2002']=data['CLC4_2002'].astype('float32')
data['CLC4_2010']=data['CLC4_2010'].astype('float32')

data['Hab1992']=""
data['Hab2002']=""
data['Hab2010']=""

for hab in habs:
	data.ix[(data.CLC4_1992.isin(habs[hab])),["Hab1992"]]=hab
	data.ix[(data.CLC4_2002.isin(habs[hab])),["Hab2002"]]=hab
	data.ix[(data.CLC4_2010.isin(habs[hab])),["Hab2010"]]=hab


area92=data.groupby(['Hab1992']).sum()['AREA']
area02=data.groupby(['Hab2002']).sum()['AREA']
area10=data.groupby(['Hab2010']).sum()['AREA']


area92.to_csv('/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Habitat/1992.csv')
area02.to_csv('/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Habitat/2002.csv')
area10.to_csv('/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Habitat/2010.csv')

#data.to_csv('/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Habitat/data.csv')

data_evolution=pda.DataFrame(dict(area92=area92,area02=area02,area10=area10))

data.to_file('/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Habitat/mos2.shp',driver='ESRI Shapefile')
