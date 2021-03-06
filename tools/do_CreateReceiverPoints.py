# -*- coding: utf-8 -*-
"""
/***************************************************************************
 opeNoise

 Qgis Plugin to compute noise levels.

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

from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import os
import traceback

from math import *
from string import find, replace
from datetime import datetime

from ui_CreateReceiverPoints import Ui_CreateReceiverPoints_window
import on_CreateReceiverPoints

import on_Settings



# import VectorWriter
try:
    # Qgis from 2.0 to 2.4
    from processing.core.VectorWriter import VectorWriter
except:
    # Qgis from 2.6
    from processing.tools.vector import VectorWriter



class Dialog(QDialog,Ui_CreateReceiverPoints_window):
    
    def __init__(self, iface):
        QDialog.__init__(self, iface.mainWindow())
        self.iface = iface
        # Set up the user interface from Designer.
        self.setupUi(self)
                
        self.populateLayers()
        
        spaced_distance_list = ['1','2','3','4','5']        
        self.spaced_pts_comboBox.clear()
        for distance in spaced_distance_list:
            self.spaced_pts_comboBox.addItem(distance)
        self.spaced_pts_comboBox.setEnabled(False)
        
        self.middle_pts_radioButton.setChecked(1)
        self.spaced_pts_radioButton.setChecked(0)
        
        QObject.connect(self.middle_pts_radioButton, SIGNAL("toggled(bool)"), self.method_update)
        QObject.connect(self.spaced_pts_radioButton, SIGNAL("toggled(bool)"), self.method_update)

        QObject.connect(self.receiver_layer_pushButton, SIGNAL("clicked()"), self.outFile)        
        self.buttonBox = self.buttonBox.button( QDialogButtonBox.Ok )


        self.progressBar.setValue(0)
    
    
    def populateLayers( self ):
        self.buildings_layer_comboBox.clear()
        layers = []
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            try:
                if layer.geometryType() == QGis.Polygon:
                    layers.append(layer.name())
            except:            
                continue            

        layers.sort()
        self.buildings_layer_comboBox.addItems(layers)
        
    def outFile(self):
        self.receiver_layer_lineEdit.clear()
        #self.shapefileName = QFileDialog.getSaveFileName(None,'Open file', "", "Shapefile (*.shp);;All files (*)")
        
        self.shapefileName = QFileDialog.getSaveFileName(None,'Open file', on_Settings.getOneSetting('directory_last') , "Shapefile (*.shp);;All files (*)")

        if self.shapefileName is None or self.shapefileName == "":
            return
            
        if find(self.shapefileName,".shp") == -1 and find(self.shapefileName,".SHP") == -1:
            self.receiver_layer_lineEdit.setText( self.shapefileName + ".shp")
        else:
            self.receiver_layer_lineEdit.setText( self.shapefileName)
       
        on_Settings.setOneSetting('directory_last',os.path.dirname(self.receiver_layer_lineEdit.text()))
            
    
    def method_update(self):
        
        if self.middle_pts_radioButton.isChecked():
            self.spaced_pts_comboBox.setEnabled(False)
        if self.spaced_pts_radioButton.isChecked():
            self.spaced_pts_comboBox.setEnabled(True)


    def log_start(self):
        
        global log_errors, log_errors_path_name
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)        
        log_errors_path_name = os.path.join(dir_path,"log_CreateReceiverPoints_errors.txt")
        log_errors = open(log_errors_path_name,"w")
        log_errors.write(self.tr("opeNoise") + " - " + self.tr("Create Receiver Points") + " - " + self.tr("Errors") + "\n\n")
        
        
    def log_end(self):

        log_errors.close()    

    def accept(self):
      
        self.buttonBox.setEnabled( False )
        
        if self.buildings_layer_comboBox.currentText() == "":
            QMessageBox.information(self, self.tr("opeNoise - Create Receiver Points"), self.tr("Please specify the buildings vector layer"))
            self.buttonBox.setEnabled( True )
            return
        elif self.receiver_layer_lineEdit.text() == "":
            QMessageBox.information(self, self.tr("opeNoise - Create Receiver Points"), self.tr("Please specify output shapefile"))
            
            self.buttonBox.setEnabled( True )
            return
        else:
            
            buildings_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.buildings_layer_comboBox.currentText())[0]
            buildings_layer_path = buildings_layer.source()
            receiver_points_layer_path = self.receiver_layer_lineEdit.text()
            
            # writes the settings log file
            self.log_start()
            
            self.time_start = datetime.now()
            
            bar = self.progressBar
            
            try:
                # CreateReceiverPoints
            
                if self.middle_pts_radioButton.isChecked():
                    on_CreateReceiverPoints.middle(bar,buildings_layer_path,receiver_points_layer_path)
                if self.spaced_pts_radioButton.isChecked():
                    spaced_pts_distance = float(self.spaced_pts_comboBox.currentText())
                    on_CreateReceiverPoints.spaced(bar,buildings_layer_path,receiver_points_layer_path,spaced_pts_distance)

                run = 1

            except:
                error= traceback.format_exc()
                log_errors.write(error)
                run = 0
                
            self.time_end = datetime.now()

            if run == 1:
                log_errors.write(self.tr("No errors.") + "\n\n") 
                result_string = self.tr("Receiver points created with success.") + "\n\n" +\
                                self.tr("Start: ") + self.time_start.strftime("%a %d/%b/%Y %H:%M:%S") + "\n" +\
                                self.tr("End: ") + self.time_end.strftime("%a %d/%b/%Y %H:%M:%S") + "\n"+\
                                self.tr("Duration: ") + str(self.duration())

                QMessageBox.information(self, self.tr("opeNoise - Create Receiver Points"), result_string)
            else:
                result_string = self.tr("Sorry, process not complete.") + "\n\n" +\
                                self.tr("View the log file to understand the problem:") + "\n" +\
                                str(log_errors_path_name) + "\n\n" +\
                                self.tr("Start: ") + self.time_start.strftime("%a %d/%b/%Y %H:%M:%S.%f") + "\n" +\
                                self.tr("End: ") + self.time_end.strftime("%a %d/%b/%Y %H:%M:%S.%f") + "\n"+\
                                self.tr("Duration: ") + str(self.duration())
                                
                QMessageBox.information(self, self.tr("opeNoise - Create Receiver Points"), self.tr(result_string))
                
                self.buttonBox.setEnabled( True )

           
            self.log_end()
        
        
        self.progressBar.setValue(0)
        self.buttonBox.setEnabled( True )

        self.close()
        
    def duration(self):
        duration = self.time_end - self.time_start
        duration_h = duration.seconds/3600
        duration_m = (duration.seconds - duration_h*3600)/60
        duration_s = duration.seconds - duration_m*60 - duration_h*3600
        duration_string = str(format(duration_h, '02')) + ':' + str(format(duration_m, '02')) + ':' + str(format(duration_s, '02')) + "." + str(format(duration.microseconds/1000, '003'))        
        return duration_string
    
    

    
