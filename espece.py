from PyQt4.QtGui import *
from PyQt4.QtCore import *
import processing
import os

canvas = iface.mapCanvas()

#path=QFileDialog.getExistingDirectory()
path='/home/users/jbdesbas/Documents/Listes rouges/Evaluation/Orthopteres/Gomphocerippus rufus'

listdir=os.listdir(path)
shapes=[]
for file in listdir:
    if file.endswith('.shp') and file!=('MCP.shp') and file!=('MCPfinal.shp'):
        shapes.append(file)

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

for shape in shapes:
  
       
    layer=QgsVectorLayer(path+'/'+shape,"Temp","ogr")
   
        
    if layer.geometryType()==0: #Point
        geomType='Point'
    elif layer.geometryType()==1: #Ligne
        geomType='linestring'
    elif layer.geometryType()==2: #Polygon
        geomType='Polygon' 
    layer.setDataSource(path+'/'+shape,geomType,"ogr")
    
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
    
    QgsMapLayerRegistry.instance().addMapLayers([layer])
 
    symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
    renderer=QgsRuleBasedRendererV2(symbol)
    root_rule = renderer.rootRule()
    
    rPass=10
    if geomType=='Point': #Carre blanc pour les prospe negative
        rule = root_rule.children()[0].clone()
        rule.setLabel('prosp neg')
        rule.setFilterExpression('"nb"=-1')
        rule.symbol().symbolLayer(0).setName("square")
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
    layer.setRendererV2(renderer) # apply the renderer to the layer

    
    #MCP
    pathMCP=path+'/MCP'
   
    for year,NULL in years_colors:
        if not os.path.exists(pathMCP+'/'+str(year)):
            os.makedirs(pathMCP+'/'+str(year))
        
        layer.setSubsetString('"annee"=%i and "nb">=0'%(year))

        processing.runalg("qgis:convexhull",layer,'',0,pathMCP+"/"+str(year)+"/"+geomType+".shp")#il aurait ete possible dutiliser un outil integre
        
    layer.setSubsetString('')

#for element in os.listdir(pathMCP): #plus simple avec os.walk ?
#    element=pathMCP+"/"+element
#    if(os.path.isdir(element)):
#        for shp in os.listdir(element):
#            if shp.endswith('.shp'):
#                print element+"/"+shp
                
shps=[]
first=True

for annee in os.listdir(pathMCP):
    annee2=int(annee)
    annee=pathMCP+"/"+annee
    if(os.path.isdir(annee)):
        for file in os.listdir(annee):
            file=annee+"/"+file
            if file.endswith('.shp'):
                layer=QgsVectorLayer(file,'toto',"ogr")
                print file
                layer.startEditing()
                layer.dataProvider().addAttributes([QgsField('annee', QVariant.Int)])
                layer.updateFields()
                field_index=layer.fieldNameIndex('annee')
                for f in layer.getFeatures():
                    #layer.updateFeature(f)
                    layer.changeAttributeValue(f.id(),field_index,annee2) 
                layer.commitChanges()
                #layer.dataProvider.updateExtents()
                layer=QgsVectorLayer(file,'toto',"ogr") #Faut rechercher le layer sinon ca marche pas je sais pas pquoi et ca m enerve

                if first: #Cloner le layer precend et le vider
                    QgsVectorFileWriter.writeAsVectorFormat(layer,path+"/MCP.shp",u'System',layer.dataProvider().crs())
                    layerMCP=QgsVectorLayer(path+"/MCP.shp","MCP","ogr")
                    layerMCP.startEditing()
                    for f in layerMCP.getFeatures():
                        layerMCP.deleteFeature(f.id())
                    layerMCP.commitChanges()
                    first=False 
                    
                layerMCP.startEditing()
                for f in layer.getFeatures():
                    layerMCP.addFeature(f)
                layerMCP.commitChanges()
                
                #Reste plus que a grouper les geometrie avec la meme annee
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
            
        geom=QgsGeometry(f.geometry().combine(geom))
        newFeature=QgsFeature(f) #copie
    newFeature.setGeometry(geom)
    
    layerMCPfinal.addFeature(newFeature)
layerMCPfinal.commitChanges()
#Faire la mise a jour des area et perimeter
#Ce n est pas encore un vrai bon MCP il faut autiliser QgsGeometry::convexHull et mettre a jour la geom
#Recharger ?
QgsMapLayerRegistry.instance().addMapLayers([layerMCPfinal])
