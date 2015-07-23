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
    if file.endswith('.shp'):
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
        rPass+=1 #Les donnes les plus recentes dessu
        rule = root_rule.children()[0].clone()
        rule.setLabel(str(year))
        rule.setFilterExpression('year("date_obs")=%i AND "nb">=0'%(year))
        
        rule.symbol().setColor(QColor(color))
        rule.symbol().symbolLayer(0).setRenderingPass(rPass)
        root_rule.appendChild(rule)

   
        
    root_rule.removeChildAt(0)
    # apply the renderer to the layer
    layer.setRendererV2(renderer)

    
    #MCP
    if not os.path.exists(path+'/MCP'):
        os.makedirs(path+'/MCP')
    for year,color in years_colors:
        
        features=layer.getFeatures(QgsFeatureRequest(QgsExpression('"nb">=0 AND year("date_obs")=%i' %(year))))

        layer.setSubsetString('year("date_obs")=%i'%(year))

        
        processing.runalg("qgis:convexhull",layer,'',0,path+"/MCP/"+str(year)+".shp")
        
    layer.setSubsetString('')
