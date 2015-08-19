#Trace des courbes de phenologie
#Necessite donnees csv avec une colone supplementaire contenant le Status nicheur (traitement_csv_nicheurs.py)

import pandas
import numpy
from datetime import datetime
import matplotlib.pyplot as plt
import unicodedata


status=(('visiteur','blue'),('possible','green'),('probable','orange'),('certain','red'))

path='/home/users/jbdesbas/Documents/ListesRouges/Evaluation/Oiseaux/donnes_pour_liste'

data=pandas.read_csv(path+'/output.csv', quotechar='"',sep=';')

colweek= data.apply( lambda row:datetime.strptime(row["date_observation"],'%Y-%m-%d').isocalendar()[1],axis = 1 )
data["semaine"]=colweek

pivot = pandas.pivot_table(data, index=['nom_f', 'Status'], columns='semaine',values='id_citation', aggfunc=numpy.count_nonzero)

for id_esp in data["id_espece"].unique():
	for s,color in status:
		sub=data[(data.id_espece==id_esp) & (data.Status==s)]
		if sub.size>0:
			data_plot=sub.groupby("semaine").count()["id_citation"]
			data_plot.plot(linestyle='-', label=s, color=color)
		
	plt.legend(loc='upper left')
	titre=unicode(data[(data.id_espece==id_esp)].nom_f.values[0],'utf-8')
	titre=unicodedata.normalize('NFD', titre).encode('ascii', 'ignore') #pour gerer les accents des noms
	plt.title(titre)
	plt.xticks(range(1,53,4))
	plt.grid(True)
	plt.savefig(path+'/pheno/'+str(id_esp)+'.png')
	plt.clf()
	
