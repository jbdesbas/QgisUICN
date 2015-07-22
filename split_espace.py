from PyQt4.QtGui import *
from PyQt4.QtCore import *
import processing
import os

canvas = iface.mapCanvas()

espaces=['espace_point','espace_polygon','espace_line','espace_commune'] #liste des espace a traiter (ajouter line commune)

path=QFileDialog.getExistingDirectory()
#path=('/home/jb/Code/python/UICN/')

#layer = QgsVectorLayer(str(filename),"Input","ogr")

for espace in espaces:

    layer = QgsVectorLayer(path+'/'+espace+'.shp',"Input","ogr")

    if not layer.isValid():
        print "Erreur input"
        continue
    else:
        field_index = layer.fieldNameIndex('id_esp')
        id_especes = layer.uniqueValues(field_index)
        i=0
        #Progres bar
        progressMessageBar = iface.messageBar().createMessage("Creation des "+espace)
        progress = QProgressBar()
        progress.setMaximum(len(id_especes))
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)

        for id_espece in id_especes:
            i+=1
            progress.setValue(i)
            #print i
            
            features2=layer.getFeatures(QgsFeatureRequest(QgsExpression('"id_esp"=%i' % (id_espece))))
            nom_s= features2.next().attribute('nom_s')#Prend le nom_s sur le premier attribut
            
            if layer.geometryType()==0: #Point
                geomType='Point'
            elif layer.geometryType()==1: #Ligne
                geomType='linestring'
            elif layer.geometryType()==2: #Polygon
                geomType='Polygon' 
                       
            layer2=QgsVectorLayer(geomType+"?crs=EPSG:2154",nom_s, "memory") #nouveau layer vide  

            layer2.startEditing()
            for field in layer.dataProvider().fields(): #on boucle pour creer chaque champs a partir du layer en input
                layer2.addAttribute(field)
            layer2.commitChanges()
            #Il faut un commit apres ajout des fields
            layer2.startEditing()

            for f in features2:
                layer2.addFeature(f)
            
            layer2.commitChanges()
            
            #Ecriture des layer sur le disque
            if not os.path.exists(path+'/'+nom_s):
                os.makedirs(path+'/'+nom_s)
            QgsVectorFileWriter.writeAsVectorFormat(layer2,'%s/%s/%s_%s.shp' % (path,nom_s,geomType,nom_s),u'System',layer2.dataProvider().crs())
            print geomType
            
