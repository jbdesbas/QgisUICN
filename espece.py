from PyQt4.QtGui import *
from PyQt4.QtCore import *
import processing
import os
import shutil
from qgis.analysis import *

canvas = iface.mapCanvas()
years_colors=(
    (2004,'#d7191c'),
    (2005,'#e44f35'),
    (2006,'#f2854e'),
    (2007,'#fdb569'),
    (2008,'#fdd28c'),
    (2009,'#fef0ae'),
    (2010,'#eef8b0'),
    (2011,'#ceea91'),
    (2012,'#aedc71'),
    (2013,'#7fc65e'),
    (2014,'#4cae4f'),
    (2015,'#1a9641'),
)

path=QFileDialog.getExistingDirectory(directory='/home/users/jbdesbas/Documents/Listes rouges/Evaluation/')
if path=='':
    raise ValueError('Pas de repertoire')
#path='/home/users/jbdesbas/Documents/Listes rouges/Evaluation/Odonates/Coenagrion mercuriale  (CHARPENTIER, 1840)'
grille=QgsVectorLayer('/home/users/jbdesbas/Documents/Listes rouges/Evaluation/grilles/2km_Picardie.shp','grille','ogr')
if os.path.isfile(path+'/data.csv'):
    os.remove(path+'/data.csv')
output_file = open(path+'/data.csv', 'w')

listdir=os.listdir(path)
shapes=[]
for file in listdir:
    if file.endswith('.shp') and file!=('MCP.shp') and file!=('MCPfinal.shp')  and file!=('Mailles.shp'):
        shapes.append(file)

