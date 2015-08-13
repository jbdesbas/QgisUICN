#Regrouper dans un meme csv les csv possible, probable, certain et le csv total (sans doublons), indiquer le status nicheur de chaque citation

import csv
import time
from datetime import datetime

writecsv=False #Ecrire toute les donnees dans un seul csv en sortie

csvFiles={}

data_out=[]
data_clean=[]
citations_nicheurs=set()
especes_temp=set()
especes=[]
path='/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Oiseaux/donnes_pour_liste'
csvFiles["possible"]=path+'/'+'clicnat_selection_18834_6vUDEx.csv'
csvFiles["probable"]=path+'/'+'clicnat_selection_18835_Iy2wZT.csv'
csvFiles["certain"]=path+'/'+'clicnat_selection_18836_xqyoP8.csv'
csvFileGlobal=path+'/'+'clicnat_selection_18833_lONOMv.csv'

csv.register_dialect('clicnat',delimiter=';', quotechar='"')
i=0
for d in csvFiles: #pour chaque csv
	csvFile=open(csvFiles[d],'rb')
	reader=csv.DictReader(csvFile, dialect=csv.get_dialect('clicnat'))
	for row in reader:
		#print i
		data_out.append(row)
		row["Status"]=d
		citations_nicheurs.add(row["id_citation"])
		i+=1

i=0

del reader
del row
del csvFile
csvFile=open(csvFileGlobal,'rb')
reader=csv.DictReader(csvFile, dialect=csv.get_dialect('clicnat'))
for row in reader:
	if row["id_citation"] not in citations_nicheurs:
		row["Status"]="visiteur"
		data_out.append(row)
		#print i
		i+=1

i=0

#Nettoyage des donnees et listes pour les stats (utiliser filter() ? )
for e in data_out:
	if int(e["precision_date"])<15:
		data_clean.append(e)
		especes_temp.add((e["id_espece"], e["nom_s"], e["nom_f"]))

dico_status={'possible' : 0, 'probable' : 0, 'certain' : 0, 'visiteur' : 0}

for e in especes_temp: #On fait une liste de dico pour les espece (plus elegant)
	especes.append({'id_espece' : e[0], 'nom_s' : e[1], 'nom_f' : e[2], 'stats': {'citations' : dico_status.copy(), 'last_obs' : dico_status.copy()} })

del data_out

del row
del csvFile

if writecsv==True:
	fields=reader.fieldnames
	fields.append("Status")
	csvOut=open(path+'/output.csv','wb')
	writer=csv.DictWriter(csvOut,fields,dialect=csv.get_dialect('clicnat'))
	writer.writeheader()
	for row in data_clean:
		writer.writerow(row)
		#print i
		i+=1
	
	del writer
	del csvOut
	del fields

#Stats sur les donnees
for row in data_clean:
	idx = especes.index(filter(lambda func: func['id_espece'] == row["id_espece"], especes)[0]) #On recupere l'index du dico de l'espece
	especes[idx]["stats"]["citations"][row["Status"]]+=1
	
	last_obs=especes[idx]["stats"]["last_obs"][row["Status"]]
	annee=datetime.strptime(row["date_observation"],'%Y-%m-%d').year
	especes[idx]["stats"]["last_obs"][row["Status"]]=max(last_obs,annee)
	
#Ecrire les especes dans un csv
csvOut=open(path+'/bilan_especes.csv','wb')
fields=["id_espece","nom_s","nom_f","cit_poss","lst_poss","cit_prob","lst_prob","cit_cert","lst_cert","cit_vis","lst_vis"]
writer=csv.DictWriter(csvOut,fields,dialect=csv.get_dialect('clicnat'))
writer.writeheader()
for espece in especes:
	row={}
	row["id_espece"]=espece["id_espece"]
	row["nom_s"]=espece["nom_s"]
	row["nom_f"]=espece["nom_f"]
	row["cit_poss"]=espece["stats"]["citations"]["possible"]
	row["cit_prob"]=espece["stats"]["citations"]["probable"]
	row["cit_cert"]=espece["stats"]["citations"]["certain"]
	row["cit_vis"]=espece["stats"]["citations"]["visiteur"]
	row["lst_poss"]=espece["stats"]["last_obs"]["possible"]
	row["lst_prob"]=espece["stats"]["last_obs"]["probable"]
	row["lst_cert"]=espece["stats"]["last_obs"]["certain"]
	row["lst_vis"]=espece["stats"]["last_obs"]["visiteur"]
	writer.writerow(row)
