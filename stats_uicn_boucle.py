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
	print("Periode par defaut utilisee : 2006-2015")
else:
	years=range(int(argv[2]),int(argv[3])+1)
	print("Periode "+str(argv[2])+" - "+str(argv[3]))

#On coupe en deux la periode
if len(years)%2 == 0: #Paire
	pos=len(years)/2
else:
	pos=len(years)/2+1

periode1=years[0:pos]
periode2=years[pos:len(years)]

pathData=argv[1]
#pathData="/home/jb/Documents/ListesRouges/Evaluation/Amphibiens-Reptiles/donnees_amphib/"
maillage=gpd.GeoDataFrame.from_file('/home/jb/Documents/ListesRouges/Evaluation/grilles/2km_Picardie.shp')
lamb93={u'lon_0': 3, 'wktext': True, u'ellps': u'GRS80', u'y_0': 6600000, u'no_defs': True, u'proj': u'lcc', u'x_0': 700000, u'units': u'm', u'lat_2': 44, u'lat_1': 49, u'lat_0': 46.5}

def occurence(dataframe): #colone pour regrouper donnes
	dataframe=dataframe[dataframe.geometry.is_valid] #Gerer les geometries invalides (lignes surtout)
	mcps=dataframe.geometry.unary_union.convex_hull #on prend le mcp de la geom
	mcps=gpd.GeoSeries(mcps)
	mcps.crs=lamb93
	#mcps.reset_index(level=0, inplace=True) #pour sortir lannee de l'index
	mcps=mcps[mcps.geom_type == 'Polygon'] #ignorer les mcp non polygon optionel ?
	return mcps

def occupation(dataframe):  #colone pour regrouper donnes
	data_centroid=gpd.GeoDataFrame(dataframe.copy()) #On ne prend que les centroid des polygone (seuil bas)
	data_centroid['geometry']=dataframe['geometry'].centroid
	try : 
		occup=sjoin(maillage[['ID','geometry']],data_centroid[['geometry']])
		occup=occup.drop_duplicates(['geometry']) #On vire les doublons
	except ValueError:
		print("erreur sjoin")
		occup=gpd.GeoDataFrame()
		occup["geometry"]=[""]
	
	return occup

