## Arguement : chemin pour contenant les shp (point, polygon, line...), nb citation mini, chemin vers la grille lambert 93
#ATTENTION A BIEN FILTRER LES DONNES AVANT
import geopandas as gpd
from geopandas.tools import sjoin
import os
from sys import argv
from math import floor, ceil

if len(argv) < 4:
	raise NameError('Erreur arguments')
#pathData='/home/jb/Documents/Rarete/V2/'
#pathGrille='/home/jb/Documents/ListesRouges/Evaluation/grilles/grille_5km_l93.shp'
#citation_mini=1

pathData=argv[1]
pathGrille=argv[2]
citation_mini=int(argv[3])

lamb93={u'lon_0': 3, 'wktext': True, u'ellps': u'GRS80', u'y_0': 6600000, u'no_defs': True, u'proj': u'lcc', u'x_0': 700000, u'units': u'm', u'lat_2': 44, u'lat_1': 49, u'lat_0': 46.5}

seuil_orig={'TC':[0,36.5],'C':[36.5,68.5],'AC':[68.5,84.5],'PC':[84.5,92.5],'AR':[92.5,96.5],'R':[96.5,98.5],'TR':[98.5,99.5],'EX':[99.5,100]}
seuil_ajust={'TC':[0,0],'C':[0,0],'AC':[0,0],'PC':[0,0],'AR':[0,0],'R':[0,0],'TR':[0,0],'EX':[0,0]}

seuil_abs={'TC':[0,0],'C':[0,0],'AC':[0,0],'PC':[0,0],'AR':[0,0],'R':[0,0],'TR':[0,0],'EX':[0,0]} #Attention, [seuilminiOrig,seuilminiAjust]
###Chargement des fichiers shp en entree
grille=gpd.GeoDataFrame.from_file(pathGrille)
nbMaillesTotal=len(grille)
listData=[]
shapes=[]
rapport_list=[]

for file in os.listdir(pathData):
	if file.endswith('.shp') and file.startswith("espace_"):
		shapes.append(file)

for shape in shapes:
	listData.append(gpd.GeoDataFrame.from_file(pathData+'/'+shape))

data=gpd.GeoDataFrame(gpd.pd.concat(listData,ignore_index=True))
data.geometry=data.geometry.centroid
data.crs=lamb93
listSp=set(data.nom_s.values)

#Compter le nombre de mailles prospectees
occup_total=sjoin(grille[['ID','geometry']],data[['geometry']])
occup_total_agreg=occup_total.groupby(['geometry']).count() #ici, geometry est l index
occup_total_agreg=gpd.GeoDataFrame(occup_total_agreg)
occup_total_agreg.geometry=occup_total_agreg.index.values.copy() #Copy de l'index dans la colonne geometry
occup_total_agreg.reset_index(drop=True, inplace=True) #On remplace par un index normal
occup_total_agreg["nb_cit"]=occup_total_agreg["index_right"].values.copy()
del occup_total_agreg["ID"]
del occup_total_agreg["index_right"]
nbMaillesProsp=len(occup_total_agreg[occup_total_agreg["nb_cit"]>=citation_mini])
P=100*float((nbMaillesTotal-nbMaillesProsp))/nbMaillesTotal
#Ajuster les seuils des indicdes de rarete
for indice,seuil in seuil_orig.items():
	seuil_ajust[indice][0]=seuil[0]+P-(seuil[0]*P/100)
	seuil_ajust[indice][1]=seuil[1]+P-(seuil[1]*P/100)

def rarete_espece(datasp,maille,seuil):
	if len(datasp)<1: #si 0 donnees
		return gpd.pd.DataFrame()
	
	try :
		occupation=sjoin(grille[['ID','geometry']],datasp[['geometry']])
	except:
		print("erreur jointure (pas en picardie ?")
		return gpd.pd.DataFrame()
	
	occupation=occupation.drop_duplicates(['geometry']) #On vire les doublons
	nb_mailles=len(occupation)
	rr=(1-(float(len(occupation))/nbMaillesTotal))*100
	
	for indice,seuil in seuil_orig.items():#Pour trouver quel indice
		if rr >= seuil[0] and rr < seuil[1]:
			indice_base=indice
			break
		else:
			indice_base='TTC' #Si on depasse le 100pour100 (citations mini > 1)
	
	for indice,seuil in seuil_ajust.items():#Pour trouver quel indice
		if rr >= seuil[0] and rr < seuil[1]:
			indice_ajust=indice
			break
		else:
			indice_ajust='TTC' #Si on depasse le 100pour100 (citations mini > 1)
	
	rapport=gpd.pd.DataFrame()
	rapport["id_esp"]=[datasp.id_esp.values[0]]
	rapport["nom_s"]=[datasp.nom_s.values[0]]
	rapport["nb_mailles"]=[nb_mailles]
	rapport["rr"]=[rr]
	rapport["indiceBrute"]=indice_base
	rapport["indicePondere"]=indice_ajust
	return rapport

for e in data.id_esp.unique():
	print(e)
	datasp=data[data["id_esp"]==e]#Selection de l'espece dans le df
	result=rarete_espece(datasp,grille,citation_mini)
	if len(result)==1:
		rapport_list.append(result)

final=gpd.pd.concat(rapport_list, ignore_index=True)
final.to_csv(pathData+'rarete.csv',index=False,decimal=",", encoding='utf-8')

#Calcule des seuils absolus
rapport_seuil=gpd.pd.DataFrame()
rap_indice=[]
rap_mini_orig=[]
rap_mini_ajust=[]

for indice,seuil in seuil_orig.items():
	rap_indice.append(indice)
	rap_mini_orig.append(int(ceil((100-seuil[1])/100*nbMaillesTotal)))

for indice,seuil in seuil_ajust.items():
	rap_mini_ajust.append(int(ceil((100-seuil[1])/100*nbMaillesTotal)))

rapport_seuil["indice"]=rap_indice
rapport_seuil["mini_orig"]=rap_mini_orig
rapport_seuil["mini_ajust"]=rap_mini_ajust

rapport_seuil.to_csv(pathData+'seuil.csv',index=False,decimal=",", encoding='utf-8')

print('Mailles prospectes : '+str(nbMaillesProsp)+' / '+str(nbMaillesTotal))
