#import sys
import geopandas as gpd
import os
import shutil
import sys

lamb93={u'lon_0': 3, 'wktext': True, u'ellps': u'GRS80', u'y_0': 6600000, u'no_defs': True, u'proj': u'lcc', u'x_0': 700000, u'units': u'm', u'lat_2': 44, u'lat_1': 49, u'lat_0': 46.5}


if len(sys.argv) < 2:
	raise ValueError("usage = split_espace2.py path")

path=sys.argv[1]

#path='/home/jb/Documents/ListesRouges/Evaluation/Amphibiens-Reptiles/donnees_amphib/'

listData=[]
shapes=[]

for file in os.listdir(path):
	if file.endswith('.shp') and file.startswith("espace_"):
		shapes.append(file)

for shape in shapes:
	listData.append(gpd.GeoDataFrame.from_file(path+'/'+shape))

data=gpd.GeoDataFrame(gpd.pd.concat(listData,ignore_index=True))
data.crs=lamb93
listSp=set(data.nom_s.values)

for sp in listSp:
	if sp is None:
		continue
	
	sp2=sp.replace('/','-') #Nettoyer les noms qui contiennent un /	
	
	if os.path.exists(path+sp2):
		shutil.rmtree(path+sp2)
	
	os.makedirs(path+sp2)
	dataSp=data[data.nom_s==sp]
	pts=dataSp[dataSp.geometry.geom_type.isin(['Point','MultiPoint'])]
	polyg=dataSp[dataSp.geometry.geom_type.isin(['Polygon','MultiPolygon'])]
	line=dataSp[dataSp.geometry.geom_type.isin(['LineString','MultiLineString'])]
	if len(pts)>0:
		pts.to_file(path+sp2+'/point.shp')	
	
	if len(polyg)>0:
		polyg.to_file(path+sp2+'/polygon.shp')
	
	if len(line)>0:
		line.to_file(path+sp2+'/line.shp')

