#Data relative au groupe de faune (maille prospecte et nombre citation selon periode)

import geopandas as gpd
import pandas as pd
import os
from geopandas.tools import sjoin


path='/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Orthopteres/Donnees/'
#maillage=gpd.GeoDataFrame.from_file('/home/jb/Code/python/UICN/V2/grille/2km_Picardie.shp')
maillage=gpd.GeoDataFrame.from_file('/home/users/jbdesbas/Documents/ListesRouges/Evaluation/grilles/2km_Picardie.shp')

annee_min=2005
annee_max=2015 #A prendre en argv apres

listData=[]
shapes=[]
output=pd.DataFrame()
output["debut"]=""
output["fin"]=""
output["occup"]=""
output["citations"]=""

for file in os.listdir(path):
	if file.endswith('.shp') and file.startswith("espace_"):
		shapes.append(file)

for shape in shapes:
	listData.append(gpd.GeoDataFrame.from_file(path+'/'+shape))

data=gpd.GeoDataFrame(pd.concat(listData,ignore_index=True))

###Travail sur lot de donnees
data=data[data["nb"] >= 0] #filtre des obs négative
data=data[data.geometry.area < 5000000] #filtre des polygon sup a 5km2
data["date_obs"]=pd.to_datetime(data["date_obs"]) #convertire la date
data["annee"]=data["date_obs"].dt.year

for debut in range(annee_min,annee_max+1-4):
	for fin in range(debut+5-1,annee_max+1):
		print str(debut)+" - "+str(fin)
		data_centroid=gpd.GeoDataFrame(data[data["annee"].between(debut,fin)].copy()) #On ne prend que les centroid des data qui entre dans la periode
		data_centroid['geometry']=data['geometry'].centroid
		count=len(data_centroid.index)
		occup=sjoin(maillage[['ID','geometry']],data_centroid[['geometry']])
		occup=occup.drop_duplicates(['geometry']) #On vire les doublons
		line=pd.DataFrame({'debut':debut,'fin':fin,'occup':occup.area.sum()/1000000,'citations':count},index=[0])
		output=output.append(line,ignore_index=True)

output.to_csv(path+"data_grp.csv",index=False)
