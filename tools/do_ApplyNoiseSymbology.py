# -*- coding: utf-8 -*-
"""
/***************************************************************************
 opeNoise

 Qgis Plugin to compute noise levels

                             -------------------
        begin                : March 2014
        copyright            : (C) 2014 by Arpa Piemonte
        email                : s.masera@arpa.piemonte.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import os, imp
import traceback

from datetime import datetime
from ui_ApplyNoiseSymbology import Ui_ApplyNoiseSymbology_window

import on_ApplyNoiseSymbology 

class Dialog(QDialog,Ui_ApplyNoiseSymbology_window):
   
    def __init__(self, iface):
        QDialog.__init__(self, iface.mainWindow())
        
        self.iface = iface
        # Set up the user interface from Designer.
        self.setupUi(self)
       
        self.populate_comboBox()
        
        self.progressBar.setValue(0)

        self.update_field_layer()
        
        QObject.connect(self.layer_comboBox, SIGNAL("currentIndexChanged(QString)"), self.update_field_layer)
        
        self.run_buttonBox.button( QDialogButtonBox.Ok )

        
    def populate_comboBox( self ):
       
        self.layer_comboBox.clear()
        layers = []
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            try:
                if layer.geometryType() == QGis.Point or layer.geometryType() == QGis.Line or layer.geometryType() == QGis.Polygon:
                    layers.append(layer.name())
            except:            
                continue

        layers.sort()
        self.layer_comboBox.addItems(layers)

        
    def update_field_layer(self):
        
        if unicode(self.layer_comboBox.currentText()) == "":
            return

        layer = QgsMapLayerRegistry.instance().mapLayersByName(self.layer_comboBox.currentText())[0]
        layer_fields = list(layer.dataProvider().fields())
        
        #self.id_field_comboBox.clear() 
        self.level_comboBox.clear()        
        
        layer_fields_number = ['']
        
        for f in layer_fields:
            if f.type() == QVariant.Int or f.type() == QVariant.Double:         
                layer_fields_number.append(unicode(f.name()))

        for f_label in layer_fields_number:
            #self.id_field_comboBox.addItem(f_label)
            self.level_comboBox.addItem(f_label)
            

    def controls(self):
        self.run_buttonBox.setEnabled( False )
        if self.layer_comboBox.currentText() == "":
            QMessageBox.information(self, self.tr("opeNoise - Apply Noise Symbology"), self.tr("Please specify the input vector layer."))
            return 0
        
        if self.level_comboBox.currentText() == "":
               message = self.tr("Please specify the level field to apply") + "\n" + self.tr("the noise symbology.")
               QMessageBox.information(self, self.tr("opeNoise - Apply Noise Symbology"), self.tr(message))
               return 0
            
        return 1

    def accept(self):
        self.run_buttonBox.setEnabled( False )
        
        if self.controls() == 0:
            self.run_buttonBox.setEnabled( True )
            return
        
        self.log_start()  
        layer = QgsMapLayerRegistry.instance().mapLayersByName(self.layer_comboBox.currentText())[0]
        field = self.level_comboBox.currentText()
        
        # writes the settings log file
        
        self.time_start = datetime.now()
        
        # Run
        try:    
            on_ApplyNoiseSymbology.render(layer,field)
            run = 1
        except:
            error= traceback.format_exc()
            log_errors.write(error)
            run = 0
            
        self.time_end = datetime.now()
        
        if run == 1:
            log_errors.write(self.tr("No errors.") + "\n\n")
            result_string = self.tr("Noise symbology assigned with success.") + "\n\n" +\
                            self.tr("Start: ") + self.time_start.strftime("%a %d/%b/%Y %H:%M:%S") + "\n" +\
                            self.tr("End: ") + self.time_end.strftime("%a %d/%b/%Y %H:%M:%S") + "\n"+\
                            self.tr("Duration: ") + str(self.duration())
            QMessageBox.information(self, self.tr("opeNoise - Apply Noise Symbology"), self.tr(result_string))
#            self.iface.messageBar().pushMessage(self.tr("opeNoise - Apply Noise Symbology"), self.tr("Process complete"))
        else:
            result_string = self.tr("Sorry, process not complete.") + "\n\n" +\
                            self.tr("View the log file to understand the problem:") + "\n" +\
                            str(log_errors_path_name) + "\n\n" +\
                            self.tr("Start: ") + self.time_start.strftime("%a %d/%b/%Y %H:%M:%S.%f") + "\n" +\
                            self.tr("End: ") + self.time_end.strftime("%a %d/%b/%Y %H:%M:%S.%f") + "\n"+\
                            self.tr("Duration: ") + str(self.duration())
            QMessageBox.information(self, self.tr("opeNoise - Apply Noise Symbology"), self.tr(result_string))
#            self.iface.messageBar().pushMessage("opeNoise - Apply Noise Symbology", "Process not complete")

        self.log_end()

        self.run_buttonBox.setEnabled( True )

#        self.iface.mainWindow().statusBar().clearMessage()
#        self.iface.mapCanvas().refresh() 
        self.close()  


    def duration(self):
        duration = self.time_end - self.time_start
        duration_h = duration.seconds/3600
        duration_m = (duration.seconds - duration_h*3600)/60
        duration_s = duration.seconds - duration_m*60 - duration_h*3600
        duration_string = str(format(duration_h, '02')) + ':' + str(format(duration_m, '02')) + ':' + str(format(duration_s, '02')) + "." + str(format(duration.microseconds/1000, '003'))        
        return duration_string
    
    def log_start(self):
        
        global log_errors, log_errors_path_name
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)        
        log_errors_path_name = os.path.join(dir_path,"log_ApplyNoiseSymbology_errors.txt")
        log_errors = open(log_errors_path_name,"w")
        log_errors.write(self.tr("opeNoise") + " - " + self.tr("Apply Noise Symbology") + " - " + self.tr("Errors") + "\n\n")    
        
    def log_end(self):

        log_errors.close()                
        
        
