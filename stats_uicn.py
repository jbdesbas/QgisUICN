import geopandas as gpd
import pandas as pd
import os
from geopandas.tools import sjoin
import shapely

path='/home/jb/Code/python/UICN/V2'

maillage=gpd.GeoDataFrame.from_file(path+'/grille/L93_1x1.shp')
listData=[]
shapes=[]
years=range(2006,2016) #les 10 dernierse annes (ou periode de ref)

for file in os.listdir(path):
	if file.endswith('.shp'):
		shapes.append(file)

for shape in shapes:
	listData.append(gpd.GeoDataFrame.from_file(path+'/'+shape))

data=gpd.GeoDataFrame(pd.concat(listData,ignore_index=True))

data=data[data["nb"] >= 0] #filtre des obs négative
data=data[data.geometry.area < 5000000] #filtre des polygon sup a 5km2
data["date_obs"]=pd.to_datetime(data["date_obs"]) #convertire la date
data["annee"]=data["date_obs"].dt.year

##### Zone d occurence #########
#Un mcp par annee
mcps=gpd.GeoSeries(data.groupby('annee')['geometry'].agg(shapely.ops.unary_union)) #une serie avec lunion des geom de la meme anne
mcps=mcps.convex_hull #on prend le mcp de chaque geom
mcps=gpd.GeoDataFrame(mcps,columns=['geometry'])
mcps.reset_index(level=0, inplace=True) #pour sortir lanne de l'index
mcps[mcps.geom_type == 'Polygon'].to_file(path+'/out/occurence_an.shp') #on ignore les mcp non polygon
#Et un mcp pour la periode de ref
subdata=gpd.GeoDataFrame(data[data["date_obs"].dt.year.isin(years)])#selection sur la periode de ref
mcp_ref = subdata['geometry'].unary_union.convex_hull #mcp total sur la periode de ref
mcp_ref = gpd.GeoSeries(mcp_ref)
mcp_ref.to_file(path+'/out/occurence_ref.shp')

##### Zone d occupation #####
data_centroid=gpd.GeoDataFrame(data.copy()) #On ne prend que les centroid des polygone (seuil bas)
data_centroid['geometry']=data['geometry'].centroid
occup_an=sjoin(maillage[['CODE_10KM','geometry']],data_centroid[['annee','geometry']])
occup_an=occup_an.drop_duplicates(['geometry','annee']) #On vire les doublons
occup_an.to_file(path+'/out/occup_an.shp')
#Caclule de la zone pour la periode de ref
data_centroid_ref=data_centroid[data_centroid["date_obs"].dt.year.isin(years)]
occup_ref=sjoin(maillage[['CODE_10KM','geometry']],data_centroid_ref[['geometry']])
occup_ref=jointure2.drop_duplicates(['geometry'])
occup_ref.to_file(path+'/out/occupation.shp')
