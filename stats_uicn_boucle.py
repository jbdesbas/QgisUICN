#Ne marche que avec du lambert93 (a fixer peutetre plus tard)
#A corriger : bug si manque occurence P1 ou P2 (utiliser un merge pour avoir NaN; comme pour occupation)
#stats_uicn.py path debut fin
import geopandas as gpd
import pandas as pd
import os
from geopandas.tools import sjoin
import shapely
from sys import argv
import numpy as np

if len(argv)<4: #si on a pas donner le debut et fin de ref
	years=range(2006,2015+1) #les 10 dernierse annes (ou periode de ref)
	print "Periode par defaut utilisee : 2006-2015"
else:
	years=range(int(argv[2]),int(argv[3])+1)
	print "Periode "+str(argv[2])+" - "+str(argv[3])


#pathData=argv[1]
pathData="/home/jb/Documents/ListesRouges/Evaluation/Coccinelles/donnees/"
maillage=gpd.GeoDataFrame.from_file('/home/jb/Documents/ListesRouges/Evaluation/grilles/2km_Picardie.shp')
lamb93={u'lon_0': 3, 'wktext': True, u'ellps': u'GRS80', u'y_0': 6600000, u'no_defs': True, u'proj': u'lcc', u'x_0': 700000, u'units': u'm', u'lat_2': 44, u'lat_1': 49, u'lat_0': 46.5}

def traitement_espece(path):
	def occurence(col): #colone pour regrouper donnes
		mcps=gpd.GeoSeries(data.groupby(col)['geometry'].agg(shapely.ops.unary_union)) #Gerer les geometries invalides (lignes surtout)
		mcps=mcps.convex_hull #on prend le mcp de chaque geom
		mcps=gpd.GeoDataFrame(mcps,columns=['geometry'])
		mcps.crs=lamb93
		mcps.reset_index(level=0, inplace=True) #pour sortir lannee de l'index
		mcps=mcps[mcps.geom_type == 'Polygon'] #ignorer les mcp non polygon
		return mcps
	
	def occupation(col):  #colone pour regrouper donnes
		data_centroid=gpd.GeoDataFrame(data[data[col].notnull()].copy()) #On ne prend que les centroid des polygone (seuil bas)
		data_centroid['geometry']=data['geometry'].centroid
		occup=sjoin(maillage[['ID','geometry']],data_centroid[[col,'geometry']])
		occup=occup.drop_duplicates(['geometry',col]) #On vire les doublons
		return occup
	
	if not os.path.exists(path+'out'):
		os.makedirs(path+'out')
	
	listData=[]
	shapes=[]
	
	for file in os.listdir(path):
		if file.endswith('.shp'):
			shapes.append(file)
	
	for shape in shapes:
		listData.append(gpd.GeoDataFrame.from_file(path+'/'+shape))
	
	if len(listData)==0:
		print("Dossier vide")
		return
	
	data=gpd.GeoDataFrame(pd.concat(listData,ignore_index=True))
	if len(data)==0:  #si le fichier est vide
		print("Shape vide")		
		return
	
	###Travail sur lot de donnees
	data=data[data["nb"] >= 0] #filtre des obs negative
	data=data[data.geometry.is_valid] #Filtre des geom invalides
	data=data[data.geometry.area < 5000000] #filtre des polygon sup a 5km2
	data["date_obs"]=pd.to_datetime(data["date_obs"]) #convertire la date
	data["annee"]=data["date_obs"].dt.year
	
	if len(data)==0:  #si le fichier est vide apres ca
		print("Shape vide apres filtrage")		
		return
	
	##### Zone d occurence #########
	
	#Et un mcp pour la periode de ref
	subdata=gpd.GeoDataFrame(data[data["date_obs"].dt.year.isin(years)])#selection sur la periode de ref
	if len(subdata)!=0:
		mcp_ref = subdata['geometry'].unary_union.convex_hull #mcp total sur la periode de ref
		mcp_ref = gpd.GeoSeries(mcp_ref)
		mcp_ref.to_file(path+'/out/occurence_ref.shp')
	else:
		mcp_ref=0
	##### Zone d occupation #####
	
	#Caclule de la zone pour la periode de ref
	data_centroid=gpd.GeoDataFrame(data.copy())
	data_centroid['geometry']=data['geometry'].centroid
	data_centroid_ref=data_centroid[data_centroid["date_obs"].dt.year.isin(years)]
	if len(data_centroid_ref)!=0:
		occup_ref=sjoin(maillage[['ID','geometry']],data_centroid_ref[['geometry']])
		occup_ref=occup_ref.drop_duplicates(['geometry'])
		occup_ref.to_file(path+'/out/occupation.shp')
	else:
		occup_ref=0
	
	#####Rapport
	rapport=gpd.pd.DataFrame() #C'est pas tres propre un dataframe a une ligne, mais c est pour garder l ordre des colonnes
	rapport["id_esp"]=[data.id_esp.values[0]]
	rapport["nom_s"]=[data.nom_s.values[0]]
	rapport["citations"]=[len(data[data["annee"].between(min(years),max(years))].index)]
	rapport["derniere_obs"]=[max(data["annee"])]
	if mcp_ref is not 0:
		rapport["occurence"]=mcp_ref.area.values/1000000
	else:
		rapport["occurence"]=[0]

	if occup_ref is not 0:
		rapport["occupation"]=[occup_ref.area.sum()/1000000]
	else:
		rapport["occupation"]=[0]
	
	return rapport


listdir=os.listdir(pathData)
rapport_list=[]
for el in listdir:
	if os.path.isdir(pathData+el): #si c'est un dossier (espece)
		rapport_esp=traitement_espece(pathData+el+'/')
		rapport_list.append(rapport_esp)

final=gpd.pd.concat(rapport_list, ignore_index=True)
final.to_csv(pathData+'rapport_glob.csv',index=False,decimal=",")
