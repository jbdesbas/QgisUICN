#Ne marche que avec du lambert93 (a fixer peutetre plus tard)
import geopandas as gpd
import pandas as pd
import os
from geopandas.tools import sjoin
import shapely
from sys import argv

if len(argv)<3: #si on a pas donner le debut et fin de ref
	years=range(2006,2016) #les 10 dernierse annes (ou periode de ref)
	print "Periode par defaut utilisee : 2006-2015"
else:
	years=range(argv[1],argv[2]+1)
	print "Periode "+str(argv[1])+" - "+str(argv[2])

path='/home/jb/Code/python/UICN/V2/'
maillage=gpd.GeoDataFrame.from_file('/home/jb/Code/python/UICN/V2/grille/2km_Picardie.shp')
lamb93={u'lon_0': 3, 'wktext': True, u'ellps': u'GRS80', u'y_0': 6600000, u'no_defs': True, u'proj': u'lcc', u'x_0': 700000, u'units': u'm', u'lat_2': 44, u'lat_1': 49, u'lat_0': 46.5}


listData=[]
shapes=[]

def occurence(col): #colone pour regrouper donnes
	mcps=gpd.GeoSeries(data.groupby(col)['geometry'].agg(shapely.ops.unary_union))
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
##Definition des periodes et mise a jour du data
if len(years)%2 == 0: #Paire
	pos=len(years)/2
else:
	pos=len(years)/2+1

periode1=years[0:pos]
periode2=years[pos:len(years)]
data.loc[data["annee"].isin(periode1),'periode']='P1' #Categorise les obs sur les deux periodes
data.loc[data["annee"].isin(periode2),'periode']='P2'
data.loc[data["annee"]<min(years),'periode']='Ant' #pour les anterierus
data.loc[data["annee"]>max(years),'periode']='Post' #Trois pour les posterieur

##### Zone d occurence #########
#Un mcp par annee
mcp_an=occurence('annee')
mcp_an.to_file(path+'/out/occurence_an.shp')
mcp_per=occurence('periode')
mcp_per.to_file(path+'/out/occurence_per.shp')
#Et un mcp pour la periode de ref
subdata=gpd.GeoDataFrame(data[data["date_obs"].dt.year.isin(years)])#selection sur la periode de ref
mcp_ref = subdata['geometry'].unary_union.convex_hull #mcp total sur la periode de ref
mcp_ref = gpd.GeoSeries(mcp_ref)
mcp_ref.to_file(path+'/out/occurence_ref.shp')

##### Zone d occupation #####
##Par annne et par periode
occup_an=occupation('annee')
occup_an.to_file(path+'/out/occup_an.shp')
occup_per=occupation('periode')
occup_per.to_file(path+'/out/occup_per.shp')
#Caclule de la zone pour la periode de ref
data_centroid_ref=data_centroid[data_centroid["date_obs"].dt.year.isin(years)]
occup_ref=sjoin(maillage[['ID','geometry']],data_centroid_ref[['geometry']])
occup_ref=jointure2.drop_duplicates(['geometry'])
occup_ref.to_file(path+'/out/occupation.shp')

##### Stats #####
ref=pd.DataFrame()
ref["annee"]=years #Pour les jointures 
##Surface des mcps par an
mcps["mcp_area"]=mcps.area/1000000
stats=pd.merge(ref,mcps[["annee","mcp_area"]], on="annee",how="left")
#mcp_ref.area.sum() #sur la periode de ref

##Surface des mailles par an et sur la periode de ref
occup_an["occup_area"]=occup_an.area/1000000
occup_grp=pd.DataFrame(occup_an.groupby('annee')["occup_area"].sum())
occup_grp["annee"]=occup_grp.index #il faudrait que j apprenne a utiliser les index sur pandas

stats=stats.merge(occup_grp[["annee","occup_area"]],on="annee",how="left")


##Regression lin
def regress(x,y):
	A = np.vstack([x, np.ones(len(x))]).T
	return np.linalg.lstsq(A, y)[0]

tend_mcp=regress(stats["annee"],stats["mcp_area"])
tend_occup=regress(stats["annee"],stats["occup_area"])

#####Rapport
rapport=pd.DataFrame()
"""Champs a prevoir
(id , nomf , noms ), occupation p1, occupation relat p1, occupation p2, occupation relat p2, var occupation, occurence p1, occurence p2, var occurence
"""


#Compilation sur pdf
"""
c = canvas.Canvas(path+"/hello.pdf")
c.drawString(100,750,"UICN")
c.drawString(150,300,"Occupation : "+str(int(round(occup_ref.area.sum()/1000000)))+" km2")
c.drawString(350,300,"Occurence : "+str(int(round(mcp_ref.area.sum()/1000000)))+" km2")
c.drawImage(path+"/testmcp.png",0,0,width=300,preserveAspectRatio=True, anchor="sw")
c.drawImage(path+"/testoccup.png",300,0,width=300,preserveAspectRatio=True, anchor="sw")
c.drawImage(path+"/carto.png",0,500,width=600,preserveAspectRatio=True, anchor="sw")
c.save()
"""
