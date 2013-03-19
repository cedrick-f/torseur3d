#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of Torseur3D
#############################################################################
#############################################################################
##                                                                         ##
##                                   Options                               ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2012 Cédrick FAURY

#    Torseur3D is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
    
#    Torseur3D is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Torseur3D; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
Options.py
Gestion des "options" pout le logiciel Torseur3D
Copyright (C) 2009 Cédrick FAURY

"""

import ConfigParser
import os.path
#import wx

#import globdef
from widgets import VariableCtrl, Variable, VAR_REEL, EVT_VAR_CTRL, VAR_ENTIER_POS, VAR_REEL_POS
import wx.combo
#import Images

##############################################################################
#      Options     #
##############################################################################
class Options:
    """ Définit les options de PySyLic """
    def __init__(self, options = None):
        #
        # Toutes les options sous forme de dictionnaires ...
        #
        self.optAffichage = {}
        self.optGenerales = {}
        self.optCalibration = {}
          
#        self.listeOptions = [u"Général", u"Affichage", u"Couleurs", u"Impression"] 
         
        self.typesOptions = {u"Général" : self.optGenerales,
                             u"Affichage" : self.optAffichage,
                             u"Acquisition" : self.optCalibration,
                             }
        
        # Le fichier où seront sauvées les options
        self.fichierOpt = "torseur3D.cfg"

    #########################################################################################################
    def __repr__(self):
        t = "Options :\n"
        for o in self.optGenerales.items() + self.optAffichage.items()+ self.optCalibration.items():
            if type(o[1]) == int or type(o[1]) == float:
                tt = str(o[1])
            elif type(o[1]) == bool:
                tt = str(o[1])
            else:
                tt = o[1]
            t += "\t" + o[0] + " = " + tt +"\n"
        return t
    
    
    #########################################################################################################
    def fichierExiste(self):
        """ Vérifie si le fichier 'options' existe
        """
#        PATH=os.path.dirname(os.path.abspath(sys.argv[0]))
#        os.chdir(globdef.PATH)
        if os.path.isfile(self.fichierOpt):
            return True
        return False

    #########################################################################################################
    def enregistrer(self):
        """" Enregistre les options dans un fichier
        """
#        print "Enregistrement",self
        config = ConfigParser.ConfigParser()

        for titre,dicopt in self.typesOptions.items():
            titre = titre.encode('utf-8')
            config.add_section(titre)
            for opt in dicopt.items():
                config.set(titre, opt[0],opt[1])
        
        config.write(open(self.fichierOpt,'w'))



    ############################################################################
    def ouvrir(self):
        """ Ouvre un fichier d'options 
        """
        config = ConfigParser.ConfigParser()
        config.read(self.fichierOpt)
        print "ouverture :",self.fichierOpt
        print self.typesOptions.keys()
        for titre in self.typesOptions.keys():
            titreUtf = titre.encode('utf-8')
            print titre
            for titreopt in self.typesOptions[titre].keys():
                opt = self.typesOptions[titre][titreopt] 
                print opt
                if type(opt) == int:
                    opt = config.getint(titreUtf, titreopt)
                elif type(opt) == float:
                    opt = config.getfloat(titreUtf, titreopt)
                elif type(opt) == bool:
                    opt = config.getboolean(titreUtf, titreopt)
                elif type(opt) == str or type(opt) == unicode:
                    opt = config.get(titreUtf, titreopt)
                elif isinstance(opt, wx._gdi.Colour):
                    v = eval(config.get(titreUtf, titreopt))
                    opt = wx.Colour(v[0], v[1], v[2], v[3])
                    
                
                # pour un passage correct de la version 2.5 à 2.6
                try:
                    v = eval(opt)
                    if type(v) == tuple:
                        opt = wx.Colour(v[0], v[1], v[2]).GetAsString(wx.C2S_HTML_SYNTAX)
                    print "  ", opt
                except:
                    pass
                
                self.typesOptions[titre][titreopt] = opt
                
                
        


    ############################################################################
    def copie(self):
        """ Retourne une copie des options """
        options = Options()
        for titre,dicopt in self.typesOptions.items():
            titre.encode('utf-8')
            for opt in dicopt.items():
                options.typesOptions[titre][opt[0]] = opt[1]
        return options
    

    ###########################################################################
    def extraireRepertoire(self,chemin):
        for i in range(len(chemin)):
            if chemin[i] == "/":
                p = i
        self.repertoireCourant = chemin[:p+1]
        return chemin[:p+1]
        
        
##############################################################################
#     Fenêtre Options     #
##############################################################################
class FenOptions(wx.Dialog):
#   "Fenêtre des options"      
    def __init__(self, parent, options):
        wx.Dialog.__init__(self, parent, -1, u"Options")#, style = wx.RESIZE_BORDER)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.options = options
        self.parent = parent
        
        #
        # Tous les panel des options
        #
        self.panelOptions = {u"Général" : pnlGenerales,
                             u"Affichage" : pnlAffichage,
                             u"Acquisition" : pnlCalibration,
                             }
        #
        # Le book ...
        #
        nb = wx.Notebook(self, -1)
        for nomOpt  in [u"Général", u"Affichage", u"Acquisition"]:
            dicOpt = options.typesOptions[nomOpt]
            pnlOpt = self.panelOptions[nomOpt]
            nb.AddPage(pnlOpt(nb, dicOpt), nomOpt)

        nb.SetMinSize((400,-1))
        sizer.Add(nb, flag = wx.EXPAND)#|wx.ALL)
        self.nb = nb
        
        #
        # Les boutons ...
        #
        btnsizer = wx.StdDialogButtonSizer()
        
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_OK)
        help = u"Valider les changements apportés aux options"
        btn.SetToolTip(wx.ToolTip(help))
        btn.SetHelpText(help)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        help = u"Annuler les changements et garder les options comme auparavant"
        btn.SetToolTip(wx.ToolTip(help))
        btn.SetHelpText(help)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        
        btn = wx.Button(self, -1, u"Défaut")
        help = u"Rétablir les options par défaut"
        btn.SetToolTip(wx.ToolTip(help))
        btn.SetHelpText(help)
        self.Bind(wx.EVT_BUTTON, self.OnClick, btn)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer.Add(btn)
        bsizer.Add(btnsizer, flag = wx.EXPAND|wx.ALIGN_RIGHT)
        
        sizer.Add(bsizer, flag = wx.EXPAND)#|wx.ALL)
        self.SetMinSize((400,-1))
#        print self.GetMinSize()
#        self.SetSize(self.GetMinSize())
        self.SetSizerAndFit(sizer)
        
        
    def OnClick(self, event):
        self.options.defaut()
        
        for np in range(self.nb.GetPageCount()):
            
            p = self.nb.GetPage(np)
#            print "   ",p
            for c in p.GetChildren():
#                print c
                c.Destroy()
#            p.DestroyChildren()
#            print p.GetSizer().GetChildren()
            p.CreatePanel()
            p.Layout()
        
        
        
#############################################################################################################
class pnlGenerales(wx.Panel):
    def __init__(self, parent, opt):
        
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = opt
        
        self.CreatePanel()
    
    
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        
        #
        # Option "Type de mode démo"
        #
        rb1 = wx.RadioBox(self, -1, u"Mode d'acquisition", wx.DefaultPosition, wx.DefaultSize,
                          [u"Démo (aléatoire)",u"Manuel", u"Banc \"Torseur 3D (JEULIN)\""],#, u"Arduino"], 
                          1, wx.RA_SPECIFY_COLS)
        rb1.SetToolTipString(u"Choix du mode d'acquisition des composantes du torseur :\n" \
                             u"\tDémo = variation aléatoire\n" \
                             u"\tManuel = saisie manuel\n")
        rb1.SetSelection(self.opt["TypeDemo"])

        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb1)
        self.ns.Add(rb1, flag = wx.EXPAND|wx.ALL)

      
        #
        # Pas de modification torseur
        #
        sb3 = wx.StaticBox(self, -1, u"Pas de modification", size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        self.ncp = Variable(u'Résultante', 
                            lstVal = self.opt["PAS_R"], modeLog = False ,
                            typ = VAR_REEL, bornes = [0.1,1.0])
        vc1 = VariableCtrl(self, self.ncp, coef = 0.01, labelMPL = False, signeEgal = False,
                          help = u"Pas (en N) de modification des composantes de résultantes (pour saisie manuelle)"
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableR, vc1)
        self.ncp = Variable(u'Moment', 
                            lstVal = self.opt["PAS_M"], modeLog = False,
                            typ = VAR_REEL, bornes = [0.01,0.1])
        vc2 = VariableCtrl(self, self.ncp, coef = 0.001, labelMPL = False, signeEgal = False,
                          help = u"Pas (en Nm) de modification des composantes de moment (pour saisie manuelle)"
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableM, vc2)
        sbs3.Add(vc1, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs3.Add(vc2, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
#        
        self.SetSizerAndFit(self.ns)
    
    
    
    def EvtComboBox(self, event):
        cb = event.GetEventObject()
#        data = GetClientData(event.GetSelection())
#        data = cb.GetValue()
#        name = cb.GetName()
        self.opt["PORT"] = cb.GetValue()
#        if name == "VAR_COMPLEXE":
#            self.opt["VAR_COMPLEXE"] = data
#        elif name == "TEMPS_REPONSE":
#            self.opt["TEMPS_REPONSE"] = float(eval(data.strip("%")))/100
#        else:
#            num = event.GetSelection()
#            self.opt["LANG"] = self.nom_langues[0][num]
            
    
    def EvtRadioBox(self, event):
        self.opt["TypeDemo"] = event.GetInt()
        
    def EvtComboCtrl(self, event):
        self.opt["RepCourant"] = event.GetEventObject().GetValue()
        
    def EvtCheckBoxM(self, event):
        self.opt["MAJ_AUTO"] = event.GetEventObject().GetValue()
    
    def EvtCheckBoxD(self, event):
        self.opt["DEPHASAGE"] = event.GetEventObject().GetValue()
        
    def EvtVariableR(self, event):
        self.opt["PAS_R"] = event.GetVar().v[0]
        
    def EvtVariableM(self, event):
        self.opt["PAS_M"] = event.GetVar().v[0]



#############################################################################################################
class pnlCalibration(wx.Panel):
    def __init__(self, parent, opt):
        
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = opt
        
        self.CreatePanel()
    
        
    
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        
        #
        # Port
        #
        sb3 = wx.StaticBox(self, -1, u"Communication", size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        
        # Option VAR_COMPLEXE
        hs = wx.BoxSizer(wx.HORIZONTAL)
        ttr = wx.StaticText(self, -1, u"Nom du port série")
        cb = wx.ComboBox(self, -1, self.opt["PORT"], size = (60, -1), 
                         choices = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9'],
                         style = wx.CB_DROPDOWN|wx.CB_READONLY ,
                         name = "")
        cb.SetToolTipString(u"Port série sur lequel est relié le capteur")
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        hs.Add(ttr, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        hs.Add(cb, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        sbs3.Add(hs, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        #
        # Coefficients
        #
        sb2 = wx.StaticBox(self, -1, u"Coefficients", size = (200,-1))
        sbs2 = wx.StaticBoxSizer(sb2,wx.VERTICAL)
        self.cr = Variable(u'Coefficient "Résultante"', 
                            lstVal = self.opt["Coef_R"], 
                            typ = VAR_REEL, bornes = [0.1,0.2])
        vcr = VariableCtrl(self, self.cr, coef = 1, labelMPL = False, signeEgal = False,
                          help = u"Coefficients de conversion \"données capteur\"/\"force\"\n" \
                            u"à régler pour l'étalonnage du capteur.")
   
        self.Bind(EVT_VAR_CTRL, self.EvtVariableR, vcr)
        
        self.cm = Variable(u'Coefficient "Moment"', 
                            lstVal = self.opt["Coef_M"], 
                            typ = VAR_REEL, bornes = [0.01,0.02])
        vcm = VariableCtrl(self, self.cm, coef = 1, labelMPL = False, signeEgal = False,
                          help = u"Coefficients de conversion \"données capteur\"/\"moment\"\n" \
                            u"à régler pour l'étalonnage du capteur.")
        self.Bind(EVT_VAR_CTRL, self.EvtVariableM, vcm)
        
    
        sbs2.Add(vcr, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs2.Add(vcm, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.ns.Add(sbs2, flag = wx.EXPAND|wx.ALL)
        
        self.SetSizerAndFit(self.ns)
    
    def EvtComboBox(self, event):
        cb = event.GetEventObject()
#        data = GetClientData(event.GetSelection())
        data = cb.GetValue()
        name = cb.GetName()
        if name == "VAR_COMPLEXE":
            self.opt["VAR_COMPLEXE"] = data
        elif name == "TEMPS_REPONSE":
            self.opt["TEMPS_REPONSE"] = float(eval(data.strip("%")))/100
        else:
            num = event.GetSelection()
            self.opt["PORT"] = data #self.nom_langues[0][num]
            
    
    def EvtRadioBox(self, event):
        self.opt["TypeSelecteur"] = event.GetInt()
        
    def EvtComboCtrl(self, event):
        self.opt["RepCourant"] = event.GetEventObject().GetValue()
        
    def EvtCheckBox(self, event):
        self.opt["MAJ_AUTO"] = event.GetEventObject().GetValue()
        
    def EvtVariableR(self, event):
        self.opt["Coef_R"] = event.GetVar().v[0]
        
    def EvtVariableM(self, event):
        self.opt["Coef_M"] = event.GetVar().v[0]

    

#    def EvtCheckBoxOnglet(self, event):
#        dlg = wx.MessageDialog(self, u"L'option ne sera effective qu'au redémarrage de l'application",
#                               u'Option "Arbre de structure"',
#                               wx.OK | wx.ICON_INFORMATION
#                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
#                               )
#        dlg.ShowModal()
#        dlg.Destroy()
#        self.opt["OngletMontage"] = event.GetEventObject().GetValue()
#        
#    def EvtCheckBoxHachurer(self, event):
#        self.opt["Hachurer"] = event.GetEventObject().GetValue()

#######################################################################################################
class pnlAffichage(wx.Panel):
    def __init__(self, parent, optAffichage):
        
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = optAffichage
        
        
        
        self.CreatePanel()
        
        
       
       
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        
        #
        # Taille des polices
        #
        sb3 = wx.StaticBox(self, -1, u"Tailles des polices", size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        self.ncp = Variable(u'Vecteurs', 
                            lstVal = self.opt["TAILLE_VECTEUR"], 
                            typ = VAR_ENTIER_POS, bornes = [10,30])
        vc1 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableV, vc1)
        self.ncp = Variable(u'Points', 
                            lstVal = self.opt["TAILLE_POINT"], 
                            typ = VAR_ENTIER_POS, bornes = [10,30])
        vc2 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableP, vc2)
        
        self.ncp = Variable(u'Composantes', 
                            lstVal = self.opt["TAILLE_COMPOSANTES"], 
                            typ = VAR_ENTIER_POS, bornes = [6,15])
        vc3 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableC, vc3)
        
        sbs3.Add(vc1, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs3.Add(vc2, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs3.Add(vc3, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        
        #
        # Echelles des vecteurs
        #
        sb3 = wx.StaticBox(self, -1, u"Echelles des vecteurs", size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        self.ncp = Variable(u'Résultante (mm/N)', 
                            lstVal = self.opt["ECHELLE_R"], 
                            typ = VAR_REEL_POS, bornes = [5,50], modeLog = False)
        vc1 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableR, vc1)
        self.ncp = Variable(u'Moment (mm/Nm)', 
                            lstVal = self.opt["ECHELLE_M"], 
                            typ = VAR_REEL_POS, bornes = [50,500], modeLog = False)
        vc2 = VariableCtrl(self, self.ncp, coef = 10, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariableM, vc2)
        
        sbs3.Add(vc1, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs3.Add(vc2, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        
        #
        # Precision des valeurs de composantes
        #
        sb3 = wx.StaticBox(self, -1, u"Precision des valeurs de composantes", size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        self.ncp = Variable(u'Résultante', 
                            lstVal = self.opt["PRECISION_R"], 
                            typ = VAR_REEL_POS, bornes = [0,2], modeLog = False)
        vc1 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariablePR, vc1)
        self.ncp = Variable(u'Moment', 
                            lstVal = self.opt["PRECISION_M"], 
                            typ = VAR_REEL_POS, bornes = [1,3], modeLog = False)
        vc2 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = ""
                          )
        self.Bind(EVT_VAR_CTRL, self.EvtVariablePM, vc2)
        
        sbs3.Add(vc1, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs3.Add(vc2, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)

        self.SetSizerAndFit(self.ns)
        
    
    def OnRadio(self, event):
        radio = event.GetId() - 100
        self.opt["FONT_TYPE"] = radio
         
    def OnVariableModified(self, event):
#        print "NBR_PTS_REPONSE 1", self.npr.v[0]
        self.opt["NBR_PTS_REPONSE"] = self.npr.v[0]
        
    
    def EvtCheckBox(self, event):
        self.opt["ANTIALIASED"] = event.IsChecked()
        
    def EvtVariableV(self, event):
        self.opt["TAILLE_VECTEUR"] = event.GetVar().v[0]
        
    def EvtVariableP(self, event):
        self.opt["TAILLE_POINT"] = event.GetVar().v[0]
        
    def EvtVariableC(self, event):
        self.opt["TAILLE_COMPOSANTES"] = event.GetVar().v[0]  
        
    def EvtVariableR(self, event):
        self.opt["ECHELLE_R"] = event.GetVar().v[0]
        
    def EvtVariableM(self, event):
        self.opt["ECHELLE_M"] = event.GetVar().v[0]  
        
    def EvtVariablePR(self, event):
        self.opt["PRECISION_R"] = event.GetVar().v[0]
        
    def EvtVariablePM(self, event):
        self.opt["PRECISION_M"] = event.GetVar().v[0]
          


#############################################################################################################
class pnlImpression(wx.Panel):
    def __init__(self, parent, opt):
        
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = opt
        
        
        
        self.CreatePanel()
        
        
        
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        #
        # Mise en page
        #
        sb1 = wx.StaticBox(self, -1, _(u"Mise en page"), size = (200,-1))
        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
        cb2 = wx.CheckBox(self, -1, _(u"Garder les proportions de l'écran"))
        cb2.SetToolTip(wx.ToolTip(_(u"Si cette case est cochée, les tracés imprimés\n"\
                                    u"auront les mêmes proportions (largeur/hauteur) qu'à l'écran.")))
        cb2.SetValue(self.opt["PRINT_PROPORTION"])
        sbs1.Add(cb2, flag = wx.EXPAND|wx.ALL, border = 5)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb2)
        self.ns.Add(sbs1, flag = wx.EXPAND|wx.ALL)
        
        #
        # Elements à imprimer
        #
        sb2 = wx.StaticBox(self, -1, _(u"Eléments à imprimer"), size = (200,-1))
        sbs2 = wx.StaticBoxSizer(sb2,wx.VERTICAL)
        sup = u"\n"+_(u"En décochant cette case, vous pouvez choisir un texte personnalisé")
        selTitre = selecteurTexteEtPosition(self, _(u"Nom du fichier système"),
                                            self.Parent.Parent.Parent.fichierCourant,
                                            _(u"Nom de fichier sous lequel le système actuel est sauvegardé")+sup,
                                            "IMPRIMER_TITRE", "POSITION_TITRE", "TEXTE_TITRE")
        selNom = selecteurTexteEtPosition(self, _(u"Nom de l'utilisateur"),
                                            globdef.NOM,
                                            _(u"Nom de l'utilisateur de l'ordinateur")+sup,
                                            "IMPRIMER_NOM", "POSITION_NOM", "TEXTE_NOM")
        sbs2.Add(selTitre, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs2.Add(selNom, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs2, flag = wx.EXPAND|wx.ALL)
        
        #
        # Qualité de l'impression
        #
        sb3 = wx.StaticBox(self, -1, _(u"Qualité de l'impression"), size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        ttr = wx.StaticText(self, -1, _(u"Résolution de l'impression :"))
        cb = wx.ComboBox(self, -1, str(self.opt["MAX_PRINTER_DPI"]), size = (80, -1), 
                         choices = ['100', '200', '300', '400', '500', '600'],
                         style = wx.CB_DROPDOWN|wx.CB_READONLY)
        help = _(u"Ajuster la résolution de l'impression.\n"\
                 u"Attention, une résolution trop élevée peut augmenter\n"\
                 u"significativement la durée de l'impression.")
        cb.SetToolTipString(help)
        ttr.SetToolTipString(help)
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        hs.Add(ttr, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        hs.Add(cb, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        sbs3.Add(hs, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        self.SetSizerAndFit(self.ns)
    
    def EvtComboBox(self, event):
        cb = event.GetEventObject()
        data = cb.GetValue()
        self.opt["MAX_PRINTER_DPI"] = eval(data)
        
    def EvtCheckBox(self, event):
        self.opt["PRINT_PROPORTION"] = event.GetEventObject().GetValue()
        


class selecteurTexteEtPosition(wx.Panel):
    def __init__(self, parent, titre, textedefaut, tooltip, impoption, posoption, txtoption, ctrl = True):
        wx.Panel.__init__(self, parent, -1)
        
        self.impoption = impoption
        self.posoption = posoption
        self.txtoption = txtoption
        self.textedefaut = textedefaut
        
        self.lstPos = ["TL","TC","TR","BL","BC","BR"]
        tooltips = [_(u"En haut à gauche"), _(u"En haut au centre"), _(u"En haut à droite"),
                   _(u"En bas à gauche"), _(u"En bas au centre"), _(u"En bas à droite")]
        #
        # Le titre
        #
        self.titre = wx.CheckBox(self, -1, titre)
        self.titre.SetValue(self.Parent.opt[self.impoption])
        self.titre.SetToolTip(wx.ToolTip(tooltip))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.titre)
        
        #
        # Le texte à afficher
        #
        if not self.Parent.opt[self.impoption]:
            txt = self.Parent.opt[self.txtoption]
        else:
            txt = self.textedefaut
            
        if ctrl:
            print self.Parent.opt[self.txtoption]
            self.texte = wx.TextCtrl(self, -1, txt)
            self.Bind(wx.EVT_TEXT, self.EvtText, self.texte)
        else:
            self.texte = wx.StaticText(self, -1, txt)
        self.texte.Enable(not self.Parent.opt[self.impoption])
            
        #
        # La position
        #
        radio = []
        box1_title = wx.StaticBox(self, -1, _(u"position") )
        box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
        grid1 = wx.BoxSizer(wx.HORIZONTAL)
        radio.append(wx.RadioButton(self, 101, "", style = wx.RB_GROUP ))
        radio.append(wx.RadioButton(self, 102, "" ))
        radio.append(wx.RadioButton(self, 103, "" ))
        for r in radio:
            grid1.Add(r)
        box1.Add(grid1)
        
        img = wx.StaticBitmap(self, -1, Images.Zone_Impression.GetBitmap())
        img.SetToolTip(wx.ToolTip(_(u"Choisir ici la position du texte par rapport aux tracés")))
        box1.Add(img)
        
        grid2 = wx.BoxSizer(wx.HORIZONTAL)
        radio.append(wx.RadioButton(self, 104, "" ))
        radio.append(wx.RadioButton(self, 105, "" ))
        radio.append(wx.RadioButton(self, 106, "" ))
        for r in radio[3:]:
            grid2.Add(r)
        box1.Add(grid2)
        
        for i, r in enumerate(radio):
            r.SetToolTip(wx.ToolTip(tooltips[i]))
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, r)
        
        self.radio = self.lstPos.index(self.Parent.opt[self.posoption])
        for i, r in enumerate(radio):
            if i == self.radio:
                r.SetValue(True)
            else:
                r.SetValue(False)
        
#        sizerV = wx.BoxSizer(wx.VERTICAL)
#        sizerV.Add(box1)
#        sizerV.Add(img)
#        sizerV.Add(box2)
        
#        posList = [" "," "," "," "," "," "]
#        rb = wx.RadioBox(self, -1, _(u"position"), wx.DefaultPosition, wx.DefaultSize,
#                         posList, 2, wx.RA_SPECIFY_ROWS)
#        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)
#        try:
#            rb.SetSelection(self.lstPos.index(self.Parent.opt[self.posoption]))
#        except:
#            pass
#        self.rb = rb
#        self.rb.Enable(self.titre.GetValue())
        
        
        #
        # Mise en place
        #
        sizerG = wx.BoxSizer(wx.VERTICAL)
        sizerG.Add(self.titre, flag = wx.EXPAND)
        sizerG.Add(self.texte, flag = wx.EXPAND|wx.ALL, border = 15)
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(sizerG, 1, flag = wx.EXPAND)
        self.sizer.Add(box1, flag = wx.EXPAND|wx.ALIGN_LEFT)
        self.SetSizer(self.sizer)
        self.sizer.Fit( self )
        
    def OnRadio(self, event):
        self.radio = event.GetId()-101
        self.Parent.opt[self.posoption] = self.lstPos[self.radio]
#        print self.radio
    
#    def EvtRadioBox(self, event):
#        p = event.GetInt()
#        self.Parent.opt[self.posoption] = self.lstPos[p]
        
    def EvtText(self, event):
        txt = event.GetString()
        self.Parent.opt[self.txtoption] = txt
        
    def EvtCheckBox(self, event):
        self.Parent.opt[self.impoption] = event.GetEventObject().GetValue()
        self.texte.Enable(not self.Parent.opt[self.impoption])
        
#        self.Parent.opt[self.posoption] = self.lstPos[self.radio]
        
    
        if not self.Parent.opt[self.impoption]:
            self.Parent.opt[self.txtoption] = self.texte.GetValue()
            self.texte.SetValue(self.Parent.opt[self.txtoption])    
        else:
            self.texte.SetValue(self.textedefaut)
            self.Parent.opt[self.txtoption] = ""
            
        
#        self.rb.Enable(event.GetEventObject().GetValue())
            
#class pnlImpression(wx.Panel):
#    def __init__(self, parent, opt):
#        wx.Panel.__init__(self, parent, -1)
#        ns = wx.BoxSizer(wx.VERTICAL)
#        self.opt = opt
#        
#        sb1 = wx.StaticBox(self, -1, u"Contenu du rapport", size = (200,-1))
#        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
#        tree = ChoixRapportTreeCtrl(self, self.opt)
#        sbs1.Add(tree, flag = wx.EXPAND|wx.ALL, border = 5)
#        
##        print tree.GetVirtualSize()[1], tree.GetBestSize()[1]
#        
#        cb2 = wx.CheckBox(self, -1, u"Demander ce qu'il faut inclure à chaque création de rapport")
#        cb2.SetValue(self.opt["DemanderImpr"])
#        
#        sbs1.Add(cb2, flag = wx.EXPAND|wx.ALL, border = 5)
#        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb2)
#        
#        ns.Add(sbs1, flag = wx.EXPAND|wx.ALL)
#        self.SetSizerAndFit(ns)
#        sb1.SetMinSize((-1, 130))
#        
##    def EvtComboCtrl(self, event):
##        self.opt["FichierMod"] = event.GetEventObject().GetValue()
#    
#    def EvtCheckBox(self, event):
#        self.opt["DemanderImpr"] = event.IsChecked()
#     
#class pnlAnalyse(wx.Panel):
#    def __init__(self, parent, options):
#        wx.Panel.__init__(self, parent, -1)
#        ns = wx.BoxSizer(wx.VERTICAL)
#        self.options = options
#        
#        sb1 = wx.StaticBox(self, -1, u"Outils visuels d'analyse")
#        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
#        
#        label = {"AnimMontage"  : u"Proposer l'animation du démontage/remontage",
#                 "AnimArrets"   : u"Proposer l'animation du manque d'arrêt axial",
#                 "ChaineAction" : u"Proposer le tracé des chaînes d'action"}
#
#        self.cb = {}
#        for titre, opt in options.items():
#            c = wx.CheckBox(self, -1, label[titre])
#            self.cb[c.GetId()] = titre
#            c.SetValue(opt)
#            self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, c)
#            sbs1.Add(c, flag = wx.ALL, border = 5)
#        
#        ns.Add(sbs1, flag = wx.EXPAND)
#
#        self.SetSizerAndFit(ns)
#
#    def EvtCheckBox(self, event):
#        self.options[self.cb[event.GetId()]] = event.IsChecked()
        
class pnlCouleurs(wx.Panel):
    """ Dialog de selection d'un format de ligne
        <format> = liste : [couleur, style, épaisseur]
    """
    def __init__(self, parent, opt):
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = opt
        
        lstID = ["COUL_GRILLE", "COUL_ISOGAIN", "COUL_ISOPHASE", 
                 "COUL_POLES", "COUL_PT_CRITIQUE", "COUL_MARGE_OK", "COUL_MARGE_NO",]
        self.lstID = lstID
        
        
        self.CreatePanel()
        
        
        
    def CreatePanel(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        nomCouleurs = {"COUL_MARGE_OK"      : _(u'Marge de stabilité "valide"'),
                       "COUL_MARGE_NO"      : _(u'Marge de stabilité "non valide"'),
                       "COUL_GRILLE"        : _(u'Grille'),
                       "COUL_ISOGAIN"       : _(u'Courbe "isogain"'),
                       "COUL_ISOPHASE"      : _(u'Courbe "isophase"'),
                       "COUL_POLES"         : _(u'Pôles'),
                       "COUL_PT_CRITIQUE"   : _(u'Point critique et Courbe "lambda"'),
                        }
        
        
        self.lstButton = {}
        for i, k in enumerate(self.lstID):
            sizerH = wx.BoxSizer(wx.HORIZONTAL)
            txtColor = wx.StaticText(self, i+100, nomCouleurs[k])
            selColor = wx.Button(self, i, "", size = (100,22))
            selColor.SetToolTipString(_(u"Modifier la couleur de l'élément") + " :\n" + nomCouleurs[k])
            selColor.SetBackgroundColour(self.opt[k])
            
            sizerH.Add(txtColor, flag = wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)
            sizerH.Add(selColor, flag = wx.ALIGN_LEFT|wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)
            self.sizer.Add(sizerH, flag = wx.ALIGN_RIGHT|wx.ALL)
            
            self.lstButton[k] = selColor
            self.Bind(wx.EVT_BUTTON, self.OnClick, id = i)
    
        self.SetSizer(self.sizer)
        
        
    ###############################################################################################
    def OnClick(self, event = None):      
        id = event.GetId()
        colourData = wx.ColourData()
        colourData.SetColour(wx.NamedColour(self.opt[self.lstID[id]]))
        dlg = wx.ColourDialog(self, colourData)

        # Ensure the full colour dialog is displayed, 
        # not the abbreviated version.
        dlg.GetColourData().SetChooseFull(True)

        if dlg.ShowModal() == wx.ID_OK:

            # If the user selected OK, then the dialog's wx.ColourData will
            # contain valid information. Fetch the data ...

            self.opt[self.lstID[id]] = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
            self.lstButton[self.lstID[id]].SetBackgroundColour(self.opt[self.lstID[id]])
#            print self.opt[self.lstID[id]]
            
        # Once the dialog is destroyed, Mr. wx.ColourData is no longer your
        # friend. Don't use it again!
        dlg.Destroy()
        return
    
    
#class nbOptions(wx.Notebook):
#    def __init__(self, parent, options):
#        wx.Notebook.__init__(self, parent, -1)
#        
#        self.AddPage(pnlGenerales(self, options.optGenerales), _(u"Général"))
#        self.AddPage(pnlAffichage(self, options.optAffichage), _(u"Affichage"))
##        self.AddPage(pnlImpression(self, options.optImpression), u"Rapport")
##        self.AddPage(pnlAnalyse(self, options.optAnalyse), u"Analyse")
#        self.SetMinSize((350,-1))
            
##########################################################################################################
#
#  DirSelectorCombo
#
##########################################################################################################
class DirSelectorCombo(wx.combo.ComboCtrl):
    def __init__(self, *args, **kw):
        wx.combo.ComboCtrl.__init__(self, *args, **kw)

        # make a custom bitmap showing "..."
        bw, bh = 14, 16
        bmp = wx.EmptyBitmap(bw,bh)
        dc = wx.MemoryDC(bmp)

        # clear to a specific background colour
        bgcolor = wx.Colour(255,254,255)
        dc.SetBackground(wx.Brush(bgcolor))
        dc.Clear()

        # draw the label onto the bitmap
        label = "..."
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        tw,th = dc.GetTextExtent(label)
        dc.DrawText(label, (bw-tw)/2, (bw-tw)/2)
        del dc

        # now apply a mask using the bgcolor
        bmp.SetMaskColour(bgcolor)

        # and tell the ComboCtrl to use it
        self.SetButtonBitmaps(bmp, True)
        

    # Overridden from ComboCtrl, called when the combo button is clicked
    def OnButtonClick(self):
        # In this case we include a "New directory" button. 
#        dlg = wx.FileDialog(self, "Choisir un fichier modèle", path, name,
#                            "Rich Text Format (*.rtf)|*.rtf", wx.FD_OPEN)
        dlg = wx.DirDialog(self, _("Choisir un dossier"),
                           defaultPath = globdef.DOSSIER_EXEMPLES,
                           style = wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            self.SetValue(dlg.GetPath())

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        
        self.SetFocus()

    # Overridden from ComboCtrl to avoid assert since there is no ComboPopup
    def DoSetPopupControl(self, popup):
        pass


