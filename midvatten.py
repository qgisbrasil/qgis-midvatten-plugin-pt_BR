# -*- coding: iso-8859-1 -*-
"""
/***************************************************************************
 This is the main part of the Midvatten plugin. 
 Mainly controlling user interaction and calling for other classes. 
                             -------------------
        begin                : 2011-10-18
        copyright            : (C) 2011 by joskal
        email                : groundwatergis [at] gmail.com
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import qgis.utils
import resources  # Initialize Qt resources from file resources.py

# Import some general python modules
import os.path
import sys
import datetime
import zipfile
try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

#add midvatten plugin directory to pythonpath (needed here to allow importing modules from subfolders)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/tools'))

# Import Midvatten tools and modules
from tsplot import TimeSeriesPlot
from stratigraphy import Stratigraphy
from xyplot import XYPlot
from wqualreport import wqualreport
from loaddefaultlayers import loadlayers
from prepareforqgis2threejs import PrepareForQgis2Threejs
import midvatten_utils as utils 
from definitions import midvatten_defs
from sectionplot import SectionPlot
import customplot
from midvsettings import midvsettings
import midvsettingsdialog
from piper import PiperPlot
from export_data import ExportData
#import profilefromdem

class midvatten:
    def __init__(self, iface): # Might need revision of variables and method for loading default variables
        #sys.path.append(os.path.dirname(os.path.abspath(__file__))) #add midvatten plugin directory to pythonpath
        self.iface = iface
        self.ms = midvsettings()#self.ms.settingsdict is created when ms is imported
        
    def initGui(self):
        # Create actions that will start plugin configuration
        self.actionNewDB = QAction(QIcon(":/plugins/midvatten/icons/create_new.xpm"), "Criar uma nova base de dados Midvatten", self.iface.mainWindow())
        QObject.connect(self.actionNewDB, SIGNAL("triggered()"), self.new_db)
        
        self.actionloadthelayers = QAction(QIcon(":/plugins/midvatten/icons/loaddefaultlayers.png"), "Carregar as camadas padrão ao QGIS", self.iface.mainWindow())
        self.actionloadthelayers.setWhatsThis("Carrega as camadas padrão da base de dados selecionada")
        self.iface.registerMainWindowAction(self.actionloadthelayers, "F7")   # The function should also be triggered by the F7 key
        QObject.connect(self.actionloadthelayers, SIGNAL("activated()"), self.loadthelayers)

        self.actionsetup = QAction(QIcon(":/plugins/midvatten/icons/MidvSettings.png"), "Configurações Midvatten", self.iface.mainWindow())
        self.actionsetup.setWhatsThis("Configuração das ferramentas Midvatten")
        self.iface.registerMainWindowAction(self.actionsetup, "F6")   # The function should also be triggered by the F6 key
        QObject.connect(self.actionsetup, SIGNAL("activated()"), self.setup)
        
        self.actionresetSettings = QAction(QIcon(":/plugins/midvatten/icons/ResetSettings.png"), "Resetar configurações", self.iface.mainWindow())
        QObject.connect(self.actionresetSettings, SIGNAL("triggered()"), self.reset_settings)
        
        self.actionabout = QAction(QIcon(":/plugins/midvatten/icons/about.png"), "Sobre", self.iface.mainWindow())
        QObject.connect(self.actionabout, SIGNAL("triggered()"), self.about)
        
        self.actionupdatecoord = QAction(QIcon(":/plugins/midvatten/icons/updatecoordfrpos.png"), "Atualizar coordenadas pela posição do mapa", self.iface.mainWindow())
        QObject.connect(self.actionupdatecoord , SIGNAL("triggered()"), self.updatecoord)
        
        self.actionupdateposition = QAction(QIcon(":/plugins/midvatten/icons/updateposfrcoord.png"), "Atualizar posição do mapa pelas coordenadas", self.iface.mainWindow())
        QObject.connect(self.actionupdateposition , SIGNAL("triggered()"), self.updateposition)
        
        self.action_import_wlvl = QAction(QIcon(":/plugins/midvatten/icons/load_wlevels_manual.png"), "Importar leituras de nível de água", self.iface.mainWindow())
        QObject.connect(self.action_import_wlvl , SIGNAL("triggered()"), self.import_wlvl)
        
        self.action_import_wflow = QAction(QIcon(":/plugins/midvatten/icons/load_wflow.png"), "Importar medidas de fluxo", self.iface.mainWindow())
        QObject.connect(self.action_import_wflow , SIGNAL("triggered()"), self.import_wflow)
        
        self.action_import_seismics = QAction(QIcon(":/plugins/midvatten/icons/load_seismics.png"), "Importar dados sísmicos", self.iface.mainWindow())
        QObject.connect(self.action_import_seismics , SIGNAL("triggered()"), self.import_seismics)
        
        self.action_import_vlf = QAction(QIcon(":/plugins/midvatten/icons/load_vlf.png"), "Importar dados vlf", self.iface.mainWindow())
        QObject.connect(self.action_import_vlf , SIGNAL("triggered()"), self.import_vlf)
        
        self.action_import_obs_lines = QAction(QIcon(":/plugins/midvatten/icons/import_obs_lines.png"), "Importar tabela obs lines", self.iface.mainWindow())
        QObject.connect(self.action_import_obs_lines , SIGNAL("triggered()"), self.import_obs_lines)
        
        self.action_wlvlcalculate = QAction(QIcon(":/plugins/midvatten/icons/calc_level_masl.png"), "Calcular nível de água acima do nível do mar", self.iface.mainWindow())
        QObject.connect(self.action_wlvlcalculate , SIGNAL("triggered()"), self.wlvlcalculate)
        
        self.action_aveflowcalculate = QAction(QIcon(":/plugins/midvatten/icons/import_wflow.png"), "Calcular Aveflow de Accvol", self.iface.mainWindow())
        QObject.connect(self.action_aveflowcalculate , SIGNAL("triggered()"), self.aveflowcalculate)
        
        self.action_import_wlvllogg = QAction(QIcon(":/plugins/midvatten/icons/load_wlevels_logger.png"), "Importar nível de água pelo logger", self.iface.mainWindow())
        QObject.connect(self.action_import_wlvllogg , SIGNAL("triggered()"), self.import_wlvllogg)
        
        self.action_wlvlloggcalibrate = QAction(QIcon(":/plugins/midvatten/icons/calibr_level_logger_masl.png"), "Calibrar nível de água pelo logger", self.iface.mainWindow())
        QObject.connect(self.action_wlvlloggcalibrate , SIGNAL("triggered()"), self.wlvlloggcalibrate)

        self.actionimport_wqual_lab = QAction(QIcon(":/plugins/midvatten/icons/import_wqual_lab.png"), "Importar dados de lab. de qual. água", self.iface.mainWindow())
        QObject.connect(self.actionimport_wqual_lab, SIGNAL("triggered()"), self.import_wqual_lab)
        
        self.actionimport_wqual_field = QAction(QIcon(":/plugins/midvatten/icons/import_wqual_field.png"), "Importar dados de campo de qual. água", self.iface.mainWindow())
        QObject.connect(self.actionimport_wqual_field, SIGNAL("triggered()"), self.import_wqual_field)
        
        self.actionimport_stratigraphy = QAction(QIcon(":/plugins/midvatten/icons/import_stratigraphy.png"), "Importar dados estratigráficos", self.iface.mainWindow())
        QObject.connect(self.actionimport_stratigraphy, SIGNAL("triggered()"), self.import_stratigraphy)
        
        self.actionimport_obs_points = QAction(QIcon(":/plugins/midvatten/icons/import_obs_points.png"), "Importar tabela obs points", self.iface.mainWindow())
        QObject.connect(self.actionimport_obs_points, SIGNAL("triggered()"), self.import_obs_points)
        
        self.actionimport_wflow = QAction(QIcon(":/plugins/midvatten/icons/import_wflow.png"), "Importar medidas de fluxo de água", self.iface.mainWindow())
        QObject.connect(self.actionimport_wflow, SIGNAL("triggered()"), self.import_wflow)
        
        self.actionimport_meteo = QAction(QIcon(":/plugins/midvatten/icons/import_wqual_field.png"), "Importar observações metereológicas", self.iface.mainWindow())
        QObject.connect(self.actionimport_meteo, SIGNAL("triggered()"), self.import_meteo)
        
        self.actionPlotTS = QAction(QIcon(":/plugins/midvatten/icons/PlotTS.png"), "Gráfico de série temporal", self.iface.mainWindow())
        self.actionPlotTS.setWhatsThis("Plota a serie temporal para os objetos selecionados")
        self.iface.registerMainWindowAction(self.actionPlotTS, "F8")   # The function should also be triggered by the F8 key
        QObject.connect(self.actionPlotTS, SIGNAL("triggered()"), self.plot_timeseries)
        
        self.actionPlotXY = QAction(QIcon(":/plugins/midvatten/icons/PlotXY.png"), "Gráfico de dispersão", self.iface.mainWindow())
        self.actionPlotXY.setWhatsThis("Plota dados de dispersão XY (e.g. perfil sísmico) para os objetos selecionados")
        self.iface.registerMainWindowAction(self.actionPlotXY, "F9")   # The function should also be triggered by the F9 key
        QObject.connect(self.actionPlotXY, SIGNAL("triggered()"), self.plot_xy)
        
        self.actionPlotPiper = QAction(QIcon(os.path.join(os.path.dirname(__file__),"icons","Piper.png")), "Diagrama Piper", self.iface.mainWindow())
        self.actionPlotPiper.setWhatsThis("Plota o diagrama Piper para os objetos selecionados")
        QObject.connect(self.actionPlotPiper, SIGNAL("triggered()"), self.plot_piper)
                
        self.actionPlotSQLite = QAction(QIcon(os.path.join(os.path.dirname(__file__),"icons","plotsqliteicon.png")), "Gráficos customizados", self.iface.mainWindow())
        self.actionPlotSQLite.setWhatsThis("Cria gráficos customizados para relatórios")
        QObject.connect(self.actionPlotSQLite, SIGNAL("triggered()"), self.plot_sqlite)
        
        self.actionPlotStratigraphy = QAction(QIcon(":/plugins/midvatten/icons/PlotStratigraphy.png"), "Perfil estratigráfico", self.iface.mainWindow())
        self.actionPlotStratigraphy.setWhatsThis("Mostra a estratigrafia dos objetos selecionados (modified ARPAT)")
        self.iface.registerMainWindowAction(self.actionPlotStratigraphy, "F10")   # The function should also be triggered by the F10 key
        QObject.connect(self.actionPlotStratigraphy, SIGNAL("triggered()"), self.plot_stratigraphy)
        
        self.actiondrillreport = QAction(QIcon(":/plugins/midvatten/icons/drill_report.png"), "Relatório Geral", self.iface.mainWindow())
        self.actiondrillreport.setWhatsThis("Mostra um relatório geral para os obs points selecionados")
        self.iface.registerMainWindowAction(self.actiondrillreport, "F11")   # The function should also be triggered by the F11 key
        QObject.connect(self.actiondrillreport, SIGNAL("triggered()"), self.drillreport)

        self.actionwqualreport = QAction(QIcon(":/plugins/midvatten/icons/wqualreport.png"), "Relatório de qualidade da água", self.iface.mainWindow())
        self.actionwqualreport.setWhatsThis("Mostra a qualidade da água para os obs points selecionados")
        self.iface.registerMainWindowAction(self.actionwqualreport, "F12")   # The function should also be triggered by the F12 key
        QObject.connect(self.actionwqualreport, SIGNAL("triggered()"), self.waterqualityreport)

        self.actionPlotSection = QAction(QIcon(":/plugins/midvatten/icons/PlotSection.png"), "Plotagem de Seção", self.iface.mainWindow())
        self.actionPlotSection.setWhatsThis("Plota uma seção com estratigrafia e níveis de água")
        #self.iface.registerMainWindowAction(self.actionChartMaker, "F12")   # The function should also be triggered by the F12 key
        QObject.connect(self.actionPlotSection, SIGNAL("triggered()"), self.plot_section)
        
        self.actionPrepareFor2Qgis2ThreeJS = QAction(QIcon(":/plugins/midvatten/icons/qgis2threejs.png"), "Prepara dados para o plugin Qgis2threejs", self.iface.mainWindow())
        self.actionPrepareFor2Qgis2ThreeJS.setWhatsThis("Add spatialite views to be used by Qgis2threejs plugin to create a 3D plot")
        QObject.connect(self.actionPrepareFor2Qgis2ThreeJS, SIGNAL("triggered()"), self.prepare_layers_for_qgis2threejs)

        self.actionVacuumDB = QAction(QIcon(":/plugins/midvatten/icons/vacuum.png"), "Varre a base de dados", self.iface.mainWindow())
        self.actionVacuumDB.setWhatsThis("Performa a varredura da base de dados")
        QObject.connect(self.actionVacuumDB, SIGNAL("triggered()"), self.vacuum_db)

        self.actionZipDB = QAction(QIcon(":/plugins/midvatten/icons/zip.png"), "Backup da base de dados", self.iface.mainWindow())
        self.actionZipDB.setWhatsThis("Uma copia comprimida da base de dados sera colocada no mesmo diretorio da BD.")
        QObject.connect(self.actionZipDB, SIGNAL("triggered()"), self.zip_db)

        self.action_export_csv = QAction(QIcon(":/plugins/midvatten/icons/export_csv.png"), "Exporta para um conjunto de arquivos csv", self.iface.mainWindow())
        self.action_export_csv.setWhatsThis("Todos dados dos objetos selecionados (obs_points e obs_lines) serão exportados para um conjunto de arquivos csv.")
        QObject.connect(self.action_export_csv, SIGNAL("triggered()"), self.export_csv)

        self.action_export_spatialite = QAction(QIcon(":/plugins/midvatten/icons/export_spatialite.png"), "Exporta para outra base de dados spatialite", self.iface.mainWindow())
        self.action_export_spatialite.setWhatsThis("Todos os dados dos objetos selecionados (obs_points e obs_lines) serão exportados para outra BD spatialite.")
        QObject.connect(self.action_export_spatialite, SIGNAL("triggered()"), self.export_spatialite)

        # Add toolbar with buttons 
        self.toolBar = self.iface.addToolBar("Midvatten")
        self.toolBar.addAction(self.actionsetup)
        #self.toolBar.addAction(self.actionloadthelayers)
        self.toolBar.addAction(self.actionPlotTS)
        self.toolBar.addAction(self.actionPlotXY)
        self.toolBar.addAction(self.actionPlotStratigraphy)
        self.toolBar.addAction(self.actionPlotSection)
        self.toolBar.addAction(self.actionPlotSQLite)
        self.toolBar.addAction(self.actionPlotPiper)
        self.toolBar.addAction(self.actiondrillreport)
        self.toolBar.addAction(self.actionwqualreport)
        #self.toolBar.addAction(self.actionChartMaker)
        
        # Add plugins menu items
        self.menu = QMenu("Midvatten")
        self.menu.import_data_menu = QMenu(QCoreApplication.translate("Midvatten", "&Importar dados para a base de dados"))
        #self.iface.addPluginToMenu("&Midvatten", self.menu.add_data_menu.menuAction())
        self.menu.addMenu(self.menu.import_data_menu)
        self.menu.import_data_menu.addAction(self.actionimport_obs_points)   
        self.menu.import_data_menu.addAction(self.action_import_wlvl)   
        self.menu.import_data_menu.addAction(self.action_import_wlvllogg)   
        self.menu.import_data_menu.addAction(self.actionimport_wqual_lab)
        self.menu.import_data_menu.addAction(self.actionimport_wqual_field)   
        self.menu.import_data_menu.addAction(self.action_import_wflow)   
        self.menu.import_data_menu.addAction(self.actionimport_stratigraphy)
        self.menu.import_data_menu.addAction(self.actionimport_meteo)
        self.menu.import_data_menu.addAction(self.action_import_obs_lines)   
        self.menu.import_data_menu.addAction(self.action_import_seismics)   
        self.menu.import_data_menu.addAction(self.action_import_vlf)   

        self.menu.export_data_menu = QMenu(QCoreApplication.translate("Midvatten", "&Exportar dados da base de dados"))
        self.menu.addMenu(self.menu.export_data_menu)
        self.menu.export_data_menu.addAction(self.action_export_csv)   
        self.menu.export_data_menu.addAction(self.action_export_spatialite)   
        
        self.menu.add_data_menu = QMenu(QCoreApplication.translate("Midvatten", "&Editar base de dados"))
        #self.iface.addPluginToMenu("&Midvatten", self.menu.add_data_menu.menuAction())
        self.menu.addMenu(self.menu.add_data_menu)
        self.menu.add_data_menu.addAction(self.action_wlvlcalculate)   
        self.menu.add_data_menu.addAction(self.action_wlvlloggcalibrate)   
        self.menu.add_data_menu.addAction(self.actionupdatecoord)   
        self.menu.add_data_menu.addAction(self.actionupdateposition)   
        self.menu.add_data_menu.addAction(self.action_aveflowcalculate)   

        self.menu.plot_data_menu = QMenu(QCoreApplication.translate("Midvatten", "&Gerar gráficos"))
        #self.iface.addPluginToMenu("&Midvatten", self.menu.plot_data_menu.menuAction())
        self.menu.addMenu(self.menu.plot_data_menu)
        self.menu.plot_data_menu.addAction(self.actionPlotTS) 
        self.menu.plot_data_menu.addAction(self.actionPlotXY)
        self.menu.plot_data_menu.addAction(self.actionPlotStratigraphy)
        self.menu.plot_data_menu.addAction(self.actionPlotSection)
        self.menu.plot_data_menu.addAction(self.actionPlotSQLite)
        self.menu.plot_data_menu.addAction(self.actionPlotPiper)

        self.menu.report_menu = QMenu(QCoreApplication.translate("Midvatten", "&Gerar relatórios"))
        self.menu.addMenu(self.menu.report_menu)
        self.menu.report_menu.addAction(self.actiondrillreport)
        self.menu.report_menu.addAction(self.actionwqualreport)


        self.menu.prepare_menu = QMenu(QCoreApplication.translate("Midvatten", "&Preparar dados 3D"))
        self.menu.addMenu(self.menu.prepare_menu)
        self.menu.prepare_menu.addAction(self.actionPrepareFor2Qgis2ThreeJS)
        
        self.menu.db_manage_menu = QMenu(QCoreApplication.translate("Midvatten", "&Gerenciar base de dados"))
        self.menu.addMenu(self.menu.db_manage_menu)
        self.menu.db_manage_menu.addAction(self.actionNewDB)
        self.menu.db_manage_menu.addAction(self.actionVacuumDB)
        self.menu.db_manage_menu.addAction(self.actionZipDB)
        
        self.menu.addSeparator()

        self.menu.addAction(self.actionloadthelayers)   
        self.menu.addAction(self.actionsetup)
        self.menu.addAction(self.actionresetSettings)
        self.menu.addAction(self.actionabout)
        #self.iface.addPluginToMenu("&Midvatten", self.actionsetup)
        #self.iface.addPluginToMenu("&Midvatten", self.actionresetSettings)
        #self.iface.addPluginToMenu("&Midvatten", self.actionabout)
        menuBar = self.iface.mainWindow().menuBar()
        menuBar.addMenu(self.menu)

        # QGIS iface connections
        self.iface.projectRead.connect(self.project_opened)
        self.iface.newProjectCreated.connect(self.project_created)

    def unload(self):    
        # Remove the plugin menu items and icons
        self.menu.deleteLater()

        # remove tool bar
        del self.toolBar
        
        # Also remove F5 - F12 key triggers
        self.iface.unregisterMainWindowAction(self.actionloadthelayers)
        self.iface.unregisterMainWindowAction(self.actionsetup)
        self.iface.unregisterMainWindowAction(self.actionPlotTS)
        self.iface.unregisterMainWindowAction(self.actionPlotXY)
        self.iface.unregisterMainWindowAction(self.actionPlotStratigraphy)
        self.iface.unregisterMainWindowAction(self.actiondrillreport)
        self.iface.unregisterMainWindowAction(self.actionwqualreport)
        sys.path.remove(os.path.dirname(os.path.abspath(__file__))) #Clean up python environment

    def about(self):   
        filenamepath = os.path.join(os.path.dirname(__file__),"metadata.txt" )
        iniText = QSettings(filenamepath , QSettings.IniFormat)#This method seems to return a list of unicode strings BUT it seems as if the encoding from the byte strings in the file is not utf-8, hence there is need for special encoding, see below
        verno = str(iniText.value('version'))
        author = iniText.value('author').encode('cp1252')#.encode due to encoding probs
        email = str(iniText.value('email'))
        homepage = str(iniText.value('homepage'))

        ABOUT_templatefile = os.path.join(os.sep,os.path.dirname(__file__),"about","about_template.htm")
        ABOUT_outputfile = os.path.join(os.sep,os.path.dirname(__file__),"about","about.htm")
        f_in = open(ABOUT_templatefile, 'r')
        f_out = open(ABOUT_outputfile, 'w')
        wholefile = f_in.read()
        changedfile = wholefile.replace('VERSIONCHANGETHIS',verno).replace('AUTHORCHANGETHIS',author).replace('EMAILCHANGETHIS',email).replace('HOMEPAGECHANGETHIS',homepage)
        f_out.write(changedfile)
        f_in.close()
        f_out.close()
        dlg = utils.HtmlDialog("About Midvatten plugin for QGIS",QUrl.fromLocalFile(ABOUT_outputfile))
        dlg.exec_()

    def aveflowcalculate(self):
        allcritical_layers = ('obs_points', 'w_flow') #none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        err_flag = utils.verify_layer_selection(err_flag,0)#verify the selected layer has attribute "obsid" and that some feature(s) is selected
        if err_flag == 0:     
            from w_flow_calc_aveflow import calcave
            dlg = calcave(self.iface.mainWindow()) 
            dlg.exec_()

    def drillreport(self):
        allcritical_layers = ('obs_points', 'w_levels', 'w_qual_lab')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        err_flag = utils.verify_layer_selection(err_flag,1)#verify the selected layer has attribute "obsid" and that exactly one feature is selected
        if err_flag == 0:
            obsid = utils.getselectedobjectnames(qgis.utils.iface.activeLayer())  # selected obs_point is now found in obsid[0]
            from drillreport import drillreport
            drillreport(obsid[0],self.ms.settingsdict)

    def export_csv(self):
        allcritical_layers = ('obs_points', 'obs_lines', 'w_levels','w_flow','w_qual_lab','w_qual_field','stratigraphy') #none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode

        if err_flag == 0:     
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))#show the user this may take a long time...

            #Get two lists (OBSID_P and OBSID_L) with selected obs_points and obs_lines
            obs_points_layer = utils.find_layer('obs_points')
            selected_obs_points = utils.getselectedobjectnames(obs_points_layer)
            obsidlist = []
            if len(selected_obs_points)>0:
                i=0
                for id in selected_obs_points:
                    obsidlist.append(str(id))#we cannot send unicode as string to sql because it would include the u'
                    i+=1
                OBSID_P = tuple(obsidlist)#because module midv_exporting depends on obsid being a tuple
            else:
                OBSID_P = tuple([])

            obs_lines_layer = utils.find_layer('obs_lines')
            selected_obs_lines = utils.getselectedobjectnames(obs_lines_layer)
            obsidlist = []
            if len(selected_obs_lines)>0:
                i=0
                for id in selected_obs_lines:
                    obsidlist.append(str(id))#we cannot send unicode as string to sql because it would include the u'
                    i+=1
                OBSID_L = tuple(obsidlist)#because module midv_exporting depends on obsid being a tuple
            else:
                OBSID_L = tuple([])

            #sanity = utils.askuser("YesNo","""You are about to export data for the selected obs_points and obs_lines into a set of csv files. \n\nContinue?""",'Are you sure?')
            #exportfolder =    QtGui.QFileDialog.getExistingDirectory(None, 'Select a folder:', 'C:\\', QtGui.QFileDialog.ShowDirsOnly)
            exportfolder = QFileDialog.getExistingDirectory(None, 'Select a folder where the csv files will be created:', '.',QFileDialog.ShowDirsOnly)
            if len(exportfolder) > 0:
                exportinstance = ExportData(OBSID_P, OBSID_L)
                exportinstance.export_2_csv(exportfolder)
                
            QApplication.restoreOverrideCursor()#now this long process is done and the cursor is back as normal

    def export_spatialite(self):
        allcritical_layers = ('obs_points', 'obs_lines', 'w_levels','w_flow','w_qual_lab','w_qual_field','stratigraphy') #none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:
            #Get two lists (OBSID_P and OBSID_L) with selected obs_points and obs_lines
            obs_points_layer = utils.find_layer('obs_points')
            selected_obs_points = utils.getselectedobjectnames(obs_points_layer)
            obsidlist = []
            if len(selected_obs_points)>0:
                i=0
                for id in selected_obs_points:
                    obsidlist.append(str(id))#we cannot send unicode as string to sql because it would include the u'
                    i+=1
                OBSID_P = tuple(obsidlist)#because module midv_exporting depends on obsid being a tuple
            else:
                OBSID_P = tuple([])

            obs_lines_layer = utils.find_layer('obs_lines')
            selected_obs_lines = utils.getselectedobjectnames(obs_lines_layer)
            obsidlist = []
            if len(selected_obs_lines)>0:
                i=0
                for id in selected_obs_lines:
                    obsidlist.append(str(id))#we cannot send unicode as string to sql because it would include the u'
                    i+=1
                OBSID_L = tuple(obsidlist)#because module midv_exporting depends on obsid being a tuple
            else:
                OBSID_L = tuple([])

            sanity = utils.askuser("YesNo","""Isto criara uma nova base de dados Midvatten vazia com design pre definido\ne completara a base de dados com os dados dos obs_points e obs_lines selecionados.\n\nContinuar?""",'Você tem certeza?')
            if sanity.result == 1:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))#show the user this may take a long time...
                obsp_layer = utils.find_layer('obs_points')
                CRS = obsp_layer.crs()
                EPSG_code = str(CRS.authid()[5:])
                filenamepath = os.path.join(os.path.dirname(__file__),"metadata.txt" )
                iniText = QSettings(filenamepath , QSettings.IniFormat)
                verno = str(iniText.value('version')) 
                from create_db import newdb
                newdbinstance = newdb(verno,'n',EPSG_code)#flag 'n' to avoid user selection of EPSG
                if not newdbinstance.dbpath=='':
                    newdb = newdbinstance.dbpath
                    exportinstance = ExportData(OBSID_P, OBSID_L)
                    exportinstance.export_2_splite(newdb,self.ms.settingsdict['database'],EPSG_code)
            
                QApplication.restoreOverrideCursor()#now this long process is done and the cursor is back as normal

    def import_obs_lines(self):
        allcritical_layers = ('obs_lines')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # unless none of the critical layers are in editing mode
            sanity = utils.askuser("YesNo","""Você está prestes a importar dados de linhas de observação de um arquivo de texto que deve conter uma linha de cabeçalho e 6 colunas (veja a página da web do plugin para explicações):\nWKT;obsid;nome;lugar;tipo;fonte\n\nNote que:\nDeve haver geometrias WKT do tipo LINESTRING na primeira coluna.\nA LINESTRING deve corresponder ao SRID na base de dados\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\nSeparados decimal deve ser ponto (.)\nVírgula ou ponto e vírgula não e permitido nos campos de texto.\nCampos vazios ou nulos não são permitidos para obsid e não devem haver obsid duplicados\n\nContinuar?""",'Você tem certeza?')
            #utils.pop_up_info(sanity.result)   #debugging
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.obslines_import()
                if importinstance.status=='True': 
                    self.iface.messageBar().pushMessage("Info","%s linhas de observacao foram importadas para a base de dados."%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_obs_points(self):
        allcritical_layers = ('obs_points')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # unless none of the critical layers are in editing mode
            sanity = utils.askuser("YesNo","""Você esta prestes a importar dados de pontos de observação de um arquivo de texto que deve conter uma linha de cabeçalho e 26 colunas (veja a página da web do plugin para explicações):\n\n1. obsid, 2. nome, 3. lugar, 4. tipo, 5. comprimento, 6. drillstop, 7. diam, 8. material, 9. screen, 10. capacidade, 11. data, 12. wmeas_yn, 13. wlogg_yn, 14. leste, 15. norte, 16. ne_accur, 17. ne_source, 18. a_bdp, 19. a_bdpgs, 20. h_gs, 21. a_acur, 22. a_syst, 23. a_fonte, 24. fonte, 25. com_onerow, 26. com_html\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\nO separador decimal deve ser ponto (.)\nVirgula ou ponto e vírgula não são permitidos nos campos de texto.\nCampos vazios ou nulos não são permitidos para obsid e não devem haver obsid duplicados\nCoordenados leste e norte devem corresponder ao SRID da base de dados.\n\nContinuar?""",'Você tem certeza?')
            #utils.pop_up_info(sanity.result)   #debugging
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.obsp_import()
                #utils.pop_up_info(returnvalue) #debugging
                #utils.pop_up_info(importinstance.status) #debugging
                if importinstance.status=='True':      # 
                    utils.pop_up_info("%s pontos de observacao foram importados para a base de dados.\nPara mostrar os pontos importados no mapa, selecione-os na\ntabela de atributos obs_points e então atualize a posição do mapa:\nMidvatten - Editar dados na base de dados - Atualizar a posição do mapa pelas coordenadas"%str(importinstance.recsafter - importinstance.recsbefore))
                    #self.iface.messageBar().pushMessage("Info","%s observation points were imported to the database.\nTo display the imported points on map, select them in\nthe obs_points attribute table then update map position:\nMidvatten - Edit data in database - Update map position from coordinates"%str(importinstance.recsafter - importinstance.recsbefore), 0)                    
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_seismics(self):
        allcritical_layers = ('obs_lines', 'seismic_data')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0: 
            sanity = utils.askuser("YesNo","""Você esta prestes a importar dados sísmicos interpretados de um arquivo de texto que deve conter uma linha de cabeçalho e 6 colunas:\n\nobsid, comprimento, ground, embasamento, gw_table, comentário\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\nO separador decimal deve ser ponto (.)\nCampo vazio ou nulo não é permitido para obsid ou comprimento.\nCada combinação de obsid e comprimento deve ser única.\n\nContinuar?""",'Você tem certeza?')
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.seismics_import()
                if importinstance.status=='True':  
                    self.iface.messageBar().pushMessage("Info","%s dados sísmicos interpretados foram importados para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_stratigraphy(self):
        allcritical_layers = ('obs_points', 'stratigraphy')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # unless none of the critical layers are in editing mode
            sanity = utils.askuser("YesNo","""Você está prestes a importar dados estratigráficos de um arquivo de texto que deve conter uma linha de cabeçalho e 9 colunas:\n1. obsid\n2. stratid - número inteiro comecando pela superfície e aumentando com a profundidade\n3. profundidade_topo - profundidade ate o topo da camada\n4. profundidade_base - profundidade ate a base da camada\n5. geologia - descricao completa da geologia da camada\n6. geoabrev - abreviacao para a geologia da camada (ver dicionario)\n7. capacidade\n8. development - well development\n9. comentário\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\nO separador decimal deve ser ponto (.)\nVírgula e ponto e vírgula não são permitidos nos comentários.\nCampos vazios ou nulos não são permitidos para obsid e stratid, tais campos serão excluídos da importação.\nCada combinação de obsid e stratid deve ser única.\n\nContinuar?""",'Você tem certeza?')
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.strat_import()
                if importinstance.status=='True':      # 
                    self.iface.messageBar().pushMessage("Info","%s camadas estratigráficas foram importadas para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_vlf(self):
        allcritical_layers = ('obs_lines', 'vlf_data')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # om ingen av de kritiska lagren är i editeringsmode
            sanity = utils.askuser("YesNo","""Você esta prester a importar dados vlf não tratados de um arquivo de texto que deve conter uma linha de cabeçalho e 5 colunas:\n\nobsid; comprimento; real_comp; imag_comp, comentário\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\nO separador decimal deve ser ponto (.)\nCampos vazios ou nulos não são permitidos para obsid e comprimento.\n Cada combinação de obsid e comprimento deve ser enica.\n\nContinuar?""",'Você tem certeza?')
            #utils.pop_up_info(sanity.result)   #debugging
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.vlf_import()
                if importinstance.status=='True': 
                    self.iface.messageBar().pushMessage("Info","%s valores vlf não tratados foram importados para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_wflow(self):
        allcritical_layers = ('obs_points', 'w_flow')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # om ingen av de kritiska lagren är i editeringsmode
            sanity = utils.askuser("YesNo","""Você está prestes a importar leituras de fluxo de água de um arquivo de texto que deve conter uma linha de cabeçalho e 7 colunas:\n\n1. obsid\n2. instrumentid\n3. tipofluxo\n4. data_hora\n5. leitura\n6. unidade\n7. comentário\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\ndata_hora deve ser no formato 'aaaa-mm-dd hh:mm(:ss)'.\nO separador decimal deve ser ponto (.)\nVírgula e ponto e vírgula não são permitidos nos comentários.\nCertifique-se de utilizar um número limitado de tipos de fluxo, pois todos serão adicionados a tabela zz_flowtype na base de dados durante a importação.\nCampos vazios ou nulos não são permitidos para obsid, instrumentid, tipofluxo ou data_hora.\nCada combinação de obsid, instrumentid, tipofluxo e data_hora deve ser anica.\n\nContinuar?""",'Você tem certeza?')
            #utils.pop_up_info(sanity.result)   #debugging
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.wflow_import()
                if importinstance.status=='True':      # 
                    self.iface.messageBar().pushMessage("Info","%s leituras de fluxo de água foram importadas para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_wlvl(self):    
        allcritical_layers = ('obs_points', 'w_levels')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:
            sanity = utils.askuser("YesNo","""Você esta prestes a importar leituras de nível de água de um arquivo de texto que deve conter uma linha de cabeçalho e 4 colunas:\n\nobsid;data_hora;leitu;comentário\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\ndata_hora deve ser no formato 'aaaa-mm-dd hh:mm(:ss)'.\nO separador decimal deve ser ponto (.)\nVírgula e ponto e vírgula não são permitidos nos comentários.\nCampos vazios ou nulos não são permitidos para obsid ou data_hora, tais linhas serão excluídas da importação.\nCampos vazios ou nulos não são aceitos ao mesmo tempo nas colunas leitu e comentário.\nCada combinaçao de obsid e data_hora deve ser única.\n\nContinuar?""",'Você tem certeza?')
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.wlvl_import()
                if importinstance.status=='True': 
                    self.iface.messageBar().pushMessage("Info","%s leituras de nível de água foram importadas para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_wlvllogg(self):#  - should be rewritten 
        allcritical_layers = ('obs_points', 'w_levels_logger')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:   
            if not (self.ms.settingsdict['database'] == ''):
                if qgis.utils.iface.activeLayer():
                    if utils.selection_check(qgis.utils.iface.activeLayer(),1) == 'ok':                
                        obsid = utils.getselectedobjectnames(qgis.utils.iface.activeLayer())                    
                        longmessage = """Você está prestes a importar dados de carga hidráulica registrados com um\nLevel Logger (e.g. Diver) """
                        longmessage += obsid[0]
                        longmessage +=u""".\nOs dados devem ser importados de um texto separado por\nvírgula ou ponto e vírgula. O arquivo deve conter uma linha de cabeçalho e as colunas:\n\nData/hora, Carga hidráulica[cm],Temperatura[°C]\nou\nData/hora,Carga hidráulica[cm],Temperatura[°C],1:Condutividade[mS/cm]\n\nO nome das colunas não é importante, embora a ordem seja.\nA coluna data-hora deve ser no formato aaaa-mm-dd hh:mm(:ss) e\nas outras colunas devem ser número reais com ponto(.) como separador decimal e sem separador de milhares.\nLembre-se de não utilizar virgulas no campo comentários!\n\nRegistros com qualquer campo vazio serão excluídos do relatório!\n\nContinuar?"""
                        sanity = utils.askuser("YesNo",utils.returnunicode(longmessage),'Você tem certeza?')
                        if sanity.result == 1:
                            from import_data_to_db import wlvlloggimportclass
                            importinstance = wlvlloggimportclass()
                            if not importinstance.status=='True':      
                                self.iface.messageBar().pushMessage("Atencao","Um erro ocorreu durante a importação", 1)
                            else:
                                try:
                                    self.midvsettingsdialog.ClearEverything()
                                    self.midvsettingsdialog.LoadAndSelectLastSettings()
                                except:
                                    pass                            
                else:
                    self.iface.messageBar().pushMessage("Crítico","Você deve selecionar a camada obs_points e o objeto (apenas um!) para o qual os dados do logger devem ser importados!", 2)
            else: 
                self.iface.messageBar().pushMessage("Verifique configurações","Você deve selecionar a base de dados primeiro!",2)

    def import_wqual_field(self):
        allcritical_layers = ('obs_points', 'w_qual_field')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # unless none of the critical layers are in editing mode
            sanity = utils.askuser("YesNo","""Você está prestes a importar dados de campo de qualidade da água de um arquivo de texto que deve conter uma linha de cabeçalho e as seguintes 10 colunas:\n\n1. obsid\n2. equipe\n3. data_hora - no formato aaaa-mm-dd hh:mm(:ss)\n4. instrumento\n5. parâmetro - nome do parâmetro de qualidade\n6. leitura_num - valor do param. (número real, separador decimal=ponto(.))\n7. leitura_txt - valor do parâmetro em texto, incluindo <, > etc\n8. unidade\n9. fluxo_lpm - fluxo em litros/minuto\n10. comentário - texto\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\ndata_hora deve ser no formato 'aaaa-mm-dd hh:mm(:ss)'.\nO separador decimal deve ser ponto (.)\nVírgula ou ponto e vírgula não são permitidos nos comentários.\nCampos vazios ou nulos não são permitidos para obsid, data_hora ou parâmetro, tais linhas serão excluídas da importação.\nCada combinação de obsid, data_hora e parâmetro deve ser única.\n\nContinuar?""",'Você tem certeza?')
            #utils.pop_up_info(sanity.result)   #debugging
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.wqualfield_import()
                if importinstance.status=='True':      # 
                    self.iface.messageBar().pushMessage("Info","%s parâmetros de qualidade da água foram importados para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_wqual_lab(self):
        allcritical_layers = ('obs_points', 'w_qual_lab')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        if err_flag == 0:        # unless none of the critical layers are in editing mode
            sanity = utils.askuser("YesNo","""Você este prestes a importar dados de laboratório de qualidade da água de um arquivo de texto que deve conter uma linha de cabeçalho e as seguintes 12 colunas:\n\n1. obsid - deve existir na tabela obs_points\n2. profundidade - profundidade da amostra (número real)\n3. relatório - cada par de relatório e parâmetro deve ser único!\n4. projeto\n5. equipe\n6. data_hora - no formato aaaa-mm-dd hh:mm(:ss)\n7. metodo_analise\n8. parâmetro - nome do parâmetro de qualidade\n9. leitura_num - valor do param. (número real, separador decimal=ponto(.))\n10. leitura_txt - valor do parâmetro como texto, incluindo<, > etc\n11. unidade\n12. comentário - texto, evite vírgula e ponto e vírgula\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\ndata_hora deve ser no formato 'aaaa-mm-dd hh:mm(:ss)'.\nO separador decimal deve ser ponto (.)\nVirgula ou ponto e vírgula não são permitidos nos comentários.\nCampos vazios ou nulos não são permitidos para obsid, relatório ou parâmetro, tais linhas serão excluídas da importação.\n Cada combinação de relatório e parâmetro deve ser única.\n\nContinuar?""",'Você tem certeza?')
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.wquallab_import()
                if importinstance.status=='True':      # 
                    self.iface.messageBar().pushMessage("Info","%s parâmetros de qualidade da água foram importados para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def import_meteo(self):
        allcritical_layers = ('obs_points')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode

        if (utils.sql_load_fr_db(r"""SELECT tbl_name FROM sqlite_master where tbl_name = 'meteo'""")[0]==True and len(utils.sql_load_fr_db(r"""SELECT tbl_name FROM sqlite_master where tbl_name = 'meteo'""")[1])==0) or (utils.sql_load_fr_db(r"""SELECT tbl_name FROM sqlite_master where tbl_name = 'meteo'""")[0]==False): #verify there actually is a meteo table (introduced in midv plugin version 1.1)
            err_flag += 1
            self.iface.messageBar().pushMessage("Erro","Não há tabela para dados metereológicos em sua base de dados! Sua base de dados deve ter sido criada em uma versão anterior do plugin Midvatten",2,duration=15)
        
        if err_flag == 0:        # unless none of the critical layers are in editing mode or the database is so old no meteo table exist
            sanity = utils.askuser("YesNo","""Você está prestes a importar dados metereológicos de um arquivo de texto que deve conter uma linha de cabeçalho e 8 colunas:\n\n"obsid", "instrumentid", "parâmetro", "data_hora", "leitura_num", "leitura_txt", "unidade", "comentário"\n\nNote que:\nO arquivo deve ser separado por vírgula ou ponto e vírgula.\ndata_hora deve ser no formato 'aaaa-mm-dd hh:mm(:ss)'.\nO separador decimal deve ser ponto (.)\nVírgula e ponto e vírgula não são permitidos nos comentários.\nCertifique-se de usar um número limitado de parâmetros, pois todos serão adicionados a tabela zz_meteoparam na base de dados durante a importação.\nCampos vazios ou nulos não são permitidos para obsid, instrumentid, parâmetro ou data_hora.\nCada combinação de obsid, instrumentid, parâmetro e data_hora deve ser única.\n\nContinuar?""",'Você tem certeza?')
            if sanity.result == 1:
                from import_data_to_db import midv_data_importer
                importinstance = midv_data_importer()
                importinstance.meteo_import()
                if importinstance.status=='True': 
                    self.iface.messageBar().pushMessage("Info","%s leituras metereologicas foram importadas para a base de dados"%str(importinstance.recsafter - importinstance.recsbefore), 0)
                    try:
                        self.midvsettingsdialog.ClearEverything()
                        self.midvsettingsdialog.LoadAndSelectLastSettings()
                    except:
                        pass

    def loadthelayers(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        if err_flag == 0:
            sanity = utils.askuser("YesNo","""Esta operação irá carregar as camadas padrão (com layout e símbolos pré-definidos, etc.) da sua base de dados selecionada para o seu projeto qgis.\n\nSe qualquer camada padrão Midvatten já estiver carregada em seu projeto qgis, elas serão excluidas.\n\nContinuar?""",'Atencao!')
            if sanity.result == 1:
                #show the user this may take a long time...
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                loadlayers(qgis.utils.iface, self.ms.settingsdict)
                QApplication.restoreOverrideCursor()#now this long process is done and the cursor is back as normal

    def new_db(self): 
        sanity = utils.askuser("YesNo","""Isto criara uma nova BD Midvatten\ncom design pre-definido.\n\nContinuar?""",'Você tem certeza?')
        if sanity.result == 1:
            filenamepath = os.path.join(os.path.dirname(__file__),"metadata.txt" )
            iniText = QSettings(filenamepath , QSettings.IniFormat)
            verno = str(iniText.value('version')) 
            from create_db import newdb
            newdbinstance = newdb(verno)
            if not newdbinstance.dbpath=='':
                db = newdbinstance.dbpath
                self.ms.settingsdict['database'] = db
                self.ms.save_settings()

    def plot_piper(self):
        allcritical_layers = ('w_qual_lab', 'w_qual_field')#none of these layers must be in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, allcritical_layers)#verify midv settings are loaded and the critical layers are not in editing mode
        err_flag = utils.verify_layer_selection(err_flag,0)#verify the selected layer has attribute "obsid" and that some features are selected
        if err_flag == 0:
            dlg = PiperPlot(self.ms,qgis.utils.iface.activeLayer())

    def plot_timeseries(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        err_flag = utils.verify_layer_selection(err_flag,0)#verify the selected layer has attribute "obsid" and that some features are selected
        if (self.ms.settingsdict['tstable'] =='' or self.ms.settingsdict['tscolumn'] == ''):
            err_flag += 1
            self.iface.messageBar().pushMessage("Erro","Por favor, configure a tabela serie temporal e coluna nas configurações Midvatten.", 2,duration =15)
        if err_flag == 0:
            dlg = TimeSeriesPlot(qgis.utils.iface.activeLayer(), self.ms.settingsdict)

    def plot_stratigraphy(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        err_flag = utils.verify_layer_selection(err_flag,0)#verify the selected layer has attribute "obsid" and that some features are selected
        if self.ms.settingsdict['stratigraphytable']=='':
            err_flag += 1
            self.iface.messageBar().pushMessage("Erro","Por favor, configure a tabela estratigrafia nas configurações Midvatten.", 2,duration =15)
        if err_flag == 0 and utils.strat_selection_check(qgis.utils.iface.activeLayer()) == 'ok':
            dlg = Stratigraphy(self.iface, qgis.utils.iface.activeLayer(), self.ms.settingsdict)
            dlg.showSurvey()
            self.dlg = dlg# only to prevent the Qdialog from closing.

    def plot_section(self):
        all_critical_layers=('obs_points')
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, all_critical_layers)#verify midv settings are loaded
        if not(err_flag == 0):
            self.iface.messageBar().pushMessage("Erro","Verifique as configurações Midvatten e certifique-se que a camada 'obs_points' não está no modo editar.", 2, duration=10)
            return

        SectionLineLayer = qgis.utils.iface.mapCanvas().currentLayer()#MUST BE LINE VECTOR LAYER WITH SAME EPSG as MIDV_OBSDB AND THERE MUST BE ONLY ONE SELECTED FEATURE
        msg = None
        if SectionLineLayer.selectedFeatureCount()==1:#First verify only one feature is selected in the active layer...
            for feat in SectionLineLayer.getFeatures():
                geom = feat.geometry()
                if geom.wkbType() == QGis.WKBLineString:#...and that the active layer is a line vector layer
                    pass
                else:
                    msg = 'Você deve ativar a camada vetor (linha) que define a seção.'
        else:
            msg = 'Você deve ativar a camada vetor (linha) e selecionar exatamente uma feição que define a seção'
        
        #Then verify that at least two feature is selected in obs_points layer, and get a list (OBSID) of selected obs_points
        obs_points_layer = utils.find_layer('obs_points')
        selectedobspoints = utils.getselectedobjectnames(obs_points_layer)
        obsidlist = []
        if len(selectedobspoints)>1:
            i=0
            for id in selectedobspoints:
                obsidlist.append(str(id))#we cannot send unicode as string to sql because it would include the u'
                i+=1
            OBSID = tuple(obsidlist)#because module sectionplot depends on obsid being a tuple
        else:
            msg = 'Você deve selecionar pelo menos dois objetos na camada obs_points'
        
        if msg:#if something went wrong
            self.iface.messageBar().pushMessage("Error",msg, 2,duration =15)
        else:#otherwise go
            try:
                self.myplot.do_it(self.ms,OBSID,SectionLineLayer)
            except:
                self.myplot = SectionPlot(self.iface.mainWindow(), self.iface)
                self.myplot.do_it(self.ms,OBSID,SectionLineLayer)

    def plot_xy(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        err_flag = utils.verify_layer_selection(err_flag,0)#verify the selected layer has attribute "obsid" and that some features are selected
        if (self.ms.settingsdict['xytable'] =='' or self.ms.settingsdict['xy_xcolumn'] == '' or (self.ms.settingsdict['xy_y1column'] == '' and self.ms.settingsdict['xy_y2column'] == '' and self.ms.settingsdict['xy_y3column'] == '')):
            err_flag += 1
            self.iface.messageBar().pushMessage("Erro","Por favor, configure a tabela xy series e colunas nas configurações Midvatten.", 2,duration =15)
        if err_flag == 0:
            dlg = XYPlot(qgis.utils.iface.activeLayer(), self.ms.settingsdict)

    def plot_sqlite(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        if not(err_flag == 0):
            return
        try:
            self.customplot.activateWindow()
        except:
            self.customplot = customplot.plotsqlitewindow(self.iface.mainWindow(), self.ms)#self.iface as arg?

    def prepare_layers_for_qgis2threejs(self):
        allcritical_layers = ('obs_points', 'stratigraphy')
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms,allcritical_layers)#verify midv settings are loaded
        if err_flag == 0:     
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))#show the user this may take a long time...
            PrepareForQgis2Threejs(qgis.utils.iface, self.ms.settingsdict)
            QApplication.restoreOverrideCursor()#now this long process is done and the cursor is back as normal

    def project_created(self):
        self.reset_settings()

    def project_opened(self):
        self.ms.reset_settings()
        self.ms.loadSettings()
        try:#if midvsettingsdock is shown, then it must be reloaded
            self.midvsettingsdialog.activateWindow()
            self.midvsettingsdialog.ClearEverything()
            self.midvsettingsdialog.LoadAndSelectLastSettings()
        except:
            pass

    def reset_settings(self):
        self.ms.reset_settings()
        self.ms.save_settings()
        try:#if midvsettingsdock is shown, then it must be reset
            self.midvsettingsdialog.activateWindow()
            self.midvsettingsdialog.ClearEverything()
        except:
            pass

    def setup(self):
        try:
            self.midvsettingsdialog.activateWindow()
        except:
            self.midvsettingsdialog = midvsettingsdialog.midvsettingsdialogdock(self.iface.mainWindow(),self.iface, self.ms)#self.iface as arg?

    def updatecoord(self):
        all_critical_layers=('obs_points')
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, all_critical_layers)#verify midv settings are loaded
        layername = 'obs_points'
        err_flag = utils.verify_this_layer_selected_and_not_in_edit_mode(err_flag, layername)
        if err_flag == 0:
            sanity = utils.askuser("AllSelected","""Você quer atualizar as coordenadas\npara Todos ou apenas objetos Selecionados?""")
            if sanity.result == 0:  #IF USER WANT ALL OBJECTS TO BE UPDATED
                sanity = utils.askuser("YesNo","""Sanity check! Isto ira alterar a base de dados.\nAs coordenadas serão adicionadas nos campos leste e norte\npara TODOS objetos na tabela obs_points.\nContinuar?""")
                if sanity.result==1:
                    ALL_OBS = utils.sql_load_fr_db("select distinct obsid from obs_points")[1]#a list of unicode strings is returned
                    observations = [None]*len(ALL_OBS)
                    i = 0
                    for obs in ALL_OBS:
                        observations[i] = obs[0]
                        i+=1
                    from coords_and_position import updatecoordinates
                    updatecoordinates(observations)
            elif sanity.result == 1:    #IF USER WANT ONLY SELECTED OBJECTS TO BE UPDATED
                sanity = utils.askuser("YesNo","""Sanity check! Isto ira alterar a base de dados.\nAs coordenadas serão adicionadas nos campos leste e norte\npara os objetos SELECIONADOS na tabela obs_points.\nContinuar?""")
                if sanity.result==1:
                    layer = self.iface.activeLayer()
                    if utils.selection_check(layer) == 'ok':    #Checks that there are some objects selected at all!
                        observations = utils.getselectedobjectnames(layer)#a list of unicode strings is returned
                        from coords_and_position import updatecoordinates
                        updatecoordinates(observations)

    def updateposition(self):
        all_critical_layers=('obs_points')
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms, all_critical_layers)#verify midv settings are loaded
        layername = 'obs_points'
        err_flag = utils.verify_this_layer_selected_and_not_in_edit_mode(err_flag, layername)
        if err_flag == 0:
            layer = self.iface.activeLayer()
            sanity = utils.askuser("AllSelected","""Você quer atualizar a posição\npara TODOS objetos ou apenas Selecionados?""")
            if sanity.result == 0:      #IF USER WANT ALL OBJECTS TO BE UPDATED
                sanity = utils.askuser("YesNo","""Sanity check! Isto ira alterar a base de dados\nTODOS objetos em obs_points serão movidos para a posição\ndada pelas coordenadas nos campos leste e norte.\nContinuar?""")
                if sanity.result==1:
                    ALL_OBS = utils.sql_load_fr_db("select distinct obsid from obs_points")[1]
                    observations = [None]*len(ALL_OBS)
                    i = 0
                    for obs in ALL_OBS:
                        observations[i] = obs[0]
                        i+=1
                    from coords_and_position import updateposition
                    updateposition(observations)
                    layer.updateExtents()
            elif sanity.result == 1:    #IF USER WANT ONLY SELECTED OBJECTS TO BE UPDATED
                sanity = utils.askuser("YesNo","""Sanity check! Isto ira alterar a base de dados.\nObjetos selecionados em obs_points serão movidos para a posição\ndada pelas coordenadas nos campos leste e norte.\nContinuar?""")
                if sanity.result==1:
                    if utils.selection_check(layer) == 'ok':    #Checks that there are some objects selected at all!
                        observations = utils.getselectedobjectnames(layer)
                        from coords_and_position import updateposition
                        updateposition(observations)
                        layer.updateExtents()

    def vacuum_db(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        if err_flag == 0:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            utils.sql_alter_db('vacuum')
            QApplication.restoreOverrideCursor()

    def waterqualityreport(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        err_flag = utils.verify_layer_selection(err_flag)#verify the selected layer has attribute "obsid" and that some feature(s) is selected
        if self.ms.settingsdict['database'] == '' or self.ms.settingsdict['wqualtable']=='' or self.ms.settingsdict['wqual_paramcolumn']=='' or self.ms.settingsdict['wqual_valuecolumn']=='':
            err_flag += 1
            self.iface.messageBar().pushMessage("Erro","Cheque as configurações Midvatten. \nAlgo está errado na aba 'W quality report'!", 2,duration =15)
        if err_flag == 0:
            fail = 0
            for k in utils.getselectedobjectnames(qgis.utils.iface.activeLayer()):#all selected objects
                if not utils.sql_load_fr_db("select obsid from %s where obsid = '%s'"%(self.ms.settingsdict['wqualtable'],str(k)))[1]:#if there is a selected object without water quality data
                    self.iface.messageBar().pushMessage("Erro","Sem dados de qualidade da água para %s"%str(k), 2)
                    fail = 1
            if not fail == 1:#only if all objects has data
                wqualreport(qgis.utils.iface.activeLayer(),self.ms.settingsdict)#TEMPORARY FOR GVAB

    def wlvlcalculate(self):
        allcritical_layers = ('obs_points', 'w_levels')     #Check that none of these layers are in editing mode
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms,allcritical_layers)#verify midv settings are loaded
        layername='obs_points'
        err_flag = utils.verify_this_layer_selected_and_not_in_edit_mode(err_flag,layername)#verify selected layername and not in edit mode
        if err_flag == 0:
            from wlevels_calc_calibr import calclvl
            dlg = calclvl(self.iface.mainWindow(),qgis.utils.iface.activeLayer())  # dock is an instance of calibrlogger
            dlg.exec_()

    def wlvlloggcalibrate(self):
        allcritical_layers = ('w_levels_logger', 'w_levels')
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms,allcritical_layers)#verify midv settings are loaded
        if err_flag == 0:
            from wlevels_calc_calibr import calibrlogger
            try:
                self.calibrplot.activateWindow()
            except:
                self.calibrplot = calibrlogger(self.iface.mainWindow(), self.ms.settingsdict)#,obsid)

    def zip_db(self):
        err_flag = utils.verify_msettings_loaded_and_layer_edit_mode(self.iface, self.ms)#verify midv settings are loaded
        if err_flag == 0:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            connection = utils.dbconnection()
            connection.connect2db()
            connection.conn.cursor().execute("begin immediate")
            bkupname = self.ms.settingsdict['database'] + datetime.datetime.now().strftime('%Y%m%dT%H%M') + '.zip'
            zf = zipfile.ZipFile(bkupname, mode='w')
            zf.write(self.ms.settingsdict['database'], compress_type=compression) #compression will depend on if zlib is found or not
            zf.close()
            connection.conn.rollback()
            connection.closedb()
            self.iface.messageBar().pushMessage("Information","Database backup was written to " + bkupname, 1,duration=15)
            QApplication.restoreOverrideCursor()