for shape in shapes: #Pour chaque fichier shape retenu
    layer=QgsVectorLayer(path+'/'+shape,"Temp","ogr")
 
    if layer.geometryType()==0: #Point
        geomType='Point'
    elif layer.geometryType()==1: #Ligne
        geomType='linestring'
    elif layer.geometryType()==2: #Polygon
        geomType='Polygon' 
    layer.setDataSource(path+'/'+shape,geomType,"ogr") #Changer le nom du layer
    
    #ajouter une colonne annee (pour le subset)
    field_index=layer.fieldNameIndex('annee')
    if field_index==-1: #La colone existe pas deja
        layer.startEditing()
        layer.dataProvider().addAttributes([QgsField('annee', QVariant.Int)])
        layer.updateFields()
        layer.commitChanges()
    field_index=layer.fieldNameIndex('annee') 
    layer.startEditing()
    for f in layer.getFeatures():
        value=QgsExpression('year("date_obs")').evaluate(f)
        layer.changeAttributeValue(f.id(),field_index,value)
    layer.commitChanges()
    
    QgsMapLayerRegistry.instance().addMapLayers([layer]) #ajouter la couche
 
    #Symbologie des donnes espece
    symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
    renderer=QgsRuleBasedRendererV2(symbol)
    root_rule = renderer.rootRule()
    rPass=10
    if geomType=='Point': #Carre blanc pour les prospe negative
        rule = root_rule.children()[0].clone()
        rule.setLabel('prosp neg')
        rule.setFilterExpression('"nb"=-1')
        rule.symbol().symbolLayer(0).setName("triangle")
        rule.symbol().setColor(QColor('white'))
        rule.symbol().symbolLayer(0).setRenderingPass(rPass)
        root_rule.appendChild(rule)
    rPass=15
    rule = root_rule.children()[0].clone() #Donnes historiques
    rule.setLabel('<2004')
    rule.setFilterExpression('year("date_obs")< 2004')
    rule.symbol().setColor(QColor('#5f5e5e'))
    rule.symbol().symbolLayer(0).setRenderingPass(rPass)
    root_rule.appendChild(rule)
    
    for year,color in years_colors: #2004 a 2015
        rPass+=1 #Les donnes les plus recentes dessus
        rule = root_rule.children()[0].clone()
        rule.setLabel(str(year))
        rule.setFilterExpression('year("date_obs")=%i AND "nb">=0'%(year))
        rule.symbol().setColor(QColor(color))
        rule.symbol().symbolLayer(0).setRenderingPass(rPass)
        root_rule.appendChild(rule)
        
    root_rule.removeChildAt(0)
    layer.setRendererV2(renderer) # Appliquer la symbologie

    #MCP
    pathMCP=path+'/MCP'
    for year,NULL in years_colors:
        if not os.path.exists(pathMCP+'/'+str(year)):
            os.makedirs(pathMCP+'/'+str(year))
        layer.setSubsetString('"annee"=%i and "nb">=0'%(year))
        processing.runalg("qgis:convexhull",layer,'',0,pathMCP+"/"+str(year)+"/"+geomType+".shp")#il aurait ete possible dutiliser un outil integre 
    layer.setSubsetString('')
    i=0
    #Presence par mailles
    print 'Presence par maille'
    pathMaille=path+'/Maille'
    for year,NULL in years_colors:
        id_mailles=[] #pour stocker les mailles qui contiennent un point
        for fl in layer.getFeatures(QgsFeatureRequest(QgsExpression('year("date_obs")=%i and "nb">=0'%(year)))):
            x=fl.geometry().centroid().asPoint().x()
            y=fl.geometry().centroid().asPoint().y()
            grille_feat=grille.getFeatures(QgsFeatureRequest(QgsExpression('x_min($geometry)<'+str(x)+' AND x_max($geometry)>'+str(x)+' AND y_min($geometry)<'+str(y)+' AND y_max($geometry)>'+str(y) )))
            #id_maille= grille_feat.next().id() #normalement un seul
            for e in grille_feat:
                id_maille=e.id()
            id_mailles.append(id_maille) #ajout a la liste des id
            print id_maille
        #Creer un shape pour cette annee
        grille_feat2=grille.getFeatures(QgsFeatureRequest().setFilterFids(id_mailles))
        if not os.path.exists(pathMaille+'/'+str(year)):
            os.makedirs(pathMaille+'/'+str(year))
        QgsVectorFileWriter.writeAsVectorFormat(grille,pathMaille+"/"+str(year)+"/"+geomType+".shp",u'System',grille.dataProvider().crs())
        grille2=QgsVectorLayer(pathMaille+"/"+str(year)+"/"+geomType+".shp",geomType+str(year),"ogr")
        grille2.startEditing()
        for f in grille2.getFeatures():
            grille2.deleteFeature(f.id())
        grille2.commitChanges()
        grille2.startEditing()
        for f in grille_feat2: #toute les features qui contiennent un point
            grille2.addFeature(f)
        grille2.commitChanges()
           
#Traitement des MCP
shps=[]
first=True
for annee in os.listdir(pathMCP): #pour chaque dossier annee
    dir_annee=pathMCP+"/"+annee
    if(os.path.isdir(dir_annee)): #S assurer que c est bien un dossier
        annee=int(annee)
        for file in os.listdir(dir_annee):
            file=dir_annee+"/"+file
            if file.endswith('.shp'): #Ne prendre que les shape
                layer=QgsVectorLayer(file,'toto',"ogr")
                print file
                layer.startEditing()
                layer.dataProvider().addAttributes([QgsField('annee', QVariant.Int)]) #ajouter un champs annee
                layer.updateFields()
                field_index=layer.fieldNameIndex('annee')
                for f in layer.getFeatures():
                    layer.changeAttributeValue(f.id(),field_index,annee) #inserer dans le champs annee (pris depuis le nom du dossier) j aurai du le faire dans l etape anvant
                layer.commitChanges()
                layer=QgsVectorLayer(file,'toto',"ogr") #Faut recharger le layer sinon ca marche pas je sais pas pquoi et ca m enerve

                if first: #Cloner le layer precend et le vider a la premiere passe
                    test='okokokok'
                    QgsVectorFileWriter.writeAsVectorFormat(layer,path+"/MCP/MCP.shp",u'System',layer.dataProvider().crs())
                    layerMCP=QgsVectorLayer(path+"/MCP/MCP.shp","MCP","ogr")
                    layerMCP.startEditing()
                    for f in layerMCP.getFeatures():
                        layerMCP.deleteFeature(f.id())
                    layerMCP.commitChanges()
                    first=False 
                    
                layerMCP.startEditing() #ajouter le contenu du layer MCP dans celui qui va tous les regrouper
                for f in layer.getFeatures():
                    layerMCP.addFeature(f)
                layerMCP.commitChanges()
                
