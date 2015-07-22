from PyQt4.QtGui import *
from PyQt4.QtCore import *
import processing
import os

canvas = iface.mapCanvas()

#path=QFileDialog.getExistingDirectory()
path='/home/jb/Code/python/UICN/Odonates/Aeshna affinis  VAN DER LINDEN, 1820'

listdir=os.listdir(path)
shapes=[]
for file in listdir:
    if file.endswith('.shp'):
        shapes.append(file)

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
    
    #Faire ici un tableau de couleur
    
    #Debut boucle
    rule = root_rule.children()[0].clone()
    rule.setLabel('2014')
    rule.setFilterExpression('year("date_obs")=2014')
    rule.symbol().setColor(QColor('orange'))
    
    root_rule.appendChild(rule)
    #Fin boucle
    
    #Ajouter une rule pour les -1 et les données < 2003
    
    #root_rule.removeChildAt(0)

    # apply the renderer to the layer
    layer.setRendererV2(renderer)

    