def traitement_espece(path): #Sera execute pour chaque sp, retourne la ligne du rapport final concernant l espece
	
	if not os.path.exists(path+'out'):
		os.makedirs(path+'out')
	
	listData=[]
	shapes=[]
	rapport=gpd.pd.DataFrame() #C'est pas tres propre un dataframe a une ligne, mais c est pour garder l ordre des colonnes
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
	#Per 1
	condition=data["date_obs"].dt.year.isin(periode1).tolist() and data.geometry.is_valid.tolist() #Array de boolean valide ET dans la periode
	subdata=gpd.GeoDataFrame(data[condition])
	if len(subdata) > 2: #pas de tableau vide sinon ca fait planter... Et un mcp sur moins de 2 donnees c est debile
		occurP1=occurence(subdata)
		occurP1.to_file(path+'/out/occurence_P1.shp')
		rapport["occurP1"]=[occurP1.area.sum()/1000000]
	else:
		rapport["occurP1"]=[0]
	#Per 2
	condition=np.logical_and(data["date_obs"].dt.year.isin(periode2), data.geometry.is_valid) #Array de boolean valide ET dans la periode
	subdata=gpd.GeoDataFrame(data[condition])
	if len(subdata) > 2: #pas de tableau vide sinon ca fait planter... Et un mcp sur moins de 2 donnees c est debile
		occurP2=occurence(subdata)
		occurP2.to_file(path+'/out/occurence_P2.shp')
		rapport["occurP2"]=[occurP2.area.sum()/1000000]
	else:
		rapport["occurP2"]=[0]
	#Periode total
	condition=np.logical_and(data["date_obs"].dt.year.isin(years), data.geometry.is_valid) #Array de boolean valide ET dans la periode
	subdata=gpd.GeoDataFrame(data[condition])
	if len(subdata) > 2: #pas de tableau vide sinon ca fait planter... Et un mcp sur moins de 2 donnees c est debile
		occur=occurence(subdata)
		occur.to_file(path+'/out/occurence.shp')
		rapport["occur"]=[occur.area.sum()/1000000]
	else:
		rapport["occur"]=[0]

	##### Zone d occupation #####
	#Per 1
	condition=np.logical_and(data["date_obs"].dt.year.isin(periode1),data.geometry.is_valid)#Array de boolean valide ET dans la periode
	subdata=gpd.GeoDataFrame(data[condition])
	if len(subdata) > 0: #pas de tableau vide sinon ca fait planter...
		occupP1=occupation(subdata)
		try:
			occupP1.to_file(path+'/out/occupation_P1.shp')
		except ValueError:
			print("shape vide ?")
		rapport["occupationP1"]=[occupP1.area.sum()/1000000]
	else:
		rapport["occupationP1"]=[0]
	
	#Per 2
	condition=np.logical_and(data["date_obs"].dt.year.isin(periode2),data.geometry.is_valid)#Array de boolean valide ET dans la periode
	subdata=gpd.GeoDataFrame(data[condition])
	if len(subdata) > 0: #pas de tableau vide sinon ca fait planter...
		occupP2=occupation(subdata)
		try:
			occupP2.to_file(path+'/out/occupation_P2.shp')
		except ValueError:
			print("shape vide ?")
		rapport["occupationP2"]=[occupP2.area.sum()/1000000]
	else:
		rapport["occupationP2"]=[0]
	#Periode total
	condition=np.logical_and(data["date_obs"].dt.year.isin(years),data.geometry.is_valid)#Array de boolean valide ET dans la periode
	subdata=gpd.GeoDataFrame(data[condition])
	if len(subdata) > 0: #pas de tableau vide sinon ca fait planter...
		occup=occupation(subdata)
		try:
			occup.to_file(path+'/out/occupation.shp')
		except ValueError:
			print("shape vide ?")
		rapport["occupation"]=[occup.area.sum()/1000000]
	else:
		rapport["occupation"]=[0]

	#####Rapport

	rapport["id_esp"]=[data.id_esp.values[0]]
	rapport["nom_s"]=[data.nom_s.values[0]]
	rapport["citations"]=[len(data[data["annee"].between(min(years),max(years))].index)]
	rapport["derniere_obs"]=[max(data["annee"])]

	return rapport


listdir=os.listdir(pathData)
rapport_list=[]
for el in listdir:
	if os.path.isdir(pathData+el): #si c'est un dossier (espece)
		print(el)
		rapport_esp=traitement_espece(pathData+el+'/')
		rapport_list.append(rapport_esp)

final=gpd.pd.concat(rapport_list, ignore_index=True)
print(final)
final.to_csv(pathData+'rapport_glob.csv',index=False,decimal=",")

##Traitement pour le groupe :
listData=[]
shapes=[]
for file in os.listdir(pathData):
	if file.endswith('.shp') and file.startswith('espace'): #Tous les shp present dans le dossier 
		shapes.append(file)

for shape in shapes:
	listData.append(gpd.GeoDataFrame.from_file(pathData+shape))
		
data=gpd.GeoDataFrame(pd.concat(listData,ignore_index=True))

###Travail sur lot de donnees
data=data[data["nb"] >= 0] #filtre des obs negative
data=data[data.geometry.is_valid] #Filtre des geom invalides
data=data[data.geometry.area < 5000000] #filtre des polygon sup a 5km2
data["date_obs"]=pd.to_datetime(data["date_obs"]) #convertire la date
data["annee"]=data["date_obs"].dt.year

occupation_glob=occupation(data)
occupation_glob.to_file(pathData+'occupation.shp')
occupation_glob_P1=occupation(data[data["date_obs"].dt.year.isin(periode1)]).to_file(pathData+'occupationP1.shp')
occupation_glob_P2=occupation(data[data["date_obs"].dt.year.isin(periode2)]).to_file(pathData+'occupationP2.shp')

occur_glob=occurence(data)
occur_glob.to_file(pathData+'occurence.shp')

#Faire occupation P1, P2 et commune aux deux periodes