#Dans cette partie, il faut juster combiner les MCP de la meme annee qui sont dans la couche MCP.shp
#Copie du layer MCP et vidange
QgsVectorFileWriter.writeAsVectorFormat(layer,path+"/MCPfinal.shp",u'System',layer.dataProvider().crs())
layerMCPfinal=QgsVectorLayer(path+"/MCPfinal.shp","MCPfinal","ogr")
layerMCPfinal.startEditing()
for f in layerMCPfinal.getFeatures():
    layerMCPfinal.deleteFeature(f.id())
layerMCPfinal.commitChanges()
layerMCPfinal.startEditing()
for anneeMCP in layerMCP.uniqueValues(layerMCP.fieldNameIndex('annee')):
    geom=QgsGeometry()
    for f in layerMCP.getFeatures(QgsFeatureRequest(QgsExpression('"annee"='+str(anneeMCP)))):
        if geom.area()<0: #Si encore invalid (premiere passe)
            geom=QgsGeometry(f.geometry())
            print str(anneeMCP)  
        geom=QgsGeometry(f.geometry().combine(geom)) #Union de la geom precedente avec la nouvelle
        newFeature=QgsFeature(f) #copie
    newFeature.setGeometry(geom) 
    layerMCPfinal.addFeature(newFeature)#et on integre le MCP de cette anne dans le MCPfinal
layerMCPfinal.commitChanges()# toutes les annees sont traitees commit

#Refait un mcp (car l union des MCP n est pas un MCP)
layerMCPfinal.startEditing()
for f in layerMCPfinal.getFeatures():
    newGeom=f.geometry().convexHull()
    layerMCPfinal.changeGeometry(f.id(),newGeom)
layerMCPfinal.updateExtents()
layerMCPfinal.commitChanges()

layerMCPfinal.startEditing() #supression des champs parasites
field_index=layerMCPfinal.fieldNameIndex('perim')
layerMCPfinal.deleteAttribute(field_index)
field_index=layerMCPfinal.fieldNameIndex('id')
layerMCPfinal.deleteAttribute(field_index)
field_index=layerMCPfinal.fieldNameIndex('value')
layerMCPfinal.deleteAttribute(field_index)
layerMCPfinal.updateFields()
layerMCPfinal.commitChanges()

#MCP total des 10ans
layerMCPfinal.startEditing()
processing.runalg("qgis:convexhull",layerMCPfinal,'',0,pathMCP+"/MCPtotal.shp")
layerMCPtotal=QgsVectorLayer(pathMCP+"/MCPtotal.shp",'tototo','ogr')
for f in layerMCPtotal.getFeatures():#un seul normalement
    geom=QgsGeometry(f.geometry())
newFeature=QgsFeature(layerMCPfinal.dataProvider().fields())
newFeature.setGeometry(geom)
newFeature.setAttribute("annee",0)
okok = layerMCPfinal.addFeature(newFeature)
layerMCPfinal.commitChanges()

#Mise a jour du champs area
output_file.write('MCP \n\r')
layerMCPfinal.startEditing()
for f in layerMCPfinal.getFeatures():
    field_index=layerMCPfinal.fieldNameIndex('area')
    value=QgsExpression(' $area /1000000').evaluate(f)
    layerMCPfinal.changeAttributeValue(f.id(),field_index,value)
    output_file.write(str(f.attribute('annee')))
    output_file.write(';')
    output_file.write(str(int(round(value))))
    output_file.write('\n\r')
layerMCPfinal.commitChanges()



#Ajout a la carte
QgsMapLayerRegistry.instance().addMapLayers([layerMCPfinal]) 

#Symbologie des MCP
rpass=0
symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
rendererMCP=QgsRuleBasedRendererV2(symbol)
root_rule = rendererMCP.rootRule()
for year,color in years_colors: #2004 a 2015
        rPass+=1 #Les donnes les plus recentes dessus
        rule = root_rule.children()[0].clone()
        rule.setLabel(str(year))
        rule.setFilterExpression('"annee"=%i'%(year))
        rule.symbol().setColor(QColor(color))
        rule.symbol().symbolLayer(0).setRenderingPass(rPass)
        rule.symbol().setAlpha(0.3)
        root_rule.appendChild(rule)
        
root_rule.removeChildAt(0)
layerMCPfinal.setRendererV2(rendererMCP) # apply the renderer to the layer
canvas.setExtent(layerMCPfinal.extent()) #zoomer sur la couche mcp
#Traitement des mailles de presence (un seul layer avec indication de l annee)
annees=[]
first=True
for e in os.listdir(pathMaille):
    if os.path.isdir(pathMaille+"/"+e):
        annees.append(e)
for annee in annees:
    shapes=[]
    for e in os.listdir(pathMaille+"/"+annee):
        if e.endswith(".shp"):
            shapes.append(e)
    
    for shp in shapes:
        file=pathMaille+"/"+annee+"/"+shp
        layer=QgsVectorLayer(file,'truc',"ogr")
        layer.startEditing()
        layer.dataProvider().addAttributes([QgsField('annee', QVariant.Int)]) #ajouter un champs annee
        layer.updateFields()
        field_index=layer.fieldNameIndex('annee')
        for f in layer.getFeatures():
            layer.changeAttributeValue(f.id(),field_index,int(annee)) #inserer dans le champs annee (pris depuis le nom du dossier) j aurai du le faire dans l etape anvant
        layer.commitChanges()
        layer=QgsVectorLayer(file,'truc',"ogr") #Faut recharger le layer (updateFeature peut etre ?)
        if first: #Cloner le layer precend et le vider a la premiere passe
            QgsVectorFileWriter.writeAsVectorFormat(layer,path+"/Mailles.shp",u'System',layer.dataProvider().crs())
            layerMailles=QgsVectorLayer(path+"/Mailles.shp","Mailles","ogr")
            layerMailles.startEditing()
            for f in layerMailles.getFeatures():
                layerMailles.deleteFeature(f.id())
            layerMailles.commitChanges()
            first=False 
        layerMailles.startEditing()
        for f in layer.getFeatures():
            layerMailles.addFeature(f)
        layerMailles.commitChanges()
        
        
#Ici, il faut virer les mailles doublons (meme annee et meme id_maille)
layerMailles.startEditing()
for annee in annees:
    field_index=layerMailles.fieldNameIndex('ID')
    id_mailles=layerMailles.uniqueValues(field_index)
    for id in id_mailles:
        i=0
        for f in layerMailles.getFeatures(QgsFeatureRequest(QgsExpression('"annee"='+str(annee)+' AND "ID"='+str(id)))):
            if i>0: #Si plus de 1 objet, supprimer tous les suivants
                layerMailles.deleteFeature(f.id())
            i+=1
layerMailles.commitChanges()

#Compter les effectifs par maille (uniquement sur les points)
print "Compte des effectifs max par maille et par annee"
layerMailles.startEditing()
layerMailles.dataProvider().addAttributes([QgsField('effMax', QVariant.Int)]) #Ajout du champs pour recuperer la valeur
layerMailles.updateFields()
#layerMailles.commitChanges()
for file in os.listdir(path):
    if file.startswith("espace_point") and file.endswith(".shp"):
        shape=file
layer_pts=QgsVectorLayer(path+"/"+shape,"abcd","ogr")
for annee in annees:
    for f in layerMailles.getFeatures(QgsFeatureRequest().setFilterExpression('annee='+str(annee))):
        xmin=str(f.attribute("XMIN"))
        xmax=str(f.attribute("XMAX"))
        ymin=str(f.attribute("YMIN"))
        ymax=str(f.attribute("YMAX"))
        features_pts=layer_pts.getFeatures(QgsFeatureRequest().setFilterExpression('$x>'+xmin+' AND $x<'+xmax+' AND $y>'+ymin+' AND $y<'+ymax+' AND annee='+str(annee)))
        effectifs=[]
        for fp in features_pts:
            effectifs.append(fp.attribute("nb"))
        if len(effectifs)>0: #Si il y au moins 1 points dans la maille
            effectifs_max=max(effectifs)
            print annee
            print effectifs_max
            #field_index=layerMailles.fieldNameIndex("effMax")
            #layerMailles.startEditing()
            #test=layerMailles.changeAttributeValue(f.id(),field_index,effectifs_max)
            f["effMax"]=effectifs_max
        else:
            f["effMax"]=0
        layerMailles.updateFeature(f)
            
layerMailles.commitChanges()
layerMailles=QgsVectorLayer(path+"/Mailles.shp","Mailles","ogr") #jesaispaspourquoiilfautabsolumentcamaiscamarche

#Compter le nombre d'unique value de chaque annee et l'effectif max par maille
unique_ids=layerMailles.uniqueValues(layerMailles.fieldNameIndex('ID'))
nb_mailles_total=len(unique_ids)
eff_max_total=0
for id in unique_ids:
    eff=[]
    for f in layerMailles.getFeatures(QgsFeatureRequest().setFilterExpression('"ID"='+str(id))):
        eff.append(f["effMax"])
    eff_max_maille=max(eff)
    eff_max_total+=eff_max_maille
print 'nb maille total : '+str(nb_mailles_total)
output_file.write('\n\r Mailles;Nombre;Effectif')
for year,NULL in years_colors:
    somme_effectifs=0
    unique_values=set()
    output_file.write('\n\r')
    output_file.write(str(year)+';')
    for f in layerMailles.getFeatures(QgsFeatureRequest().setFilterExpression('"annee"='+str(year))):
        unique_values.add(f['ID'])
        somme_effectifs+=f["effMax"]
    output_file.write(str(len(unique_values)))
    output_file.write(";")
    output_file.write(str(somme_effectifs))
output_file.write('\n\r Total;')
output_file.write(str(nb_mailles_total))
output_file.write(';')
output_file.write(str(eff_max_total))
#Ajout et symbologie de la grille
QgsMapLayerRegistry.instance().addMapLayers([layerMailles])
rpass=0
symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
rendererMailles=QgsRuleBasedRendererV2(symbol)
root_rule = rendererMailles.rootRule()
for year,color in years_colors: #2004 a 2015
        rPass+=1 #Les donnes les plus recentes dessus
        rule = root_rule.children()[0].clone()
        rule.setLabel(str(year))
        rule.setFilterExpression('"annee"=%i'%(year))
        rule.symbol().setColor(QColor(color))
        rule.symbol().symbolLayer(0).setRenderingPass(rPass)
        rule.symbol().setAlpha(0.3)
        root_rule.appendChild(rule)
        
root_rule.removeChildAt(0)
layerMailles.setRendererV2(rendererMailles) # apply the renderer to the layer
output_file.close()

#Suppresion des shp qui servent plus a rien :
shutil.rmtree(path+'/MCP')
shutil.rmtree(path+'/Maille')

project = QgsProject.instance()
project.write(QFileInfo(path+'/projet.qgs')) #enregistre le projet

print "fini!"
