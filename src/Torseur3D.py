#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

#############################################################################
#############################################################################
##                                                                         ##
##                               Torseur 3D                                ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2013 Cédrick FAURY

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
Torseur3D.py
Affichage 3D de torseurs d'action mécanique
Copyright (C) 2009-2013 Cédrick FAURY

"""
import sys, os#, time

import matplotlib
matplotlib.use('WXAgg')

import matplotlib.cm as cm

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import getp, subplot, setp
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import ImageGrid
import matplotlib.transforms as mtransforms
matplotlib.rcParams['legend.fontsize'] = 10
matplotlib.interactive(True)
matplotlib.rcParams['mathtext.fontset'] = 'stixsans'
import proj3d
import numpy as np

from DAQ import *#InterfaceAcquisition
from Saisie import *
import DAQ
import wx
import threading
from math import sin, pi, cos, atan
from torseur import Point, Vecteur, Torseur
import random

import Options

from widgets import *
#import traceback

VERSION = "1.2beta2"



DEBUG = False

################################################################################
################################################################################



# Les couleurs
COUL_RESULTANTE = wx.Colour(240,10,10)
COUL_MOMENT = wx.Colour(40,240,40)


PULS = [1.0, 2.0, 1.3, 0.9, 0.7, 2.5]

# Accélération de la pesanteur (m/s²)
G = 10

ORIGINE = Point(nom = 'O')

################################################################################
################################################################################

TIMER_ID = wx.NewId()
PERIODE = 200 #(ms)

# Limites des axes (mm)
LIMITE_X0 = LIMITE_Y0 = LIMITE_Z0 = -300.0
LIMITE_X1 = LIMITE_Y1 = LIMITE_Z1 = 300.0

# Echelles de vecteur Résultante (mm/N) et des vecteurs Moment(mm/Nm)
ECHELLE_R = 20.0
ECHELLE_M = 100.0

# Précision d'affichege des composantes
PRECISION_R = 1
PRECISION_M = 2


# Type de démo : 0 : aléatoire ; 1 = clavier
TYPE_DEMO = 1
PAS_R = 0.1  #N
PAS_M = 0.01 #Nm

# Mode de démarrage : 0 = torseur ; 1 = pyStatic
MODE_DEMARRAGE = 0

# Tailles des polices sur la zone graphique mlp
TAILLE_VECTEUR = 26
TAILLE_POINT = 22
TAILLE_COMPOSANTES = 12
TAILLE_TICKS = 14

class Chronometre():
    def __init__(self):
        self.initScores()
        self.etat = False
        
    def demarrer(self):
        self.t1 = time.clock()
        self.etat = True
        self.duree_pause = 0.0
        
    def stopper(self):
        self.score = self.getVal()
        self.etat = False
        if self.score > self.maxScore:
            self.maxScore = self.score
            
    def initScores(self):
        self.maxScore = 0.0
        self.score = 0.0
        self.duree_pause = 0.0
        self.t1 = time.clock()
        
    def getMaxScore(self):
        return self.maxScore
    
    def getVal(self):
        t2 = time.clock()-self.t1 - self.duree_pause
        return t2
    
    def estDemarre(self):
        return self.etat
        
    def pause(self):
        self.debut_pause = time.clock()
        
    def reprise(self):
        self.duree_pause += time.clock() - self.debut_pause
                      
                      
                      
_id = 0
def getNewId():
    global _id
    _id +=1
    return _id


        
################################################################################
#
# Panel premettant l'affichage et la saisie des coordonnées d'un Point
#
################################################################################
class PointCtrlPanel(wx.Panel):
    """
    """
    def __init__(self, parent, fct, P = None, nom = '', titre = '', useMPL = False):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.fct = fct
        
        if P == None:
            self.P = Point()
        else:
            self.P = P
        
        if useMPL:
            _titre = wx.StaticBitmap(self, -1, mathtext_to_wxbitmap(nom))
        else:
            _titre = wx.StaticText(self, -1, nom)

        vx = Variable('', [int(m2mm(self.P.x))], typ = VAR_ENTIER, modeLog = False)
        vy = Variable('', [int(m2mm(self.P.y))], typ = VAR_ENTIER, modeLog = False)
        vz = Variable('', [int(m2mm(self.P.z))], typ = VAR_ENTIER, modeLog = False)
        
        self.x = VariableCtrl(self, vx, coef = 1,
                              labelMPL = False, signeEgal = False)
        self.y = VariableCtrl(self, vy, coef = 1,
                              labelMPL = False, signeEgal = False)
        self.z = VariableCtrl(self, vz, coef = 1,
                              labelMPL = False, signeEgal = False)
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.x, flag = wx.ALIGN_LEFT|wx.LEFT, border = 5)
        vsizer.Add(self.y, flag = wx.ALIGN_LEFT|wx.LEFT, border = 5)
        vsizer.Add(self.z, flag = wx.ALIGN_LEFT|wx.LEFT, border = 5)

        
        sb = wx.StaticBox(self, -1, titre)
        sz = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        sz.Add(_titre, flag = wx.ALIGN_CENTER_VERTICAL)
        sz.Add(wx.StaticLine(self, -1, style = wx.LI_VERTICAL), flag = wx.EXPAND)
        sz.Add(vsizer, flag = wx.ALIGN_CENTER_VERTICAL)

        self.Bind(EVT_VAR_CTRL, self.OnPointModified)
#
#        border = wx.BoxSizer(wx.VERTICAL)
#        border.Add(sz, wx.EXPAND)
#        self.SetSizerAndFit(border)
#        self.Layout()
        self.SetSizer(sz)
        self.Layout()
    
    def OnPointModified(self, event):
#        print "Point de réduction",self.P 
#        var = event.GetVar()
        self.P.x = mm2m(self.x.variable.v[0])
        self.P.y = mm2m(self.y.variable.v[0])
        self.P.z = mm2m(self.z.variable.v[0])
        self.fct()
        
        
################################################################################
#
# Panel premettant l'affichage des composantes d'un vecteur
#
################################################################################
class VecteurPanel(wx.Panel):
    def __init__(self, parent, vect = None, nom = '', titre = '', useMPL = False, nc = 1):
        if vect == None:
            self.vect = Vecteur()
            self.vect.setComp(vect)
        else:
            self.vect.vect

        # Nombre de chiffres après la virgule
        self.nc = nc
        
        wx.Panel.__init__(self, parent, -1)
        
        if useMPL:
            _titre = wx.StaticBitmap(self, -1, mathtext_to_wxbitmap(nom))
        else:
            _titre = wx.StaticText(self, -1, nom)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.x = wx.StaticText(self, -1, '')
        self.y = wx.StaticText(self, -1, '')
        self.z = wx.StaticText(self, -1, '')
        vsizer.Add(self.x, flag = wx.ALIGN_LEFT|wx.LEFT, border = 5)
        vsizer.Add(self.y, flag = wx.ALIGN_LEFT|wx.LEFT, border = 5)
        vsizer.Add(self.z, flag = wx.ALIGN_LEFT|wx.LEFT, border = 5)
        
        
#        sizer.Add(_titre, flag = wx.ALIGN_CENTER_VERTICAL)
#        sizer.Add(vsizer, flag = wx.ALIGN_CENTER_VERTICAL)
        
        sb = wx.StaticBox(self, -1, titre)
        sz = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        sz.Add(_titre, flag = wx.ALIGN_CENTER_VERTICAL)
        sz.Add(wx.StaticLine(self, -1, style = wx.LI_VERTICAL), flag = wx.EXPAND)
        sz.Add(vsizer, flag = wx.ALIGN_CENTER_VERTICAL)
        
        
        
        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(sz, 1, wx.EXPAND)
        
        self.SetSizer(border)
#        self.SetSizerAndFit(sz)


    def actualiser(self, vect):
        if not isinstance(vect, Vecteur):
            vect = Vecteur(vect[0], vect[1], vect[2])
        self.x.SetLabel(strRound(vect.x, self.nc))
        self.y.SetLabel(strRound(vect.y, self.nc))
        self.z.SetLabel(strRound(vect.z, self.nc))
        self.Layout()
#        self.Fit()
        
        

#    f = '%.' + ('%d' % (nc))
#    z = float(f % (x.real))
#    if z%1 == 0:
#        z = int(z)
#    
#    return str(z)
def getAncre(cadran):
    """ Renvoie l'horizontalalignment et le verticalalignment 
        pour placer un text mpl dans le <cadran>
    """
    if cadran == 0:
        return 'left', 'bottom'
    elif cadran == 1:
        return 'right', 'bottom'
    elif cadran == 2:
        return 'right', 'top'
    else:
        return 'left', 'top'


################################################################################
################################################################################
class MPLVecteur():
    def __init__(self, axe, vect = None, coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True, nc = 2):
        if vect == None:
            self.vect = Vecteur()
            self.vect.setComp(vect)
        else:
            self.vect.vect
            
        self.nom = nom
        self.id = str(getNewId())
        self.echelle = echelle   
        self.coul = coul
        self.nc = nc
        
        self.comp_visible = True
        self.valcomp_visible = True
        self.nom_visible = True
        
        self.initdraw(axe)
        
        self.set_visible(visible)

    def setEchelle(self, echelle):
        self.echelle = echelle
        
    def set_visible(self, etat):
        for a in self.artists:
            a.set_visible(etat)
        
    def set_visible_nom(self, etat):
        self.nom_visible = etat
        for a in [self.text]:
            a.set_visible(etat)
            
    def setComp(self, vect):
        if not isinstance(vect, Vecteur):
            vect = Vecteur(vect[0], vect[1], vect[2])
        self.vect.setComp(vect)
        
################################################################################
################################################################################
class MPLVecteur3D(MPLVecteur):
    def __init__(self, axe, vect = None, coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True, nc = 2):
        
        MPLVecteur.__init__(self, axe, vect, coul, nom, echelle, visible, nc)
        
    def getCadran(self, v = None):
        if v == None:
            x, y, z = self.vect.x, self.vect.y, self.vect.z
        else:
            x, y, z = v
        _x, _y, _z = proj3d.transform(x, y, z, self.axe.get_proj())
#        print _x, _y, _z
        if _x > 0:
            if _y > 0:
                c = 0
            else:
                c = 3
        else:
            if _y > 0:
                c = 1
            else:
                c = 2
        return c
        
    def set_artist_data(self, art, x, y, z):
        for line in art:
            line.set_xdata(x)
            line.set_ydata(y)
            line.set_3d_properties(zs=z)
                 
    def draw(self, o = ORIGINE, multi = False):
        _x = m2mm(o.x)
        _y = m2mm(o.y)
        _z = m2mm(o.z)
        p = Point(_x + self.vect.x*self.echelle,
                  _y + self.vect.y*self.echelle,
                  _z + self.vect.z*self.echelle)
        x = [_x, p.x]
        y = [_y, p.y]
        z = [_z, p.z]
        self.set_artist_data(self.fleche, x, y, z)
        
        self.x = x
        self.y = y
        self.z = z
        
        x0 = [_x, _x]
        y0 = [_y, _y]
        z0 = [_z, _z]
        self.set_artist_data(self.comp_x, x, y0, z0)
        self.set_artist_data(self.comp_y, x0, y, z0)
        self.set_artist_data(self.comp_z, x0, y0, z)
        
        if multi: m = 2
        else: m = 1
        
        ancre = getAncre(self.getCadran((self.vect.x, 0, 0)))
        self.text_cx.set_text(strRound(self.vect.x, self.nc))
        self.text_cx.set_x(p.x)
        self.text_cx.set_y(_y)
        self.text_cx.set_size(TAILLE_COMPOSANTES/m)
        self.text_cx.set_3d_properties(z = _z, zdir = (x[1]-x[0], y0[1]-y0[0], z0[1]-z0[0]))
        self.text_cx.set_horizontalalignment(ancre[0])
        self.text_cx.set_verticalalignment(ancre[1])
        
        ancre = getAncre(self.getCadran((0, self.vect.y, 0)))
        self.text_cy.set_text(strRound(self.vect.y, self.nc))
        self.text_cy.set_x(_x)
        self.text_cy.set_y(p.y)
        self.text_cy.set_size(TAILLE_COMPOSANTES/m)
        self.text_cy.set_3d_properties(z = _z, zdir = (x0[1]-x0[0], y[1]-y[0], z0[1]-z0[0]))
        self.text_cy.set_horizontalalignment(ancre[0])
        self.text_cy.set_verticalalignment(ancre[1])
        
        ancre = getAncre(self.getCadran((0, 0, self.vect.z)))
        self.text_cz.set_text(strRound(self.vect.z, self.nc))
        self.text_cz.set_x(_x)
        self.text_cz.set_y(_y)
        self.text_cz.set_size(TAILLE_COMPOSANTES/m)
        self.text_cz.set_3d_properties(z = p.z, zdir = (x0[1]-x0[0], y0[1]-y0[0], z[1]-z[0]))
        self.text_cz.set_horizontalalignment(ancre[0])
        self.text_cz.set_verticalalignment(ancre[1])
        
        
        self.set_artist_data(self.arete[0], [p.x, p.x], [_y, _y], [_z, p.z])
        self.set_artist_data(self.arete[1], [_x, p.x], [_y, _y], [p.z, p.z])
        self.set_artist_data(self.arete[2], [_x, _x], [_y, p.y], [p.z, p.z])
        self.set_artist_data(self.arete[3], [_x, _x], [p.y, p.y], [_z, p.z])
        self.set_artist_data(self.arete[4], [_x, p.x], [p.y, p.y], [_z, _z])
        self.set_artist_data(self.arete[5], [p.x, p.x], [_y, p.y], [_z, _z])
        self.set_artist_data(self.arete[6], [p.x, _x], [p.y, p.y], [p.z, p.z])
        self.set_artist_data(self.arete[7], [p.x, p.x], [p.y, _y], [p.z, p.z])
        self.set_artist_data(self.arete[8], [p.x, p.x], [p.y, p.y], [p.z, _z])
        
        ancre = getAncre(self.getCadran())
        self.text.set_x(p.x)
        self.text.set_y(p.y)
        self.text.set_size(TAILLE_VECTEUR/m)
        self.text.set_3d_properties(z = p.z, zdir = None)
        self.text.set_horizontalalignment(ancre[0])
        self.text.set_verticalalignment(ancre[1])
        
        
    def initdraw(self, axe):
        
        # La flèche
        self.fleche = axe.plot([0], [0], [0], color = self.coul, linewidth = 2, label = "f"+self.id)
        
        # Les composantes
        self.comp_x = axe.plot([0], [0], [0], color = self.coul, label = "x"+self.id)
        self.comp_y = axe.plot([0], [0], [0], color = self.coul, label = "y"+self.id)
        self.comp_z = axe.plot([0], [0], [0], color = self.coul, label = "z"+self.id)
        
        # Les valeurs des composantes
        self.text_cx = axe.text3D(0, 0, 0, "", color = self.coul)
        self.text_cy = axe.text3D(0, 0, 0, "", color = self.coul)
        self.text_cz = axe.text3D(0, 0, 0, "", color = self.coul)
        
        # Les arêtes de la "boite"
        ls = "--"
        self.arete = []
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "0"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "1"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "2"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "3"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "4"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "5"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "6"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "7"+self.id))
        self.arete.append(axe.plot([0], [0], [0], color = self.coul, linestyle = ls, label = "8"+self.id))

        # Le nom du vecteur
        self.text = axe.text3D(0, 0, 0, self.nom)#, horizontalalignment = ancre[0], va = ancre[1])
        
        #
        self.axe = axe
        
        artists = []
        artists.append(self.fleche[0])
        artists.append(self.comp_x[0])
        artists.append(self.comp_y[0])
        artists.append(self.comp_z[0])
        for a in self.arete:
            artists.append(a[0])
        artists.append(self.text)
        artists.append(self.text_cx)
        artists.append(self.text_cy)
        artists.append(self.text_cz)
        self.artists = artists
    
        self.x = [0]
        self.y = [0]
        self.z = [0]
    
            
    def set_visible_comp(self, etat):
        self.comp_visible = etat
        lst = [self.comp_x[0], self.comp_y[0], self.comp_z[0]]
        for a in self.arete:
            lst.append(a[0])
        for a in lst:
            a.set_visible(etat)
            
    def set_visible_valcomp(self, etat):
        self.valcomp_visible = etat
        for a in [self.text_cx, self.text_cy, self.text_cz]:
            a.set_visible(etat)
    
        
    def get_data_lim(self):
        return self.x, self.y, self.z
        
################################################################################
################################################################################
class MPLVecteur2D(MPLVecteur):
    def __init__(self, axe, vect = None, vue = 'f', coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True, nc = 2):
        self.vue = vue
        MPLVecteur.__init__(self, axe, vect, coul, nom, echelle, visible, nc)
          
        
    def set_artist_data(self, art, x, y):
        for line in art:
            line.set_xdata(x)
            line.set_ydata(y)
        
    def getCadran(self, composante = None):
        if self.vue == 'f':
            _x = self.vect.y
            _y = self.vect.z
        elif self.vue == 'g':
            _x = self.vect.x
            _y = self.vect.z
        else: 
            _x = self.vect.y
            _y = -self.vect.x
            
        if composante == 'x':
            _y = 0
        elif composante == 'y':
            _x = 0
            
        if _x > 0:
            if _y > 0:
                c = 0
            else:
                c = 3
        else:
            if _y > 0:
                c = 1
            else:
                c = 2
        return c
                 
                
        
    def draw(self, o = ORIGINE):
        
        if self.vue == 'f':
            _x = m2mm(o.y)
            _y = m2mm(o.z)
            p = Point(_x + self.vect.y*self.echelle,
                      _y + self.vect.z*self.echelle)
            self.text_cx.set_text(strRound(self.vect.y, self.nc))
            self.text_cy.set_text(strRound(self.vect.z, self.nc))
        elif self.vue == 'g':
            _x = m2mm(o.x)
            _y = m2mm(o.z)
            p = Point(_x + self.vect.x*self.echelle,
                      _y + self.vect.z*self.echelle)
            self.text_cx.set_text(strRound(self.vect.x, self.nc))
            self.text_cy.set_text(strRound(self.vect.z, self.nc))
        else: 
            _x = m2mm(o.y)
            _y = m2mm(o.x)
            p = Point(_x + self.vect.y*self.echelle,
                      _y + self.vect.x*self.echelle)
            self.text_cx.set_text(strRound(self.vect.y, self.nc))
            self.text_cy.set_text(strRound(self.vect.x, self.nc))
                
        x = [_x, p.x]
        y = [_y, p.y]
     
        self.set_artist_data(self.fleche, x, y)
            
        x0 = [_x, _x]
        y0 = [_y, _y]
        
        self.set_artist_data(self.comp_x, x, y0)
        self.set_artist_data(self.comp_y, x0, y)
        
        ancre = getAncre(self.getCadran(composante = 'x'))
        self.text_cx.set_x(p.x)
        self.text_cx.set_y(_y)
        self.text_cx.set_size(TAILLE_COMPOSANTES/2)
        self.text_cx.set_horizontalalignment(ancre[0])
        self.text_cx.set_verticalalignment(ancre[1])
        
        ancre = getAncre(self.getCadran(composante = 'y'))
        self.text_cy.set_x(_x)
        self.text_cy.set_y(p.y)
        self.text_cy.set_size(TAILLE_COMPOSANTES/2)
        self.text_cy.set_horizontalalignment(ancre[0])
        self.text_cy.set_verticalalignment(ancre[1])
    
        ancre = getAncre(self.getCadran())
        self.text.set_x(p.x)
        self.text.set_y(p.y)
        self.text.set_size(TAILLE_VECTEUR/2)
        self.text.set_horizontalalignment(ancre[0])
        self.text.set_verticalalignment(ancre[1])
        
        self.set_artist_data(self.arete[0], [p.x, p.x], y)
        self.set_artist_data(self.arete[1], x, [p.y, p.y])
        
        self.regleVisibilite()
        
        
    def regleVisibilite(self):
        lX = self.axe.get_xlim()
        lY = self.axe.get_ylim()
        lY = sorted(lY)
        for txt, etat in zip([self.text, self.text_cx, self.text_cy], [self.nom_visible, self.valcomp_visible, self.valcomp_visible]):
            X, Y = txt.get_position()
            if X > lX[0] and X < lX[1] and Y > lY[0] and Y < lY[1]:
                txt.set_visible(etat)
            else:
                txt.set_visible(False)
    
    
        
    def initdraw(self, axe):
        if self.vue == 'f':
            lx = 'y'
            ly = 'z'
        elif self.vue == 'g':
            lx = 'x'
            ly = 'z'
        else: 
            lx = 'y'
            ly = 'x'
                
        self.fleche = axe.plot([0], [0], color = self.coul, linewidth = 2, label = "f"+self.id)
        self.comp_x = axe.plot([0], [0], color = self.coul, label = lx+self.id)
        self.comp_y = axe.plot([0], [0], color = self.coul, label = ly+self.id)
        
        
        self.text_cx = axe.text(0, 0, "", color = self.coul)
        self.text_cy = axe.text(0, 0, "", color = self.coul, rotation = 90)
        
        
        ls = "--"
        self.arete = []
        self.arete.append(axe.plot([0], [0], color = self.coul, linestyle = ls, label = "0"+self.id))
        self.arete.append(axe.plot([0], [0], color = self.coul, linestyle = ls, label = "1"+self.id))
        
        self.text = axe.text(0, 0, self.nom)#, horizontalalignment = ancre[0], va = ancre[1])
        
        self.axe = axe
        
        artists = []
        artists.append(self.fleche[0])
        artists.append(self.comp_x[0])
        artists.append(self.comp_y[0])
        
        for a in self.arete:
            artists.append(a[0])
        artists.append(self.text)
        artists.append(self.text_cx)
        artists.append(self.text_cy)
        self.artists = artists
    
            
            
    def set_visible_comp(self, etat):
        self.comp_visible = etat
        lst = [self.comp_x[0], self.comp_y[0]]
        for a in self.arete:
            lst.append(a[0])
        for a in lst:
            a.set_visible(etat)
            
    def set_visible_valcomp(self, etat):
        self.valcomp_visible = etat
        for a in [self.text_cx, self.text_cy]:
            a.set_visible(etat)
            
   
        
#############################################################################################################
class MPLPoint():
    def __init__(self, axe, point = None, coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True):
        if point == None:
            self.point = Point()
        else:
            self.point = point
        self.coul = coul
        self.nom = u"  "+nom
        self.id = str(getNewId())
        self.initdraw(axe)
        
        self.set_visible(visible)
        
    def getAncre(self, lstvect):
        if lstvect == None or None in lstvect:
            return 'right', 'top'
        c = [0, 1, 2, 3]
        c.remove(lstvect[0].getCadran())
        try:
            c.remove(lstvect[1].getCadran())
        except:
            pass
        
        return getAncre(c[0])    
    
    def set_visible(self, etat):
        for a in self.artists:
            a.set_visible(etat)
            
    def setComp(self, point):
        if not isinstance(point, Point):
            point = Point(point[0], point[1], point[2])
        self.point = point
        
    def remove(self):
        if self.axe == None:
            return
        self.pt[0].remove()
        self.text.remove()
    
    
        
            
#############################################################################################################
class MPLPoint3D(MPLPoint):
    def __init__(self, axe, point = None, coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True):
        
        MPLPoint.__init__(self, axe, point, coul, nom, echelle, visible)   
    
    
    def draw(self, o = ORIGINE, vect = None, multi = False):
        if multi:
            m = 2
        else:
            m = 1
            
        lx = m2mm(self.point.x)
        ly = m2mm(self.point.y)
        lz = m2mm(self.point.z)
        self.pt[0].set_xdata([lx])
        self.pt[0].set_ydata([ly])
        self.pt[0].set_3d_properties(zs = [lz])
        
        self.lx = [lx]
        self.ly = [ly]
        self.lz = [lz]
        
        self.text.set_size(TAILLE_POINT/m)
        
        ancre = self.getAncre(vect)
        self.text.set_horizontalalignment(ancre[0])
        self.text.set_verticalalignment(ancre[1])
        self.text.set_x(lx)
        self.text.set_y(ly)
        self.text.set_3d_properties(z = lz, zdir = None)
        
        
    def decaleTexte(self):
        ancre = self.text.get_horizontalalignment()
        if ancre == 'right':
#            print self.text.get_text()
            lx = self.pt[0].get_xdata()[0]
            ly = self.pt[0].get_ydata()[0]
            lz = self.pt[0]._verts3d[2][0]
            tr = self.axe.get_proj() 
            _x, _y, _z = proj3d.transform(lx, ly, lz, tr)
#            print ly, "-->", _y,
            _x, _y = self.axe.transData.transform((_x, _y))
#            print "-->",_y
            _x += -4
            _x, _y = self.axe.transData.inverted().transform((_x, _y))
            lx, ly, lz = proj3d.inv_transform(_x, _y, _z, tr)
#            print _x, "-->", lx
            self.text.set_x(lx)
            self.text.set_y(ly)
            self.text.set_3d_properties(z = lz, zdir = None)
            
            
            
    def initdraw(self, axe):
        self.pt = axe.plot([0], [0], [0], marker = 'o', mfc = self.coul, picker=True)
        self.pt[0].set_picker(5)
        self.text = axe.text3D(0, 0, 0, self.nom)
        self.axe = axe
        
        artists = []
        artists.append(self.pt[0])
        artists.append(self.text)
        self.artists = artists
        
    
    
    
        
    
        
        
    def get_data_lim(self):
        return self.lx, self.ly, self.lz
        
        
        
#############################################################################################################
class MPLPoint2D(MPLPoint):
    def __init__(self, axe, point = None, vue = 'f', coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True):
        self.vue = vue
        MPLPoint.__init__(self, axe, point, coul, nom, echelle, visible)
        
        
    def draw(self, o = ORIGINE, vect = None):
        if self.vue == 'f':
            lx = m2mm(self.point.y)
            ly = m2mm(self.point.z)
        elif self.vue == 'g':
            lx = m2mm(self.point.x)
            ly = m2mm(self.point.z)
        else: 
            lx = m2mm(self.point.y)
            ly = m2mm(self.point.x)
            
        self.pt[0].set_xdata([lx])
        self.pt[0].set_ydata([ly])
        
        self.text.set_size(TAILLE_POINT/2)
        ancre = self.getAncre(vect)
        self.text.set_horizontalalignment(ancre[0])
        self.text.set_verticalalignment(ancre[1])
        self.text.set_x(lx)
        self.text.set_y(ly)
        self.decaleTexte()
        
        self.regleVisibilite()
            
    def decaleTexte(self):
        ancre = self.text.get_horizontalalignment()
        if ancre == 'right':
            lx = self.pt[0].get_xdata()[0]
            tr = self.axe.transData
            _x, _y = tr.transform((lx, 0))
#            print lx, "-->", _x
            _x += -4
            lx, ly = tr.inverted().transform((_x, _y))
#            print _x, "-->", lx
            self.text.set_x(lx)
        
    def initdraw(self, axe):
        self.pt = axe.plot([0], [0], marker = 'o', mfc = self.coul, picker=True)
        self.pt[0].set_picker(5)
        self.text = axe.text(0, 0, self.nom)
        self.axe = axe
        
        artists = []
        artists.append(self.pt[0])
        artists.append(self.text)
        self.artists = artists
    
    def regleVisibilite(self):
        X, Y = self.pt[0].get_xdata()[0], self.pt[0].get_ydata()[0]
        lX = self.axe.get_xlim()
        lY = self.axe.get_ylim()
        lY = sorted(lY) # à cause de la vue de dessus dont l'axe Y est inversé
        if X > lX[0] and X < lX[1] and Y > lY[0] and Y < lY[1]:
            self.set_visible(True)
        else:
            self.set_visible(False)

        
#############################################################################################################
class MPLDroite():
    def __init__(self, axe, droite = None, coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True):
        self.droite = droite
        self.coul = coul
        self.nom = nom
        self.id = str(getNewId())
        self.initdraw(axe)
        self.set_visible(visible)
        
    def set_visible(self, etat):
        for a in self.artists:
            a.set_visible(etat)
            
    def setComp(self, droite):
        self.droite = droite
        if self.droite != None:
            self.droite.changeUnite('mm')
    
    def remove(self):
        if self.axe == None:
            return
        self.dr[0].remove()
        self.text.remove()
            
#############################################################################################################
class MPLDroite3D(MPLDroite):
    def __init__(self, axe, droite = None, coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True):
        MPLDroite.__init__(self, axe, droite, coul, nom, echelle, visible)
        
        
    def draw(self):
#        print "draw Droite"
        if self.droite == None:
            return
        e = 0.001
        def dedans(p):
            return p != None and p.x <= x1+e and p.x >= x0-e and p.y <= y1+e and p.y >= y0-e and p.z >= z0-e and p.z <= z1+e
        
        x0, x1 = self.axe.get_xlim3d()
        y0, y1 = self.axe.get_ylim3d()
        z0, z1 = self.axe.get_zlim3d()
        p0 = self.droite.intersectionPlan(Point(x0, 0, 0), Vecteur(1,0,0))
        p1 = self.droite.intersectionPlan(Point(x1, 0, 0), Vecteur(1,0,0))
        p2 = self.droite.intersectionPlan(Point(0, y0, 0), Vecteur(0,1,0))
        p3 = self.droite.intersectionPlan(Point(0, y1, 0), Vecteur(0,1,0))
        p4 = self.droite.intersectionPlan(Point(0, 0, z0), Vecteur(0,0,1))
        p5 = self.droite.intersectionPlan(Point(0, 0, z1), Vecteur(0,0,1))
         
        x = []
        y = []
        z = []
        for p in [p0, p1, p2, p3, p4, p5]:
#            print p
            if dedans(p):
                x.append(p.x)
                y.append(p.y)
                z.append(p.z)
        
#        print x, y, z
        self.dr[0].set_xdata(x)
        self.dr[0].set_ydata(y)
        self.dr[0].set_3d_properties(zs = z)
        
        
        
    def initdraw(self, axe):
        self.dr = axe.plot([0], [0], [0], color = self.coul)
        self.axe = axe
        artists = []
        artists.append(self.dr[0])
        self.artists = artists
    
    
        

#############################################################################################################
class MPLDroite2D(MPLDroite):
    def __init__(self, axe, droite = None, vue = 'f', coul = wx.Colour(0,0,0), nom = "", 
                 echelle = 1.0, visible = True):
        self.vue = vue
        MPLDroite.__init__(self, axe, droite, coul, nom, echelle, visible)
        
        
    def draw(self):
#        print "draw Droite"
        if self.droite == None:
            return
        e = 0.001
        def dedans(p):
            return p != None and p.x <= x1+e and p.x >= x0-e and p.y <= y1+e and p.y >= y0-e
        
        
        try:
            x0, x1 = self.axe.get_xlim3d()
            y0, y1 = self.axe.get_ylim3d()
        except:
            return
        
        if self.vue == 'f':
            p0 = self.droite.intersectionPlan(Point(0, x0, 0), Vecteur(0,1,0))
            p1 = self.droite.intersectionPlan(Point(0, x1, 0), Vecteur(0,1,0))
            p2 = self.droite.intersectionPlan(Point(0, 0, y0), Vecteur(0,0,1))
            p3 = self.droite.intersectionPlan(Point(0, 0, y1), Vecteur(0,0,1))
            for p in [p0, p1, p2, p3]:
                if p != None:
                    x, y = p.y, p.z
                    p.x, p.y = x, y
        elif self.vue == 'g':
            p0 = self.droite.intersectionPlan(Point(x0, 0, 0), Vecteur(1,0,0))
            p1 = self.droite.intersectionPlan(Point(x1, 0, 0), Vecteur(1,0,0))
            p2 = self.droite.intersectionPlan(Point(0, 0, y0), Vecteur(0,0,1))
            p3 = self.droite.intersectionPlan(Point(0, 0, y1), Vecteur(0,0,1))
            for p in [p0, p1, p2, p3]:
                if p != None:
                    x, y = p.x, p.z
                    p.x, p.y = x, y
        else:
            p0 = self.droite.intersectionPlan(Point(y0, 0, 0), Vecteur(1,0,0))
            p1 = self.droite.intersectionPlan(Point(y1, 0, 0), Vecteur(1,0,0))
            p2 = self.droite.intersectionPlan(Point(0, x0, 0), Vecteur(0,1,0))
            p3 = self.droite.intersectionPlan(Point(0, x1, 0), Vecteur(0,1,0))
            for p in [p0, p1, p2, p3]:
                if p != None:
                    x, y = p.y, p.x
                    p.x, p.y = x, y
         
        x = []
        y = []
        
        for p in [p0, p1, p2, p3]:
#            print p
            if dedans(p):
                x.append(p.x)
                y.append(p.y)
                
        
#        print x, y, z
        self.dr[0].set_xdata(x)
        self.dr[0].set_ydata(y)
        
        
        
    def initdraw(self, axe):
        self.dr = axe.plot([0], [0], color = self.coul)
        self.axe = axe
        artists = []
        artists.append(self.dr[0])
        self.artists = artists
    
   
################################################################################
#
#   Fenetre principale 
#
################################################################################
class Torseur3D(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, "", size = (805,619))
        if DEBUG: print "Mode DEBUG"
        
        self.SetIcon(wx.Icon(os.path.join("Images", 'Torseur3D.ico')))
        
        #############################################################################################
        # Instanciation et chargement des options
        #############################################################################################
        options = self.optionsDefaut()
        if options.fichierExiste():
            try :
                options.ouvrir()
            except:
                print "Fichier d'options corrompus ou inexistant !! Initialisation ..."
                options = self.optionsDefaut()
        else:
            options = self.optionsDefaut()
        self.DefinirOptions(options)
        print self.options
        
        self.pause = False
            
        self.pleinEcran = False
        self.makeTB()
        
        
        #
        # Les paramètres liés au torseur
        #
        self.tors = Torseur(P = Point(0.0, 0.0, 0.065, nom = 'P')) # Par défaut réduit au centre de la sphère
        self.torsO = Torseur()
        self.T = 0.0
        
        #
        # Le NoteBook des différentes activités
        #
        self.nb = wx.Notebook(self, -1)
        
        # Page "Torseurs"
        self.pageTorseurs = PanelTorseurs(self.nb, self)
        self.nb.AddPage(self.pageTorseurs, "Torseurs en perspective")
        
        # Page "PyStatic"
        self.pagePyStatic = PanelPyStatic(self.nb, self)
        self.nb.AddPage(self.pagePyStatic, "Equilibre d'une barre")

        self.nb.ChangeSelection(MODE_DEMARRAGE)
        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        #
        # Le panel de commande
        #
        psizer = wx.BoxSizer(wx.VERTICAL)
        size = (210,-1)
        self.panelCommande = wx.Panel(self, -1, size = size)
        self.panelCommande.SetMinSize(size)
        self.panelCommande.SetMaxSize(size)
        
        vsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panelResultante = VecteurPanel(self.panelCommande, nom = r"$\vec{R}$", 
                                            titre = u"Résultante (N)", useMPL = True, nc = PRECISION_R)
        self.panelMoment = VecteurPanel(self.panelCommande, nom = r"$\vec{M}_P$", 
                                        titre = u"Moment en P (Nm)", useMPL = True, nc = PRECISION_M)
        vsizer.Add(self.panelResultante, 1, flag = wx.EXPAND|wx.ALL, border = 3)
        vsizer.Add(self.panelMoment, 1, flag = wx.EXPAND|wx.ALL, border = 3)
        self.imgTorseurO = wx.StaticBitmap(self.panelCommande, -1, 
                                          self.torsO.getBitmap(ncR = PRECISION_R, ncM = PRECISION_M))
        self.imgTorseur = wx.StaticBitmap(self.panelCommande, -1, 
                                          self.tors.getBitmap(ncR = PRECISION_R, ncM = PRECISION_M))
        self.panelPointRed = PointCtrlPanel(self.panelCommande, self.OnPointRedModified, self.tors.P, nom = 'P', titre = u"Point de réduction (mm)", useMPL = True)
        self.pageTorseurs.miseAJourPtRed(self.tors.P)
        psizer.Add(vsizer, flag = wx.EXPAND|wx.ALL)
        
        psizer.Add(self.imgTorseurO, flag = wx.EXPAND|wx.ALL, border = 3)
        psizer.Add(self.imgTorseur, flag = wx.EXPAND|wx.ALL, border = 3)
        psizer.Add(self.panelPointRed, flag = wx.EXPAND|wx.ALL, border = 3)

        #
        # Panel de saisie
        #
        self.saisie = InterfaceSaisie(self.panelCommande, ECHELLE_R, ECHELLE_M)
        psizer.Add(self.saisie, flag = wx.EXPAND|wx.ALL, border = 3)
        self.saisie.Bind(EVT_VAR_CTRL, self.onVar)
            
        #
        # Mise en place
        #
        self.panelCommande.SetSizer(psizer)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.panelCommande, 0, flag = wx.EXPAND)
        hsizer.Add(self.nb, 1, flag = wx.EXPAND)
        self.SetSizer(hsizer)
        self.Fit()
         
        wx.EVT_CLOSE(self, self.onClose)
        wx.EVT_KEY_DOWN(self, self.onKey)
        self.SetFocus()
        
        self.acquisition = True
        self.commandeAcquisition()
        
        self.onTarer()
    
        self.Bind(wx.EVT_CLOSE, self.quitter)
        self.SetSize((805,619))
    
    ############################################################################  
    def makeTB(self):
        self.tb = self.CreateToolBar()
        tsize = (24,24)
        self.tb.SetToolBitmapSize(tsize)
        
        self.tb.AddSimpleTool(10, wx.Bitmap(os.path.join("Images", "Icone_fullscreen.png")), 
                              u"Plein écran", u"Plein écran")
        self.Bind(wx.EVT_TOOL, self.commandePleinEcran, id=10)
        
        self.tb.AddCheckLabelTool(11, u"", wx.Bitmap(os.path.join("Images", "Icone_acquisition.png")), 
                                  shortHelp=u"Acquisition")
        self.Bind(wx.EVT_TOOL, self.commandeAcquisition, id=11)
        
        self.tb.AddSimpleTool(12, wx.Bitmap(os.path.join("Images", "Icone_tarer.png")), 
                                  u"Tarer", u"Tarer")
        self.Bind(wx.EVT_TOOL, self.onTarer, id=12)

        self.boutonPause = self.tb.AddCheckTool(13, wx.Bitmap(os.path.join("Images", "Icone_pause.png")), 
                                                     shortHelp=u"Pause")
        self.Bind(wx.EVT_TOOL, self.onPause, id=13)
        
        #
        # Bouton "Options"
        #
        self.tb.AddSimpleTool(14, wx.Bitmap(os.path.join("Images", "Icone_option.png")), 
                                                 u"Options")
        self.Bind(wx.EVT_TOOL, self.onOptions, id=14)
        
    
            
        self.tb.Realize()
        
        
    ###############################################################################################
    def commandeAcquisition(self, event = None):    
        self.acquisition = not self.acquisition
        
        if self.acquisition :
            #
            # Ouverture de l'interface d'acquisition
            #
            if DAQ.PORT == '':
                dlg = wx.MessageDialog(None, u"Veuillez sélectionner le port série "\
                                             u"sur lequel est connecté le banc.",
                                       u'Choix du port série',
                                       wx.OK | wx.ICON_INFORMATION
                                       #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                       )
                dlg.ShowModal()
                dlg.Destroy()
                self.onOptions(page = 0)
                
            print "Port :",DAQ.PORT
            
            self.InterfaceDAQ = InterfaceAcquisition()
            if not self.InterfaceDAQ.estOk():
                dlg = wx.MessageDialog(None, u'Il faut un port série pour utiliser Torseur3D\n\n' \
                                             u'Mode "Démo" !!',
                                   u'Pas de port série',
                                   wx.OK | wx.ICON_ERROR 
                                   #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                   )
                dlg.ShowModal()
                dlg.Destroy()
                t = u"Mode Démo"
                self.kR = 0.0
                self.kM = 0.0
                self.getTorseur = self.getRandomTorseur
            else:
                t = self.InterfaceDAQ.port
                self.getTorseur = self.InterfaceDAQ.getTorseur
        
        else:
            t = u"Mode manuel"
            self.kR = 0.0
            self.kM = 0.0
            self.getTorseur = self.getManuelTorseur
        
        self.SetTitle("Torseur 3D "+VERSION+" - "+t)    
        
        if self.getTorseur != self.getManuelTorseur:
            #
            # Initialisation du Timer qui lit sur le port
            #
            periode = PERIODE
            if DEBUG: periode = periode * 5
            self.t = wx.Timer(self, TIMER_ID)
            self.t.Start(periode)
            wx.EVT_TIMER(self, TIMER_ID, self.onTimer)
            self.saisie.Show(False)
        else:
            if hasattr(self, 't'):
                self.t.Stop()
            self.saisie.MiseAJour(self.torsO)
            self.saisie.Show()
        
    ###############################################################################################
    def commandePleinEcran(self, event):
        self.pleinEcran = not self.pleinEcran
        if self.pleinEcran:
            win = self.nb.GetCurrentPage()
            self.fsframe = wx.Frame(self, -1)
            win.Reparent(self.fsframe)
            win.canvas.Bind(wx.EVT_KEY_DOWN, self.onKey)
            self.fsframe.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
        else:
            win = self.fsframe.GetChildren()[0]
            win.Reparent(self.nb)
            self.fsframe.Destroy()
            win.SendSizeEventToParent()
    
    
        
    ############################################################################  
    def optionsDefaut(self):
        global TYPE_DEMO, PAS_R, PAS_M, TAILLE_VECTEUR, TAILLE_POINT, MODE_DEMARRAGE, \
               TAILLE_COMPOSANTES, ECHELLE_R, ECHELLE_M, PRECISION_R, PRECISION_M
        options = Options.Options()
        options.optCalibration["Coef_R"] = DAQ.COEF_R
        options.optCalibration["Coef_M"] = DAQ.COEF_M
        options.optGenerales["TypeDemo"] = TYPE_DEMO
        options.optCalibration["PORT"] = DAQ.PORT
        options.optGenerales["PAS_R"] = PAS_R
        options.optGenerales["PAS_M"] = PAS_M
        options.optAffichage["PRECISION_R"] = PRECISION_R
        options.optAffichage["PRECISION_M"] = PRECISION_M
        options.optGenerales["MODE_DEMARRAGE"] = MODE_DEMARRAGE
        options.optAffichage["TAILLE_VECTEUR"] = TAILLE_VECTEUR
        options.optAffichage["TAILLE_POINT"] = TAILLE_POINT
        options.optAffichage["TAILLE_COMPOSANTES"] = TAILLE_COMPOSANTES
        options.optAffichage["ECHELLE_R"] = ECHELLE_R
        options.optAffichage["ECHELLE_M"] = ECHELLE_M
        return options

    ##########################################################################
    def OnPageChanged(self, event):
        self.onTimer(None)
        event.Skip()
        
#        sel = event.GetSelection()
#        if sel == 0:
#            self.pagePyStatic.StopperThread()
#        
#        elif sel == 1:
##            self.pagePyStatic.InitBuffer()
#            self.pagePyStatic.DemarrerThread()
#        self.options.optGenerales["MODE_DEMARRAGE"] = sel
        
            
            
    ##########################################################################
    def onOptions(self, event = None, page = 0):
        options = self.options.copie()

        dlg = Options.FenOptions(self, options)
        dlg.CenterOnScreen()
        dlg.nb.SetSelection(page)

        # this does not return until the dialog is closed.
        val = dlg.ShowModal()
    
        if val == wx.ID_OK:
#            print options
            self.DefinirOptions(options)
            
            if hasattr(self, 'nb'):
                self.nb.GetCurrentPage().drawNouvOptions()
            
        else:
            pass
#            print "You pressed Cancel"

        dlg.Destroy()
        
        if event != None:
            self.onTimer(None)

    ##########################################################################
    def DefinirOptions(self, options):
        global TYPE_DEMO, PAS_R, PAS_M, TAILLE_VECTEUR, TAILLE_POINT, MODE_DEMARRAGE,  \
               TAILLE_COMPOSANTES, ECHELLE_R, ECHELLE_M, PRECISION_R, PRECISION_M
        self.options = options.copie()
        DAQ.COEF_R = self.options.optCalibration["Coef_R"]
        DAQ.COEF_M = self.options.optCalibration["Coef_M"]
        DAQ.PORT = self.options.optCalibration["PORT"]
        
        TYPE_DEMO = self.options.optGenerales["TypeDemo"]
        PAS_R = options.optGenerales["PAS_R"]
        PAS_M = options.optGenerales["PAS_M"]
        
        PRECISION_R = options.optAffichage["PRECISION_R"]
        PRECISION_M = options.optAffichage["PRECISION_M"]
        MODE_DEMARRAGE = options.optGenerales["MODE_DEMARRAGE"]
        TAILLE_VECTEUR = options.optAffichage["TAILLE_VECTEUR"]
        TAILLE_POINT = options.optAffichage["TAILLE_POINT"]
        TAILLE_COMPOSANTES = options.optAffichage["TAILLE_COMPOSANTES"]
        ECHELLE_R = options.optAffichage["ECHELLE_R"]
        ECHELLE_M = options.optAffichage["ECHELLE_M"]
    
    ##########################################################################
    def AppliquerOptions(self, options):    
        self.panelResultante.nc = PRECISION_R
        self.panelMoment.nc = PRECISION_M
        
    ##########################################################################
    def onKey(self, event = None):
        keycode = event.GetKeyCode()
        try:
            keyname = chr(keycode)
        except:
            keyname = ""
            
        if keyname == "P":
            self.onPause(event)
            self.boutonPause.SetValue(self.pause)
        elif keyname == "T":
            self.onOptions(event)
        elif keyname == "O":
            self.onTarer(event)
        elif keyname == "Q":
            self.onClose(event)
        elif keycode == wx.WXK_UP:
            self.kR += PAS_R
        elif keycode == wx.WXK_DOWN:
            self.kR += -PAS_R  
        elif keycode == wx.WXK_LEFT:
            self.kM += -PAS_M
        elif keycode == wx.WXK_RIGHT:
            self.kM += PAS_M    
        elif keycode == wx.WXK_ESCAPE and self.pleinEcran:
            self.commandePleinEcran(event)
        event.Skip()
            


    ##########################################################################
    def onTarer(self, event = None):
        if hasattr(self, 'InterfaceDAQ'):
            self.InterfaceDAQ.tarer()
        self.pagePyStatic.onTarer()
#        self.SetFocus()
    
    ##########################################################################
    def onPause(self, event):
        self.pause = not self.pause
        if self.pause:
            print "Pause"
            if self.acquisition:
                self.t.Stop()
                self.nb.GetCurrentPage().OnPause(self.pause)
            self.boutonPause.SetShortHelp(u"Reprise")
            self.boutonPause.SetNormalBitmap(wx.Bitmap(os.path.join("Images", "Icone_play.png")))
            self.tb.Realize()
        else:
            print "Reprise"
            if self.acquisition:
                self.t.Start()
                self.nb.GetCurrentPage().OnPause(self.pause)
            self.boutonPause.SetShortHelp(u"Pause")
            self.boutonPause.SetNormalBitmap(wx.Bitmap(os.path.join("Images", "Icone_pause.png")),)
        event.Skip()
        self.tb.Realize()
#        self.SetFocus()
    
    ###########################################################################
    def onClose(self, event):
        """Called on application shutdown."""
        print "Fermeture"
        
        #
        # Arret du thread de lecture
        #
        self.t.Stop()

        #
        # Fermeture de l'interface d'acquisition
        #
        self.InterfaceDAQ.fermer()            #cleanup
            
        # 
        # Arret du thread de calcul pyStatic
        #
        self.pagePyStatic.OnClose()
            
        #
        # Fermeture de la fenêtre
        #
        self.Destroy()
        event.Skip()


    ###########################################################################
    def getRandomTorseur(self, tors):
        self.i = -1
        def modifier(v, coef = 1.0):
            self.i += 1
            return (v + ((random.random()-0.5)/5 + sin(PULS[self.i]*self.T)/10) * coef*2) 
        
        
        tors.setElementsRed(self.torsO)
        
        tors.R.x = modifier(self.torsO.R.x, 10)
        tors.R.y = modifier(self.torsO.R.y, 10)
        tors.R.z = modifier(self.torsO.R.z, 10)
        tors.M.x = modifier(self.torsO.M.x)
        tors.M.y = modifier(self.torsO.M.y)
        tors.M.z = modifier(self.torsO.M.z)
    
        return
        
    ###########################################################################
    def getClavierTorseur(self, tors):

        tors.setElementsRed(self.torsO)
        tors.R.z = self.kR
        tors.M.y = self.kM
 
        return
    
    ###########################################################################
    def getManuelTorseur(self, tors):

        tors = self.saisie.tors
#        tors.setElementsRed(self.torsO)
#        tors.R.z = self.kR
#        tors.M.y = self.kM
 
        return
    
    ###########################################################################
    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an
        # unmanaged toolbar in your frame
        return self.toolbar

    ###########################################################################
    def onVar(self, evt):
        self.saisie.OnVar(evt)
        self.onTimer(evt)
        
    ###########################################################################
    def onTimer(self, evt):
        """ Tout ce qui est fait par cycle ...
        """
#        print "onTimer"
        if self.pause:
            return
        
        self.getTorseur(self.torsO)
        
        self.tors = self.torsO.getCopy(self.tors.P)

        self.nb.GetCurrentPage().actualiser(self.tors, self.torsO)
        
        self.panelResultante.actualiser(self.tors.R)
        self.panelMoment.actualiser(self.tors.M)
        self.imgTorseur.SetBitmap(self.tors.getBitmap(ncR = PRECISION_R, ncM = PRECISION_M))
        self.imgTorseurO.SetBitmap(self.torsO.getBitmap(ncR = PRECISION_R, ncM = PRECISION_M))
        
        self.panelCommande.Layout()
        self.Layout()
        
#        self.SetFocus()


    ###########################################################################
    def onEraseBackground(self, evt):
        # this is supposed to prevent redraw flicker on some X servers...
        pass


    def OnPointRedModified(self):
        self.nb.GetCurrentPage().miseAJourPtRed(self.tors.P)
        self.onTimer(None)
        
#        self.tors.changerPtRed(self.panelPointRed.P)
    
    #############################################################################
    def quitter(self, event = None):
        try:
            self.options.enregistrer()
            print "Options enregistrées"
        except IOError:
            print "   Permission d'enregistrer les options refusée...",
        except:
            print "   Erreur enregistrement options...",
    
        self.pagePyStatic.StopperThread()
        self.Destroy()
        sys.exit()
        

        
#############################################################################################################
#############################################################################################################
#
#
#
#############################################################################################################
#############################################################################################################
class PanelTorseurs(wx.Panel):
    def __init__(self, parent, app):
        wx.Panel.__init__(self, parent, -1)
        
        
        self.app = app
        
        #
        # Les vecteurs à tracer
        #
        self.tracerActionOrig = False
        self.tracerResultantes = True
        self.tracerMoments = True
        self.tracerComposantes = True
        self.tracerValComp = True
        self.tracerNoms = True
        self.tracerAxeCentral = False
        
        #
        # Pour faire des Pan
        #
        self.panX, self.panY = None, None
        self.panAx = None
        
        #
        # Le type d'affichage simple vue ou multiples vues
        #
        multi = False
        self.multi = multi
        
        #
        # La figure Matplotlib
        #
        self.fig = Figure((5,5), 75)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)
        self.canvas.SetSize((400,400))
        self.InitDraw(multi)
        self.canvas.mpl_connect('scroll_event', self.OnWheel)
        self.canvas.mpl_connect('figure_enter_event', self.OnEnter)
        self.canvas.mpl_connect('pick_event', self.OnPick)
        self.canvas.mpl_connect('button_press_event', self.OnPress)
        self.canvas.mpl_connect('button_release_event', self.OnRelease)
        self.canvas.mpl_connect('motion_notify_event', self.OnMotion)
#        self.canvas.mpl_connect('draw_event', self.on_draw)
#        self.canvas.mpl_connect('resize_event', self.OnLimChanged)
        
    
        
        #
        # La barre d'outils
        #
        self.toolbar = MyCustomToolbar(self.canvas, self)
        self.toolbar.Realize()
        # On Windows, default frame size behaviour is incorrect
        # you don't need this under Linux
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        self.toolbar.SetSize(wx.Size(fw, th))
        
        
        #
        # La zone d'options
        #
        self.zoneOptions = wx.Panel(self, -1)
        opt1 = wx.CheckBox(self.zoneOptions, 1, u"torseur de l'action mécanique réduit à l'origine O")
        opt2 = wx.CheckBox(self.zoneOptions, 2, u"résultantes")
        opt3 = wx.CheckBox(self.zoneOptions, 3, u"moments")
        opt4 = wx.CheckBox(self.zoneOptions, 4, u"composantes des vecteurs")
        opt5 = wx.CheckBox(self.zoneOptions, 5, u"valeurs des composantes")
        opt6 = wx.CheckBox(self.zoneOptions, 6, u"noms des vecteurs")
        opt7 = wx.CheckBox(self.zoneOptions, 7, u"axe central des torseurs")
        
        opt2.SetValue(self.tracerResultantes)
        opt3.SetValue(self.tracerMoments)
        opt4.SetValue(self.tracerComposantes)
        opt5.SetValue(self.tracerValComp)
        opt6.SetValue(self.tracerNoms)
        opt7.SetValue(self.tracerAxeCentral)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox)
        
        bo = wx.StaticBox(self.zoneOptions, -1, u"Eléments à afficher")
        
        sb = wx.StaticBoxSizer(bo, wx.HORIZONTAL)
        
        sbo1 = wx.BoxSizer(wx.VERTICAL)
        sbo1.Add(opt1, flag = wx.ALL, border = 2)
        sbo1.Add(opt2, flag = wx.ALL, border = 2)
        sbo1.Add(opt3, flag = wx.ALL, border = 2)
        sbo1.Add(opt7, flag = wx.ALL, border = 2)
        
        sbo2 = wx.BoxSizer(wx.VERTICAL)
        sbo2.Add(opt4, flag = wx.ALL, border = 2)
        sbo2.Add(opt5, flag = wx.ALL, border = 2)
        sbo2.Add(opt6, flag = wx.ALL, border = 2)
        
        sb.Add(sbo1)
        sb.Add(sbo2)
        
        self.zoneOptions.SetSizer(sb)
        
        #
        # La zone Type d'affichage
        #
        self.zoneTypeAff = wx.Panel(self, -1)
        
        rb = wx.RadioBox(self.zoneTypeAff, -1, u"Type d'affichage", wx.DefaultPosition, wx.DefaultSize,
                         [u"1 vue", u"4 vues"], 1, wx.RA_SPECIFY_COLS
                         )
        rb.SetSelection(multi)
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)
        
        sizerbas = wx.BoxSizer(wx.HORIZONTAL)  
        sizerbas.Add(self.zoneOptions, flag = wx.GROW)
        sizerbas.Add(self.zoneTypeAff, flag = wx.GROW)
#        sizerbas.Fit()
        
        #
        # Mise en place
        #
        sizer = wx.BoxSizer(wx.VERTICAL)   
        sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.GROW)
        sizer.Add(sizerbas, 0, wx.GROW)
        self.SetSizer(sizer)
        
        
#        self.canvas.draw()
#        wx.CallAfter(self.calculerMargesFigure)
#        self.canvas.draw()
        
        self.Bind(wx.EVT_SIZE, self.OnLimChanged)
        
        
    ######################################################################################################
    def setLimites(self, multi):
        """ Applique les limites à tous les axes visibles
        """
        if multi:
            # limites des axes 2D
            self.axes['f'].set_xlim(LIMITE_Y0, LIMITE_Y1)
            self.axes['f'].set_ylim(LIMITE_Z0, LIMITE_Z1)
            self.axes['g'].set_xlim(LIMITE_X0, LIMITE_X1)
            self.axes['d'].set_ylim(LIMITE_X1, LIMITE_X0)
        
        self.ax.set_xlim3d(LIMITE_X0, LIMITE_X1)
        self.ax.set_ylim3d(LIMITE_Y0, LIMITE_Y1)
        self.ax.set_zlim3d(LIMITE_Z0, LIMITE_Z1)
        
        
    ######################################################################################################
    def setEchelles(self, multi):
        """ Applique les échelles aux vecteurs
        """
        if multi:
            er = ECHELLE_R/2
            em = ECHELLE_M/2
            for vue in self.vues:        
                self.vectR[vue].setEchelle(er)
                self.vectM[vue].setEchelle(em)
                self.vectRO[vue].setEchelle(er)
                self.vectMO[vue].setEchelle(em)
        else:
            er = ECHELLE_R
            em = ECHELLE_M
            
        self.vectResultante.setEchelle(er)
        self.vectResultanteO.setEchelle(er)
        self.vectMoment.setEchelle(em)
        self.vectMomentO.setEchelle(em)
        
        
        
        
    ######################################################################################################
    def InitDraw(self, multi):
        """ Initialise les axes
            (pour un passage de 1 à 4 vues)
        """
        
        if multi:
            self.vues = ['f', 'g', 'd']
            self.axes = {}
            m = 2
            # Face
            self.axes['f'] = self.fig.add_subplot(221, aspect='equal', adjustable = 'datalim', anchor = 'C')
            self.axes['f'].set_xlabel("y")
            self.axes['f'].set_ylabel("z")
            self.axes['f'].get_xaxis().set_ticks_position('top')
            self.axes['f'].get_xaxis().set_label_position('top')
            self.axes['f'].get_yaxis().get_label().set_rotation(0) 
            self.axes['f'].spines['bottom'].set_visible(True)
#            self.axes['f'].set_aspect('equal', 'datalim')
            
            # Gauche
            self.axes['g'] = self.fig.add_subplot(222, sharey = self.axes['f'], aspect='equal', adjustable = 'datalim', anchor = 'C')
            self.axes['g'].set_xlabel("x")
            self.axes['g'].set_ylabel("z")
            self.axes['g'].get_xaxis().set_ticks_position('top')
            self.axes['g'].get_xaxis().set_label_position('top')
            self.axes['g'].get_yaxis().set_ticks_position('right')
            self.axes['g'].get_yaxis().set_label_position('right')
            self.axes['g'].get_yaxis().get_label().set_rotation(0) 
#            self.axes['g'].set_aspect('equal', 'datalim')
            
            # Dessus
            self.axes['d'] = self.fig.add_subplot(223, sharex = self.axes['f'], aspect='equal', adjustable = 'datalim', anchor = 'C')
            self.axes['d'].set_xlabel("y")
            self.axes['d'].set_ylabel("x")
            self.axes['d'].get_yaxis().get_label().set_rotation(0) 
#            self.axes['d'].set_aspect('equal', 'datalim')
            
            # 3D
            self.ax = self.fig.add_subplot(224, projection='3d')#, aspect='equal')
            self.fig.axes.pop()
            
            # Taille des caractères
            setp(self.axes['f'].get_xaxis().get_ticklabels(), fontsize = TAILLE_TICKS/2)
            setp(self.axes['g'].get_xaxis().get_ticklabels(), fontsize = TAILLE_TICKS/2)
            setp(self.axes['d'].get_xaxis().get_ticklabels(), fontsize = TAILLE_TICKS/2)
            setp(self.axes['f'].get_yaxis().get_ticklabels(), fontsize = TAILLE_TICKS/2)
            setp(self.axes['g'].get_yaxis().get_ticklabels(), fontsize = TAILLE_TICKS/2)
            setp(self.axes['d'].get_yaxis().get_ticklabels(), fontsize = TAILLE_TICKS/2)
            setp(self.ax.w_xaxis.get_ticklabels(), fontsize=TAILLE_TICKS/2)
            setp(self.ax.w_yaxis.get_ticklabels(), fontsize=TAILLE_TICKS/2)
            setp(self.ax.w_zaxis.get_ticklabels(), fontsize=TAILLE_TICKS/2)
            
            self.fig.subplots_adjust(left=0, bottom=0.1, right=0.9, top=1,wspace=0.05, hspace=0.05)
            

        else:
            m = 1
            self.ax = self.fig.add_subplot(111, projection='3d')#, aspect='equal')
            self.fig.axes.pop()
            setp(self.ax.w_xaxis.get_ticklabels(), fontsize=TAILLE_TICKS)
            setp(self.ax.w_yaxis.get_ticklabels(), fontsize=TAILLE_TICKS)
            setp(self.ax.w_zaxis.get_ticklabels(), fontsize=TAILLE_TICKS)
            self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
                                                       
        self.ax.set_xlabel('x', x = 0, y = 0)
        self.ax.set_ylabel('y')
        self.ax.set_zlabel('z')
        self.ax.set_aspect('equal', 'datalim')
#        self.ax.pbaspect = [1.0, 1.0, 1.0]
        
        self.setLimites(multi)
        
        self.ax.set_autoscale_on(False)
        
        if multi:
            self.vectR = {}
            self.vectRO = {}
            self.vectM = {}
            self.vectMO = {}
            self.axeC = {}
            
            for vue in self.vues:
                self.vectR[vue] = MPLVecteur2D(self.axes[vue], vue = vue, coul = COUL_RESULTANTE.GetAsString(wx.C2S_HTML_SYNTAX), 
                                                   nom = r"$\vec{R}$", echelle = ECHELLE_R/m, 
                                                   visible = self.tracerResultantes, nc = PRECISION_R)
                self.vectRO[vue] = MPLVecteur2D(self.axes[vue], vue = vue, coul = COUL_RESULTANTE.GetAsString(wx.C2S_HTML_SYNTAX), 
                                                   nom = r"$\vec{R}$", echelle = ECHELLE_R/m, 
                                                   visible = self.tracerResultantes * self.tracerActionOrig, nc = PRECISION_R)
                self.vectM[vue] = MPLVecteur2D(self.axes[vue], vue = vue, coul = COUL_MOMENT.GetAsString(wx.C2S_HTML_SYNTAX), 
                                               nom = r"$\vec{M}_P$", echelle = ECHELLE_M/m, 
                                                   visible = self.tracerMoments, nc = PRECISION_M)
                self.vectMO[vue] = MPLVecteur2D(self.axes[vue], vue = vue, coul = COUL_MOMENT.GetAsString(wx.C2S_HTML_SYNTAX), 
                                                nom = r"$\vec{M}_O$", echelle = ECHELLE_M/m, 
                                                   visible = self.tracerMoments * self.tracerActionOrig, nc = PRECISION_M)
                
                self.axeC[vue] = MPLDroite2D(self.axes[vue], vue = vue)
        
        
        self.vectResultante = MPLVecteur3D(self.ax, coul = COUL_RESULTANTE.GetAsString(wx.C2S_HTML_SYNTAX), 
                                           nom = r"$\vec{R}$", echelle = ECHELLE_R/m, 
                                           visible = self.tracerResultantes, nc = PRECISION_R)
        self.vectResultanteO = MPLVecteur3D(self.ax, coul = COUL_RESULTANTE.GetAsString(wx.C2S_HTML_SYNTAX), 
                                           nom = r"$\vec{R}$", echelle = ECHELLE_R/m, 
                                           visible = self.tracerResultantes * self.tracerActionOrig, nc = PRECISION_R)
        self.vectMoment = MPLVecteur3D(self.ax, coul = COUL_MOMENT.GetAsString(wx.C2S_HTML_SYNTAX), 
                                       nom = r"$\vec{M}_P$", echelle = ECHELLE_M/m, 
                                           visible = self.tracerMoments, nc = PRECISION_M)
        self.vectMomentO = MPLVecteur3D(self.ax, coul = COUL_MOMENT.GetAsString(wx.C2S_HTML_SYNTAX), 
                                        nom = r"$\vec{M}_O$", echelle = ECHELLE_M/m, 
                                           visible = self.tracerMoments * self.tracerActionOrig, nc = PRECISION_M)
        
        self.axeCentral = MPLDroite3D(self.ax)
        
        #
        # les points à tracer
        #
        if multi:
            self.pointO = {}
            self.pointR = {}
            for vue in self.vues:
                self.pointO[vue] = MPLPoint2D(self.axes[vue], point = Point(), vue = vue, coul = "b", nom = "O")
                self.pointR[vue] = MPLPoint2D(self.axes[vue], point = Point(), vue = vue, coul = "b", nom = "P")
                self.pointO[vue].draw()
                self.pointR[vue].draw()
                
        self.pointOrig = MPLPoint3D(self.ax, point = Point(), coul = "b", nom = "O")
        self.pointRed  = MPLPoint3D(self.ax, point = Point(), coul = "b", nom = "P")
        self.pointOrig.draw(multi = multi)
        self.pointRed.draw(multi = multi)
        
        self.miseAJourPtRed(self.app.tors.P)
#        for ax in self.fig.axes:
#            ax.callbacks.connect('xlim_changed', self.OnLimChanged)
#            ax.callbacks.connect('ylim_changed', self.OnLimChanged)
        
        #
        # Le "cube" pour fixer l'aspect 
        #
        lx = []
        ly = []
        lz = []
        for x in [0,1]:
            for y in [0,1]:
                for z in [0,1]:
                    lx.append(100*(x-0.5))
                    ly.append(100*(y-0.5))
                    lz.append(100*(z-0.5))
        self.cube = self.ax.plot(lx, ly, lz, 
                                 mfc = (1,0,0), marker = 'o', visible = False)
        
        
        self.regleVisibilites()
        

        
    ######################################################################################################
    def MisesAJourMarges(self):    
        self.pointOrig.decaleTexte()
        self.pointRed.decaleTexte()
        for vue in self.vues:
            self.pointR[vue].decaleTexte()
            self.pointO[vue].decaleTexte()

        self.fig.tight_layout()
        
        
    ######################################################################################################
    def OnLimChanged(self, event):
        event.Skip()        
        if self.multi:
            wx.CallAfter(self.MisesAJourMarges)
            wx.CallAfter(self.rectifierLimites)
            
    ######################################################################################################
    def rectifierLimites(self):
        """ Corrige les limites des 3 axes 2D
            pour corriger le découpage créé par l'aspect "equal'
        """
                
        def rectifierLim(axe, limitesX, limitesY):
            ly = axe.get_ylim()
            lx = axe.get_xlim()
            
            dX = limitesX[1] - limitesX[0]
            dY = limitesY[1] - limitesY[0]
            
            dx = lx[1] - lx[0]
            dy = ly[1] - ly[0]
            
            if dX/dY < dx/dy:
                dx = dx/dy*dY/2
                m = (limitesX[1] + limitesX[0])/2
                Lx = [m-dx, m+dx]
                axe.set_xlim(Lx)
            
            if dX/dY > dx/dy:
                dx = dy/dx*dX/2
                m = (limitesY[1] + limitesY[0])/2
                Ly = [m-dy, m+dy]
                axe.set_ylim(Ly)
                
        
        rectifierLim(self.axes['f'], (LIMITE_Y0, LIMITE_Y1), (LIMITE_Z0, LIMITE_Z1))
        rectifierLim(self.axes['g'], (LIMITE_X0, LIMITE_X1), (LIMITE_Z0, LIMITE_Z1))
        rectifierLim(self.axes['d'], (LIMITE_Y0, LIMITE_Y1), (LIMITE_X1, LIMITE_X0))
        
        self.canvas.draw()
        
    
    ######################################################################################################
    def EvtRadioBox(self, event):
        self.multi = event.GetInt() != 0
        
        self.fig.clf(keep_observers = True)
        self.InitDraw(self.multi)
        
        if self.multi:
            self.MisesAJourMarges()
        
        self.actualiser(self.app.tors, self.app.torsO)
        
        
    ######################################################################################################
    def OnPress(self, event):
        if event.button ==1:
            if self.multi and event.inaxes in self.axes.values():
                self.panX, self.panY = event.xdata, event.ydata
                self.panAx = event.inaxes
                
                
    ######################################################################################################
    def OnRelease(self, event):
        if event.button ==1:
            self.panX, self.panY = None, None
            self.panAx = None
                      
    ######################################################################################################
    def OnMotion(self, event):
        global LIMITE_X0, LIMITE_X1, LIMITE_Y0, LIMITE_Y1, LIMITE_Z0, LIMITE_Z1
        if self.panAx != None and event.inaxes == self.panAx:
            x, y = event.xdata, event.ydata
            dx, dy = x-self.panX, y-self.panY
            if self.panAx == self.axes['f']:
                LIMITE_Y0, LIMITE_Y1 = LIMITE_Y0-dx, LIMITE_Y1-dx
                LIMITE_Z0, LIMITE_Z1 = LIMITE_Z0-dy, LIMITE_Z1-dy
            elif self.panAx == self.axes['g']:
                LIMITE_X0, LIMITE_X1 = LIMITE_X0-dx, LIMITE_X1-dx
                LIMITE_Z0, LIMITE_Z1 = LIMITE_Z0-dy, LIMITE_Z1-dy
            elif self.panAx == self.axes['d']:
                LIMITE_X1, LIMITE_X0 = LIMITE_X1-dy, LIMITE_X0-dy
                LIMITE_Y0, LIMITE_Y1 = LIMITE_Y0-dx, LIMITE_Y1-dx
            
            self.drawNouvLimites()
            
    ######################################################################################################
    def OnPick(self, event):
        if event.mouseevent.button !=1:
            return
        
        global LIMITE_X0, LIMITE_X1, LIMITE_Y0, LIMITE_Y1, LIMITE_Z0, LIMITE_Z1
        art = event.artist
        
        def decaleAxe(range, centre):
            m = (range[1]+range[0])/2
            d = centre-m
            return range[0]+d, range[1]+d
        
        if hasattr(art, "_verts3d"):
            xdata, ydata, zdata = art._verts3d
            x, y, z = xdata[0], ydata[0], zdata[0]

            LIMITE_X0, LIMITE_X1 = decaleAxe([LIMITE_X0, LIMITE_X1], x)
            LIMITE_Y0, LIMITE_Y1 = decaleAxe([LIMITE_Y0, LIMITE_Y1], y)
            LIMITE_Z0, LIMITE_Z1 = decaleAxe([LIMITE_Z0, LIMITE_Z1], z)
        else:
            x, y = art.get_xdata()[0], art.get_ydata()[0]
            axe = art.get_axes()
            if axe == self.axes['f']:
                LIMITE_Y0, LIMITE_Y1 = decaleAxe([LIMITE_Y0, LIMITE_Y1], x)
                LIMITE_Z0, LIMITE_Z1 = decaleAxe([LIMITE_Z0, LIMITE_Z1], y)
            elif axe == self.axes['g']:
                LIMITE_X0, LIMITE_X1 = decaleAxe([LIMITE_X0, LIMITE_X1], x)
                LIMITE_Z0, LIMITE_Z1 = decaleAxe([LIMITE_Z0, LIMITE_Z1], y)
            else:
                LIMITE_X1, LIMITE_X0 = decaleAxe([LIMITE_X1, LIMITE_X0], y)
                LIMITE_Y0, LIMITE_Y1 = decaleAxe([LIMITE_Y0, LIMITE_Y1], x)
                
        self.drawNouvLimites()
        
        
    ######################################################################################################
    def drawNouvLimites(self):
        """ Applique les nouvelles limites aux axes et echelles aux vecteurs ...
            ... et redessine tout.
        """
        self.setLimites(self.multi)
        self.setEchelles(self.multi)
        
#        self.pointRed.regleVisibilite()
#        self.pointOrig.regleVisibilite()
        
        if hasattr(self, 'tors'):
            self.vectResultante.draw(o = self.tors.P, multi = self.multi)
            self.vectMoment.draw(o = self.tors.P, multi = self.multi)
        
        if self.tracerActionOrig:
            self.vectResultanteO.draw(multi = self.multi)
            self.vectMomentO.draw(multi = self.multi)
            
        if self.multi:
            for vue in self.vues:
                self.pointR[vue].regleVisibilite()
                self.pointO[vue].regleVisibilite()
                if self.tracerActionOrig:      
                    self.vectRO[vue].draw(o = self.torsO.P)
                    self.vectMO[vue].draw(o = self.torsO.P)
                
                if hasattr(self, 'tors'):
                    self.vectR[vue].draw(o = self.tors.P)
                    self.vectM[vue].draw(o = self.tors.P)
        
        
        if self.tracerAxeCentral:
            self.axeCentral.draw()
            if self.multi:
                for vue in self.vues:
                    self.axeC[vue].draw(vect = [self.vectRO[vue],self.vectMO[vue]] )             
        
        #
        # Tracé du cube d'encombrement
        #
        lx = []
        ly = []
        lz = []
        for x in [LIMITE_X0, LIMITE_X1]:
            for y in [LIMITE_Y0, LIMITE_Y1]:
                for z in [LIMITE_Z0, LIMITE_Z1]:
                    lx.append(x)
                    ly.append(y)
                    lz.append(z)
        self.cube[0].set_xdata(lx)
        self.cube[0].set_ydata(ly)
        self.cube[0].set_3d_properties(zs = lz)
        
        self.canvas.draw()
        
    

    ######################################################################################################
    def zoomTout(self):
        global LIMITE_X0, LIMITE_X1, LIMITE_Y0, LIMITE_Y1, LIMITE_Z0, LIMITE_Z1
        xr, yr, zr = self.vectResultante.get_data_lim()
        xm, ym, zm = self.vectMoment.get_data_lim()
        xp, yp, zp = self.pointRed.get_data_lim()
        x0, y0, z0 = self.pointOrig.get_data_lim()
        
        if self.tracerActionOrig:
            xr0, yr0, zr0 = self.vectResultanteO.get_data_lim()
            xm0, ym0, zm0 = self.vectMomentO.get_data_lim()
        else:
            xr0, yr0, zr0 = [], [], []
            xm0, ym0, zm0 = [], [], []
            
        x = xr + xm + xp + xr0 + xm0 + x0
        y = yr + ym + yp + yr0 + ym0 + y0
        z = zr + zm + zp + zr0 + zm0 + z0
        
        LIMITE_X0 = min(x)
        LIMITE_Y0 = min(y)
        LIMITE_Z0 = min(z)
        LIMITE_X1 = max(x)
        LIMITE_Y1 = max(y)
        LIMITE_Z1 = max(z)
        
        dx, dy, dz = LIMITE_X1-LIMITE_X0, LIMITE_Y1-LIMITE_Y0, LIMITE_Z1-LIMITE_Z0
        d = max([dx, dy, dz])/2
        mx, my, mz = (LIMITE_X1+LIMITE_X0)/2, (LIMITE_Y1+LIMITE_Y0)/2, (LIMITE_Z1+LIMITE_Z0)/2
        
        LIMITE_X0 = mx-d
        LIMITE_X1 = mx+d
        LIMITE_Y0 = my-d
        LIMITE_Y1 = my+d
        LIMITE_Z0 = mz-d
        LIMITE_Z1 = mz+d
        
        r = 10
        e = max(5, d/r)
        
        LIMITE_X0 = LIMITE_X0 - e
        LIMITE_Y0 = LIMITE_Y0 - e
        LIMITE_Z0 = LIMITE_Z0 - e
        LIMITE_X1 = LIMITE_X1 + e
        LIMITE_Y1 = LIMITE_Y1 + e
        LIMITE_Z1 = LIMITE_Z1 + e
        
        self.drawNouvLimites()
        
        if self.multi:
            self.rectifierLimites()
        
        
    ######################################################################################################
    def OnEnter(self, event = None):
        self.SetFocus()
        
    #########################################################################################################
    def OnWheel(self, event):
        global ECHELLE_M, ECHELLE_R, \
               LIMITE_X0, LIMITE_X1, LIMITE_Y0, LIMITE_Y1, LIMITE_Z0, LIMITE_Z1
               
        step = event.step
        coef = exp(step/100)
        
        def getEchelleAxe(coef, rng, centre):
            L0 = centre - (centre-rng[0])*coef
            L1 = centre - (centre-rng[1])*coef
            return L0, L1
        
        if event.inaxes == self.ax:
            x, y, z = self.coord3D(event.xdata, event.ydata)
            
            LIMITE_X0, LIMITE_X1 = getEchelleAxe(coef, [LIMITE_X0, LIMITE_X1], x)
            LIMITE_Y0, LIMITE_Y1 = getEchelleAxe(coef, [LIMITE_Y0, LIMITE_Y1], y)
            LIMITE_Z0, LIMITE_Z1 = getEchelleAxe(coef, [LIMITE_Z0, LIMITE_Z1], z)
            
            ECHELLE_R = ECHELLE_R*coef
            ECHELLE_M = ECHELLE_M*coef
            
            self.drawNouvLimites()
            
        elif event.inaxes in self.axes.values():
            x, y = event.xdata, event.ydata

            if event.inaxes == self.axes['f']:
                LIMITE_Y0, LIMITE_Y1 = getEchelleAxe(coef, [LIMITE_Y0, LIMITE_Y1], x)
                LIMITE_Z0, LIMITE_Z1 = getEchelleAxe(coef, [LIMITE_Z0, LIMITE_Z1], y)
            elif event.inaxes == self.axes['g']:
                LIMITE_X0, LIMITE_X1 = getEchelleAxe(coef, [LIMITE_X0, LIMITE_X1], x)
                LIMITE_Z0, LIMITE_Z1 = getEchelleAxe(coef, [LIMITE_Z0, LIMITE_Z1], y)
            else:
                LIMITE_X1, LIMITE_X0 = getEchelleAxe(coef, [LIMITE_X1, LIMITE_X0], y)
                LIMITE_Y0, LIMITE_Y1 = getEchelleAxe(coef, [LIMITE_Y0, LIMITE_Y1], x)
                
            ECHELLE_R = ECHELLE_R*coef
            ECHELLE_M = ECHELLE_M*coef
            
            self.drawNouvLimites()
            
        else:
            return
            
        
    #########################################################################################################
    def EvtCheckBox(self, event):
        id = event.GetId()
        if id == 1:
            self.tracerActionOrig = event.IsChecked()
            
        elif id == 2:
            self.tracerResultantes = event.IsChecked()
        
        elif id == 3:
            self.tracerMoments = event.IsChecked()
            
        elif id == 4:
            self.tracerComposantes = event.IsChecked()
            
        elif id == 5:
            self.tracerValComp = event.IsChecked() 
              
        elif id == 6:
            self.tracerNoms = event.IsChecked() 
            
        elif id == 7:
            self.tracerAxeCentral = event.IsChecked() 
        
        self.regleVisibilites()
        
        
    #########################################################################################################
    def regleVisibilites(self):
        if self.multi:
            for vue in self.vues:
                self.vectRO[vue].set_visible(self.tracerActionOrig * self.tracerResultantes)
                self.vectMO[vue].set_visible(self.tracerActionOrig * self.tracerMoments)
                self.vectR[vue].set_visible(self.tracerResultantes)
                self.vectM[vue].set_visible(self.tracerMoments)
                    
                self.vectM[vue].set_visible_comp(self.tracerComposantes * self.tracerMoments)
                self.vectMO[vue].set_visible_comp(self.tracerComposantes * self.tracerActionOrig* self.tracerMoments)
                self.vectR[vue].set_visible_comp(self.tracerComposantes * self.tracerResultantes)
                self.vectRO[vue].set_visible_comp(self.tracerComposantes * self.tracerActionOrig * self.tracerResultantes)
                
                self.vectM[vue].set_visible_valcomp(self.tracerComposantes * self.tracerMoments * self.tracerValComp)
                self.vectMO[vue].set_visible_valcomp(self.tracerComposantes * self.tracerActionOrig* self.tracerMoments* self.tracerValComp)
                self.vectR[vue].set_visible_valcomp(self.tracerComposantes * self.tracerResultantes * self.tracerValComp)
                self.vectRO[vue].set_visible_valcomp(self.tracerComposantes * self.tracerActionOrig * self.tracerResultantes * self.tracerValComp)
                     
                self.vectM[vue].set_visible_nom(self.tracerNoms * self.tracerMoments)
                self.vectMO[vue].set_visible_nom(self.tracerNoms * self.tracerActionOrig * self.tracerMoments)
                self.vectR[vue].set_visible_nom(self.tracerNoms * self.tracerResultantes)
                self.vectRO[vue].set_visible_nom(self.tracerNoms * self.tracerActionOrig * self.tracerResultantes)
                
                self.axeC[vue].set_visible(self.tracerAxeCentral)
                
        self.vectResultanteO.set_visible(self.tracerActionOrig * self.tracerResultantes)
        self.vectMomentO.set_visible(self.tracerActionOrig * self.tracerMoments)
        self.vectResultante.set_visible(self.tracerResultantes)
        self.vectMoment.set_visible(self.tracerMoments)
            
        self.vectMoment.set_visible_comp(self.tracerComposantes * self.tracerMoments)
        self.vectMomentO.set_visible_comp(self.tracerComposantes * self.tracerActionOrig* self.tracerMoments)
        self.vectResultante.set_visible_comp(self.tracerComposantes * self.tracerResultantes)
        self.vectResultanteO.set_visible_comp(self.tracerComposantes * self.tracerActionOrig * self.tracerResultantes)
        
        self.vectMoment.set_visible_valcomp(self.tracerComposantes * self.tracerMoments * self.tracerValComp)
        self.vectMomentO.set_visible_valcomp(self.tracerComposantes * self.tracerActionOrig* self.tracerMoments* self.tracerValComp)
        self.vectResultante.set_visible_valcomp(self.tracerComposantes * self.tracerResultantes * self.tracerValComp)
        self.vectResultanteO.set_visible_valcomp(self.tracerComposantes * self.tracerActionOrig * self.tracerResultantes * self.tracerValComp)
             
        self.vectMoment.set_visible_nom(self.tracerNoms * self.tracerMoments)
        self.vectMomentO.set_visible_nom(self.tracerNoms * self.tracerActionOrig * self.tracerMoments)
        self.vectResultante.set_visible_nom(self.tracerNoms * self.tracerResultantes)
        self.vectResultanteO.set_visible_nom(self.tracerNoms * self.tracerActionOrig * self.tracerResultantes)
        
        self.axeCentral.set_visible(self.tracerAxeCentral)
            
        self.actualiser(self.app.tors, self.app.torsO)
        
        self.canvas.draw()
        

    #########################################################################################################
    def drawNouvOptions(self):
        self.setEchelles(self.multi)


    #########################################################################################################
    def actualiser(self, tors, torsO = None):
        
        def getAncres(vect):
            if vect.z > 0 :
                av1 = 'top'
                av2 = 'bottom'
            else:
                av2 = 'top'
                av1 = 'bottom'
                
            if vect.x > 0:
                ah1 = 'left'
                ah2 = 'right'
            else:
                ah1 = 'right'
                ah2 = 'left'
                
            return [ah1, av1], [ah2, av2]
        
        self.vectResultante.setComp(tors.R)
        self.vectResultante.draw( o = tors.P, multi = self.multi)
        self.vectMoment.setComp(tors.M)
        self.vectMoment.draw( o = tors.P, multi = self.multi)
        self.pointRed.draw(vect = [self.vectResultante, self.vectMoment], multi = self.multi)   
        
        if self.multi:
            for vue in self.vues:
                self.vectR[vue].setComp(tors.R)
                self.vectR[vue].draw( o = tors.P)
                self.vectM[vue].setComp(tors.M)
                self.vectM[vue].draw( o = tors.P)
                self.pointR[vue].draw(vect = [self.vectR[vue], self.vectM[vue]])    
                
                
        if self.tracerActionOrig and torsO != None:
            self.vectResultanteO.setComp(torsO.R)
            self.vectResultanteO.draw(multi = self.multi)
            self.vectMomentO.setComp(torsO.M)
            self.vectMomentO.draw(multi = self.multi)
            self.pointOrig.draw(vect = [self.vectResultanteO, self.vectMomentO], multi = self.multi)   
            if self.multi:
                for vue in self.vues:
                    self.vectRO[vue].setComp(torsO.R)
                    self.vectRO[vue].draw(o = torsO.P)
                    self.vectMO[vue].setComp(torsO.M)
                    self.vectMO[vue].draw(o = torsO.P)
                    self.pointO[vue].draw(vect = [self.vectRO[vue],self.vectMO[vue]] )    
                    
        if self.tracerAxeCentral:
            self.axeCentral.setComp(tors.getAxeCentral())
            self.axeCentral.draw()
            if self.multi:
                for vue in self.vues:
                    self.axeC[vue].setComp(tors.getAxeCentral())
                    self.axeC[vue].draw()
#                    
                    
        
        self.tors = tors
        self.torsO = torsO
        
        self.canvas.draw()





#        self.OnEnter()
#        self.Refresh()

#    #########################################################################################################
#    def actualiser2(self, tors, torsO = None):
#        
#        def getAncres(vect):
#            if vect.z > 0 :
#                av1 = 'top'
#                av2 = 'bottom'
#            else:
#                av2 = 'top'
#                av1 = 'bottom'
#          
#            if vect.x > 0:
#                ah1 = 'left'
#                ah2 = 'right'
#            else:
#                ah1 = 'right'
#                ah2 = 'left'
#                
#            return [ah1, av1], [ah2, av2]
#        
##        print  tors.P
#        self.ax.cla()
#        self.ax.set_autoscale_on(False)
#        lim = 0.3
#        self.ax.set_xlim3d(-lim, lim)
#        self.ax.set_ylim3d(-lim, lim)
#        self.ax.set_zlim3d(-lim, lim)
#        
#        if self.tracerResultantes:
#            self.vectResultante.setComp(tors.R)
#            self.vectResultante.draw(self.ax, o = tors.P, ancre = getAncres(tors.R)[0])
#        
#        if self.tracerMoments:
#            self.vectMoment.setComp(tors.M)
#            self.vectMoment.draw(self.ax, o = tors.P)
#        
#        self.pointRed.point = tors.P
#        self.pointRed.draw(self.ax)
#        self.pointOrig.draw(self.ax)
###        self.ax.redraw_in_frame()
#
#        if self.tracerActionOrig and torsO != None:
#            if self.tracerResultantes:
#                self.vectResultante.draw(self.ax)
#            if self.tracerMoments:
#                self.vectMomentO.setComp(torsO.M)
#                self.vectMomentO.draw(self.ax)
#            
#        self.canvas.draw()
#        self.Refresh()
#        
        
    #########################################################################################################
    def OnPause(self, etat):
        
        return
    
    #########################################################################################################
    def miseAJourPtRed(self, P):
#        self.pointRed.remove()
        self.pointRed.point = P
        self.pointRed.draw(multi = self.multi)
        if self.multi:
            for vue in self.vues:
                self.pointR[vue].point = P
                self.pointR[vue].draw()
        return
    
    #########################################################################################################
    def coord3D(self, xd, yd):
        """Given the 2D view coordinates attempt to guess a 3D coordinate

        Looks for the nearest edge to the point and then assumes that the point is
        at the same z location as the nearest point on the edge.
        """
        p = (xd,yd)
        edges = self.ax.tunit_edges()
        #lines = [proj3d.line2d(p0,p1) for (p0,p1) in edges]
        ldists = [(proj3d.line2d_seg_dist(p0,p1,p),i) for i,(p0,p1) in enumerate(edges)]
        ldists.sort()
        # nearest edge
        edgei = ldists[0][1]
        #
        p0,p1 = edges[edgei]
        
        # scale the z value to match 
        x0,y0,z0 = p0
        x1,y1,z1 = p1
        d0 = np.hypot(x0-xd,y0-yd)
        d1 = np.hypot(x1-xd,y1-yd)
        dt = d0+d1
        z = d1/dt * z0 + d0/dt * z1
        #print 'mid', edgei, d0, d1, z0, z1, z

        x,y,z = proj3d.inv_transform(xd,yd,z,self.ax.get_proj())

        return  x, y, z
    
#############################################################################################################
#############################################################################################################
#
#
#
#############################################################################################################
#############################################################################################################
class PanelPyStatic(wx.Panel):
    def __init__(self, parent, app):
        wx.Panel.__init__(self, parent, -1, size = (600,600))
        
        self.parent = parent
        self.app = app
        
        self.Pause = False
        
        self.chrono = Chronometre()
        self.afficherChrono = True
        
        #
        # Légendes des poins et vecteurs
        #
        self.legender = True
        self._G = mathtext_to_wxbitmap(r"$G$", taille = 80)
        self._P = mathtext_to_wxbitmap(r"$P$", taille = 80)
        self._vM = mathtext_to_wxbitmap(r'$\vec{M}_P$', taille = 80)
        self._vR = mathtext_to_wxbitmap(r'$\vec{R}$', taille = 80)
        self._vP = mathtext_to_wxbitmap(r'$\vec{P}$', taille = 80)
        
        #
        # La Barre ...
        #
        self.barre = Barre(self)
        
        #
        # La zone de dessin de la barre
        #
        self.maxWidth, self.maxHeight = 600,400
        self.zoneDessin = wx.Panel(self, -1, size = (self.maxWidth, self.maxHeight))
        self.echelle_force = 4
        self.echelle_dim = 200  # 1 mètre --> "echelle_dim" pixels
        
        
        #
        # la zone des paramètres
        #
        self.zoneParam = wx.Panel(self, -1)
        
        boxp  = wx.StaticBox(self.zoneParam, -1, u"Paramètres")
        sboxp = wx.StaticBoxSizer(boxp)
        
        sli1 = TextSlider(self.zoneParam, u"Position de la main", 0, -5, 5, self.OnSliderPosX, 20.0, unite = u'%')
        sli2 = TextSlider(self.zoneParam, u"Longeur de la barre", self.barre.LONGUEUR_BARRE*8, 0, 8, self.OnSliderLong, 1.0/8, unite = u'm')
        sli3 = TextSlider(self.zoneParam, u"Espace vertical", self.barre.H_PLAFOND*10, 2, 15, self.OnSliderPlaf, 0.1, unite = u'm')
        sli4 = TextSlider(self.zoneParam, u"Masse de la barre", self.barre.MASSE*10, 1, 20, self.OnSliderMasse, 0.1, unite = u'kg')
        
        sizerP = wx.BoxSizer(wx.VERTICAL)
        sizerP.Add(sli1)
        sizerP.Add(sli2)
        sizerP.Add(sli3)
        sizerP.Add(sli4)
        
        sboxp.Add(sizerP)
        
        boxa = wx.StaticBox(self.zoneParam, -1, u"Actions mécaniques")
        sboxa = wx.StaticBoxSizer(boxa)
        
        self.textPoids  = StaticTextValeur(self.zoneParam, r"$\parallel\vec{P}\parallel=$", 0, u"N")
        self.textResult = StaticTextValeur(self.zoneParam, r"$\parallel\vec{R}\parallel=$", 0, u"N")
        self.textMoment = StaticTextValeur(self.zoneParam, r"$\parallel\vec{M}_P\parallel=$", 0, u"Nm")
        self.miseAJourValeurAction()
        
        sizerP = wx.BoxSizer(wx.VERTICAL)
        sizerP.Add(self.textPoids , flag = wx.EXPAND|wx.ALL, border = 2)
        sizerP.Add(self.textResult, flag = wx.EXPAND|wx.ALL, border = 2)
        sizerP.Add(self.textMoment, flag = wx.EXPAND|wx.ALL, border = 2)
        
        sboxa.Add(sizerP)
        
        boxo = wx.StaticBox(self.zoneParam, -1, u"Options")
        sboxo = wx.StaticBoxSizer(boxo)
    
        opt1 = wx.CheckBox(self.zoneParam, 10, u"Afficher une légende")
        opt1.SetValue(self.legender)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox)
        opt2 = wx.CheckBox(self.zoneParam, 11, u"Afficher le chronomètre")
        opt2.SetValue(self.legender)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox)
        
        sizerP = wx.BoxSizer(wx.VERTICAL)
        sizerP.Add(opt1, flag = wx.EXPAND|wx.ALL, border = 2)
        sizerP.Add(opt2, flag = wx.EXPAND|wx.ALL, border = 2)
        
        sboxo.Add(sizerP)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(sboxp,2, flag = wx.EXPAND|wx.ALL, border = 2)
        sz.Add(sboxa,1, flag = wx.EXPAND|wx.ALL, border = 2)
        sz.Add(sboxo,1, flag = wx.EXPAND|wx.ALL, border = 2)
        self.zoneParam.SetSizer(sz)
        
        self.centre = wx.Point(self.zoneDessin.GetSize()[0]/2, self.zoneDessin.GetSize()[1]/2)
        
#        self.ZPlancher = self.centre[1] - self.barre.HAUTEUR_PLAFOND /2
#        self.ZPlafond  = self.centre[1] + self.barre.HAUTEUR_PLAFOND /2
#        
#        #
#        # Echelle pour passer des mètres aux pixels
#        #
#        self.coef = 1.0*(self.ZPlafond - self.ZPlancher) / (self.barre.H_PLAFOND - self.barre.H_PLANCHER)
        
        
        
        #
        # Le thread de calcul de pyStatic
        #
        self.threadDess = DessinThread(self.barre.PERIODE_RAFFRAICH, self.CalculerPositionEtRedessiner)
        self.threadDess.start()
        print "Thread Demarré !"
        
        #
        # Mise en place
        #
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.zoneDessin, flag = wx.EXPAND)
        sizer.Add(self.zoneParam, flag = wx.EXPAND)
        self.SetSizer(sizer)
        
        self.Layout()
        self.InitBuffer()
        
#        self.Bind(wx.EVT_PAINT, self.onPaint)
        
#    #########################################################################################################
#    def onPaint(self, event = None):   
#        print "onPaint"
#        dc = wx.BufferedPaintDC(self, self.buffer, wx.BUFFER_VIRTUAL_AREA)
        
        
         
    #########################################################################################################
    def onTarer(self, event = None):
        self.chrono.initScores()
        
    #########################################################################################################
    def EvtCheckBox(self, event):
        if event.GetId() == 10:
            self.legender = event.IsChecked()
        elif event.GetId() == 11:
            self.afficherChrono = event.IsChecked()
        
    #########################################################################################################
    def OnSliderPosX(self, v):
        self.barre.PosXpc = v/100
        self.barre.PosX = self.barre.demiL*self.barre.PosXpc
        self.chrono.initScores()
        
    #########################################################################################################
    def OnSliderLong(self, v):
        self.barre.LONGUEUR_BARRE = v
        self.barre.demiL = self.barre.LONGUEUR_BARRE / 2
        self.barre.PosX = self.barre.demiL*self.barre.PosXpc
        self.barre.MOMENT_INERT = self.barre.MASSE * self.barre.LONGUEUR_BARRE**2 /4
        self.chrono.initScores()
        
    #########################################################################################################
    def OnSliderPlaf(self, v):
        self.barre.H_PLAFOND = v
        self.chrono.initScores()
        
    #########################################################################################################
    def OnSliderMasse(self, v):
        self.barre.MASSE = v
        self.barre.MOMENT_INERT = self.barre.MASSE * self.barre.LONGUEUR_BARRE**2 /4
        self.barre.poids = self.barre.MASSE * G
        self.chrono.initScores()
        
        
    #########################################################################################################
    def drawNouvOptions(self):
        return
    
    
    #########################################################################################################
    def actualiser(self, tors, torsO = None):
        # On applique les efforts sur la barre
        self.barre.Fz = tors.R.z
        self.barre.My = tors.M.y
#        print self.Fz, self.My
#        print "Effort sur barre:",self.barre.Fz, self.barre.My
        # On calcul les accélérations de la barre
#        self.barre.CalculerEqMouv()
        
        # Initialisation equation du mvt
        self.barre.InitEq = True
        
        self.miseAJourValeurAction()
        
        
        
    #########################################################################################################
    def miseAJourValeurAction(self):
        self.textResult.SetValue(self.barre.Fz)
        self.textMoment.SetValue(self.barre.My)
        self.textPoids.SetValue(self.barre.poids)
        
        
    #########################################################################################################
    def InitBuffer(self):
        w,h = self.zoneDessin.GetSize()
        self.buffer = wx.EmptyBitmap(w, h)
        self.Redessiner()
        
    #########################################################################################################
    def CalculerPositionEtRedessiner(self):
        if self.Pause:
            return
        self.barre.ComputePositionBarre(self.chrono) 
        self.Redessiner()
    
    
    #########################################################################################################
    def Redessiner(self):  
#        print "REDESSINER"
        cdc = wx.ClientDC(self.zoneDessin)
#        self.parent.DoPrepareDC(cdc)
        dc = DCPlus(cdc, self.buffer, wx.BUFFER_VIRTUAL_AREA)
        Pz, Ay, Pxi, Pzi = self.barre.Pz, self.barre.Ay, self.barre.Pxi, self.barre.Pzi
        self.DessinerTout(dc, Pz, Ay, Pxi, Pzi)

        
    #########################################################################################################
    def DessinerTout(self, dc, Pz, Ay, Pxi, Pzi):
        """ Dessine la barre, le plancher et le plafond
            et trace les éléments de réduction du torseur des actions mécaniques en jeu
                Pz : position du point d'accroche de la barre suivant z
                Ay : angle de la barre autour de y
        """
        
        PosX = self.barre.PosX
        
        def ConvForce(pos):
            return int(pos*self.echelle_force)         # Appliquer l"échelle des forces"
        
        def ConvDim(pos):
            return int(pos*self.echelle_dim)   # Appliquer l"échelle des dimensions"
            
        def Coord(x, z):
            return self.centre[0] + ConvDim(x) , self.zoneDessin.GetSize()[1] - (self.zPlan + ConvDim(z))
        
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(self.zoneDessin.GetBackgroundColour()))
        dc.Clear()
        
        
#        zPlaf = Coord(0, HAUTEUR_PLAFOND)[1]
#        zPlaf = Coord(0, HAUTEUR_PLAFOND)[1]
        self.zPlaf = self.centre[1] + self.barre.H_PLAFOND/2*self.echelle_dim
        self.zPlan = self.centre[1] - self.barre.H_PLAFOND/2*self.echelle_dim
        
#        self.coef = 1.0*(zPlaf - zPlan) / (self.barre.H_PLAFOND - self.barre.H_PLANCHER)
        
        #
        # On dessine le plafond et le plancher
        #
        dc.DrawLine(0, self.zPlan - 5,
                    self.zoneDessin.GetSize()[0], self.zPlan - 5)
    
        dc.DrawLine(0, self.zPlaf + 5,
                    self.zoneDessin.GetSize()[0], self.zPlaf + 5)
        
#        self.CalculerPoints(Pz, Ay)
        
        #
        # On dessine la barre
        #
        x1, z1 = Pxi[0], Pzi[0]
        x2, z2 = Pxi[1], Pzi[1]
        
        _x1, _z1 = Coord(x1, z1)
        _x2, _z2 = Coord(x2, z2)
        
        dc.SetPen(wx.Pen(self.barre.COUL_BARRE, 10))
        dc.DrawLine(_x1, _z1, _x2, _z2)
        
        dc.SetTextForeground(wx.BLACK)
        
        #
        # On dessine le point d'accroche
        #
        zP = Pz + PosX*sin(Ay)
        xP = PosX*cos(Ay)
        
        _xP, _zP = Coord(xP, zP)
        
        if self.legender:
            dc.DrawBitmap(self._P, _xP - self._P.GetWidth() - 2, _zP + self._P.GetHeight()/2)
            
        dc.SetPen(wx.Pen(wx.BLACK, 2))
        dc.DrawCircle(_xP, _zP, 2)
        
        
        
        #
        # On dessine les actions mécaniques
        #
        
        # Le Poids ...
        dc.SetPen(wx.Pen(self.barre.COUL_POIDS, 3))
        xG, zG = Coord(0,Pz)
        dc.DrawLineArrow(xG, zG , 
                         xG, zG + ConvForce(self.barre.poids),
                         taille = 2, style = 2)
        if self.legender:
            dc.DrawBitmap(self._G, xG - self._G.GetWidth() - 2, zG + self._G.GetHeight()/2)
            dc.DrawBitmap(self._vP, xG, zG + ConvForce(self.barre.poids))
            
        # La force extérieure
        dc.SetPen(wx.Pen(COUL_RESULTANTE, 3))
        if ConvForce(self.barre.Fz) <> 0:
            dc.DrawLineArrow(_xP, _zP , 
                             _xP, _zP - ConvForce(self.barre.Fz),
                             taille = 2 , style = 2)
        if self.legender:
            dc.DrawBitmap(self._vR, _xP - self._vR.GetWidth(), _zP - ConvForce(self.barre.Fz)-sign(self.barre.Fz)*self._vR.GetHeight())
            
        # Le moment extérieur
        dc.SetPen(wx.Pen(COUL_MOMENT, 3))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        a = 3.0*pi/2.0 * self.barre.My/self.barre.MY_MAX  # Angle de l'arc à tracer (en rad)
        
        rayon = 16
        x1, y1 = int(round(_xP+rayon*cos(self.barre.Ay))), int(round(_zP-rayon*sin(self.barre.Ay)))
        x2, y2 = int(round(_xP+rayon*cos(a+self.barre.Ay))), int(round(_zP-rayon*sin(a+self.barre.Ay)))
        
        st = 1
        if a+self.barre.Ay<0:
            x1, y1, x2, y2 = x2, y2, x1, y1
            st = 2
            
        if x1 != x2 :
            dc.DrawArcArrow(x1, y1, x2, y2,
                               _xP, _zP, taille = 2 , style = st)
        
        if self.legender:
            dc.DrawBitmap(self._vM, x2 - self._vM.GetWidth(), y2 - sign(a)*self._vM.GetHeight())
        
        #
        # Le chronometre 
        #
        if self.afficherChrono:
            s1 = u"Durée de l'\"équilibre\" : "+strSc(round(self.chrono.getVal(),1), nc = 2)+" s"
            w, h = dc.GetTextExtent(s1)
            dc.DrawText(s1, 0, 0)
            dc.SetTextForeground(wx.RED)
            dc.DrawText(u"Meilleur \"score\" : "+strSc(round(self.chrono.getMaxScore(),1), nc = 2)+" s",
                        0, h)
        
        dc.EndDrawing()     
        
    def StopperThread(self):
        wx.BusyInfo(u"Arrêt du thread ...")
        wx.Yield()
        
        self.threadDess.stopper()
        running = True
        while running:
            running = self.threadDess.IsRunning() 
            time.sleep(0.1)
       
        
    def OnClose(self):
        self.StopperThread()
        
    def DemarrerThread(self):
        self.threadDess.run()
    
    #########################################################################################################
    def miseAJourPtRed(self, P):
        return
    
    #########################################################################################################
    def OnPause(self, etat):
        if etat:
            self.Pause = True
            self.chrono.pause()
        else:
            self.Pause = False
            self.chrono.reprise()
        
    
            
            
#############################################################################################################
class StaticTextValeur(wx.Panel):
    def __init__(self, parent, nom, val, unite = '', useMPL = True):
        wx.Panel.__init__(self, parent, -1)
        
        if useMPL:
            titre = wx.StaticBitmap(self, -1, mathtext_to_wxbitmap(nom))
        else:
            titre = wx.StaticText(self, -1, nom)
            
        self.val = wx.StaticText(self, -1, '')
        
        
        unite = wx.StaticText(self, -1, ' '+unite)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add(titre, flag = wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.val, flag = wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(unite, flag = wx.ALIGN_CENTER_VERTICAL)
        
        self.SetSizer(sizer)
        self.SetValue(val)
        
        
    def SetValue(self, v):
        self.val.SetLabel(strSc(v, nc = 2))
        self.Layout()
        self.Fit()
        
        
#############################################################################################################
class TextSlider(wx.Panel):
    def __init__(self, parent, texte, val, maxval, minval, fct, coef = 1.0, unite = '', style = wx.SL_HORIZONTAL):
        wx.Panel.__init__(self, parent, -1)
        self.fct = fct
        self.coef = coef
        self.unite = unite
        
        self.texte = wx.StaticText(self, -1, texte)
        self.slide = wx.Slider(self, -1, val, maxval, minval, style = style)
        self.valeur = wx.StaticText(self, -1, str(val * self.coef)+self.unite)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.texte, 1, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        sizer.Add(self.slide, 1, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        sizer.Add(self.valeur, 1, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        self.SetSizer(sizer)
        
        self.Bind(wx.EVT_SCROLL, self.OnScroll)
        
    def OnScroll(self, event):
        p = 1.0 * event.GetPosition() * self.coef
        self.valeur.SetLabel(str(p)+self.unite)
        self.Layout()
        self.Fit()
        self.fct(p)
    
#############################################################################################################
#############################################################################################################
#
#  Classe gérant la barre dans son environnement
#
#############################################################################################################
#############################################################################################################
class Barre:  
    # Dimensions réelles (en mètres)
    LONGUEUR_BARRE = 1.0
    H_PLANCHER = 0.0
    H_PLAFOND = 1.2
    A_MAXI = pi/4
    
    # Grandeurs physiques (en N et en Nm)
    FZ_MIN = 0
    FZ_MAX = 100
    MY_MIN = -6
    MY_MAX = 6
    
    MASSE = 1.0 # en kg
#    MOMENT_INERT = 10.0
    MOMENT_INERT = MASSE * LONGUEUR_BARRE**2 /4
    
    # Periode du calcul
    PERIODE_RAFFRAICH = 0.05 # en secondes
    PERIODE_CALCUL = 0.04 # periode "virtuelle" (à rapprocher de PERIODE_RAFFRAICH pour plus de réalisme)

    # Coefficient de restitution des chocs
    COEF_RESTIT = 0.25
    
    # Couleur
    COUL_BARRE = wx.Colour(0,100,100)
    COUL_POIDS = wx.Colour(10,10,240)
    
    #########################################################################################################
    def __init__(self, zoneDessin):
        self.poids = self.MASSE * G
        self.zoneDessin = zoneDessin
        
        # Constantes
        self.demiL = self.LONGUEUR_BARRE / 2
        
        # Les elements de réduction du torseur d'action mécanique sur la barre
        self.Fz = 0.0
        self.My = 0.0

        # Position du point d'accroche
        self.PosXpc = 0.0 # en %
        self.PosX = 0.0
        
        # Paramètres de position de la barre
        self.Ay = 0.0 # Angle
        self.Pz = 0.0 # Position G
        
        # Positions des extrémités de la barre
        self.Pzi = [0.0,0.0]
        self.Pxi = [- self.demiL*cos(self.Ay), self.demiL*cos(self.Ay)]
        
        # 2 variable temporelles (positions linéaire et angulaire gérées séparément)
        self.t1 = 0.0
        self.t2 = 0.0
        
        # état initial position/vitesse linéaire/angulaire
        self.Vz0 = self.Vz = 0.0
        self.Pz0 = self.Pz = 0.0
        self.Ay0 = self.Ay = 0.0
        self.VAy0 = self.VAy = 0.0
        
        # Accélérations
        self.AccPz = 0.0
        self.AccAy = 0.0
        
        self.InitEq = False
        
        return
    
    #########################################################################################################
    def CalcPxiPzi(self, Pz, Ay):
        Pzi = [Pz - self.demiL*sin(Ay), Pz + self.demiL*sin(Ay)]
        Pxi = [- self.demiL*cos(Ay), self.demiL*cos(Ay)]
        return Pxi, Pzi
    

    #########################################################################################################
    def CalcPzAy(self, Pxi, Pzi):
        Pz = (Pzi[0] + Pzi[1])/2
        try:
            Ay = atan((Pzi[1] - Pzi[0])/(Pxi[1] - Pxi[0]))
        except:
            Ay = 0.0
        return Pz, Ay
    
        
#    #########################################################################################################
#    def CalculerEqMouv(self):
#        """ Permet de passer au thread de calcul 
#            les paramètres de position de la barre
#                AccPz : Accelération verticale de G
#                AccAy : Accélération en rotation autour de y
#        """
#        
#        # Accelération verticale de G
#        self.AccPz = (self.Fz - self.poids) / self.MASSE
#        
#        # Accélération en rotation autour de y
#        self.AccAy = (self.My + self.Fz*self.PosX) / self.MOMENT_INERT
        
#        print "Accélération barre", self.AccPz, self.AccAy 
        
        # Mise à jour des textes
#        self.accel1.SetLabel(str(self.threadDess.AccPz))
#        self.accel2.SetLabel(str(self.threadDess.AccAy))

    def initEquations(self, flag = 0):
        if flag == 1 or flag == 0:
            self.t1 = 0.0
            self.Vz0 = self.Vz
            self.Pz0 = self.Pz
        if flag == 2 or flag == 0:
            self.t2 = 0.0
            self.Ay0 = self.Ay
            self.VAy0 = self.VAy
        
    def ComputePositionBarre(self, chrono = None):
        
#        print "Calcul Position barre :", self.t1
        
        if self.InitEq:
            self.initEquations()
            self.InitEq = False
#                print "AccelPz = ", self.AccPz
#                print "AccelAy = ", self.AccAy

        self.t1 += self.PERIODE_CALCUL
        self.t2 += self.PERIODE_CALCUL
        
        #
        # Effort au(x) contact(s)
        #
#        Fi = [0.0, 0.0]
#        if self.Pzi[0] == self.H_PLANCHER:
#            Fi[0] =
        #
        # Calcul de la position et de la vitesse linéaire suivant z
        #
#        if self.Pz == self.H_PLANCHER and self.AccPz < 0.0:
#            AccPz = 0.0
#            self.initEquations(1)
#        elif self.Pz == self.H_PLAFOND and self.AccPz > 0.0:
#            AccPz = 0.0
#            self.initEquations(1)
#        else:

        # Accelération verticale de G
        self.AccPz = (self.Fz - self.poids) / self.MASSE
        
        # Equations du mouvement
        self.Pz = self.AccPz * self.t1**2 + self.Vz0 * self.t1 + self.Pz0
        self.Vz = self.AccPz * self.t1 + self.Vz0
#        print "   ", self.AccPz, self.t1, self.Vz0, self.Pz0, self.Pz
        
        #
        # Calcul de la position et de la vitesse angulaire autour de y
        #
        # Accélération en rotation autour de y
        if self.MOMENT_INERT == 0.0:
            self.AccAy = 0.0
        else:
            self.AccAy = (self.My + self.Fz*self.PosX) / self.MOMENT_INERT
#        if self.Ay > self.A_MAXI and self.AccAy > 0.0:
#            AccAy = 0.0
#            self.initEquations(2)
#        if self.Ay < -self.A_MAXI and self.AccAy < 0.0:
#            AccAy = 0.0
#            self.initEquations(2)
#        else:
        AccAy = self.AccAy
        self.Ay = AccAy * self.t2**2 + self.VAy0 * self.t2 + self.Ay0
        self.VAy = AccAy * self.t2 + self.VAy0
        
#        print "Accélération barre", self.AccPz, self.AccAy
#        print "  ==>>", self.Pz , self.Vz
#        print "  avant butées", self.Pz, self.Ay
        #
        # gestion des "butées"
        #
        
        ## butée angulaire
        if self.MOMENT_INERT != 0.0 and abs(self.Ay) > self.A_MAXI:
            if chrono != None and chrono.estDemarre():
                chrono.stopper()
            self.Ay = sign(self.Ay)*self.A_MAXI
            # RAZ position angulaire
            self.t2 = 0.0
            self.VAy0 = 0.0
            self.Ay0 = self.Ay
#            print "  après butée Ay =", self.Ay
#            print Ay
#            print "Pz =", Pz, "Vz =", Vz

        else:
            if chrono != None and not chrono.estDemarre():
                chrono.demarrer()
        
        self.Pxi, self.Pzi = self.CalcPxiPzi(self.Pz ,self.Ay)
#            print "  >>>",Pzi
        
        choc = False
        dVz = dVAy = 0.0
        if self.MOMENT_INERT == 0.0:
            if self.Pz > self.H_PLAFOND or self.Pz < self.H_PLANCHER:
#                print "Choc ",i,"!", self.Pz , self.Vz, "...", self.Ay, self.VAy
                K = 1/self.MASSE
                Vzi = self.Vz
                per = -(1+self.COEF_RESTIT) * Vzi /K
                
                dVz += per/self.MASSE
                
                if self.Pz > self.H_PLAFOND:
                    self.Pzi[0] = self.Pzi[1] = self.H_PLAFOND
                
                if self.Pz < self.H_PLANCHER:
                    self.Pzi[0] = self.Pzi[1] = self.H_PLANCHER
        
                choc = True
                
        else:
            for i in [0,1]:
                if self.Pzi[i] > self.H_PLAFOND or self.Pzi[i] < self.H_PLANCHER:
    #                print "Choc ",i,"!", self.Pz , self.Vz, "...", self.Ay, self.VAy
                    K = 1/self.MASSE + self.Pxi[i]**2 / self.MOMENT_INERT
                    Vzi = self.Vz + self.Pxi[i] * self.VAy
                    per = -(1+self.COEF_RESTIT) * Vzi /K
                    
    #                if self.Pzi[i] < self.H_PLANCHER:
    #                    per += self.poids/2 * self.PERIODE_CALCUL
                        
    #                print "percussion", per
    #                if self.Pzi[i] > self.H_PLAFOND:
    #                    per = -per
                    
                    dVz += per/self.MASSE
                    if self.MOMENT_INERT == 0.0:
                        dVAy += 0.0
                    else:
                        dVAy += self.Pxi[i] * per / self.MOMENT_INERT
                    
                    if self.Pzi[i] > self.H_PLAFOND:
                        self.Pzi[i] = self.H_PLAFOND
                    
                    if self.Pzi[i] < self.H_PLANCHER:
                        self.Pzi[i] = self.H_PLANCHER
            
                    choc = True
                
                
        if choc:
            self.Vz += dVz
            self.VAy += dVAy
            self.Pz ,self.Ay = self.CalcPzAy(self.Pxi, self.Pzi)
#            print "  ==>", self.Pz, self.Vz, "...", self.Ay, self.VAy
            self.InitEq = True
            if chrono != None and chrono.estDemarre():
                chrono.stopper()
        else:
            if chrono != None and not chrono.estDemarre():
                chrono.demarrer()
                
                
#        ## butée linéaire (plancher/plafond
#        stopT = False
#        cor = 0
#        for i in [0,1]:
#            if self.Pzi[i] > self.H_PLAFOND:
#                cor = min(cor, self.H_PLAFOND - self.Pzi[i])
##                    Pzi[i] = H_PLAFOND
##                    Pz += - H_PLAFOND + Pzi[i]
##                    Pzi[1-i]+= - H_PLAFOND + Pzi[i]
#                stopT = True
#            elif self.Pzi[i] < self.H_PLANCHER:
#                cor = max(cor, self.H_PLANCHER - self.Pzi[i])
##                    Pzi[i] = H_PLANCHER
##                    Pz += + H_PLANCHER - Pzi[i]
##                    Pzi[1-i]+= + H_PLANCHER - Pzi[i]
#                stopT = True
#        
#        
#        
#        if stopT:
#            # RAZ position linéaire
#            self.t1 = 0.0
#            self.Pz += cor
#            self.Vz0 = self._Vz
#            self.Pz0 = self._Pz
#            self.Pxi, self.Pzi = self.CalcPxiPzi(self.Pz ,self.Ay)
#            print "  après butée Pz =", self.Pz
##            print "    >>>",Pzi
#     
#        else: 
##                print
#            self._Pz = self.Pz
#            self._Ay = self.Ay
#            self._Vz = self.Vz
#            self._VAy = self.VAy
        
#        self.t1 += self.PERIODE_CALCUL
#        self.t2 += self.PERIODE_CALCUL
        
    
    
#############################################################################################################
#############################################################################################################
class DessinThread(threading.Thread):
    def __init__(self, periode, fonction):
        threading.Thread.__init__(self)
        self.periode = periode
        self.fonction = fonction
        self.PasFini = False
        
    def run(self):
        print u"C'est parti ... "
        self.Terminated = False
        self.PasFini = True
        
        while not self.Terminated:
            time.sleep(self.periode)
            self.fonction()
            
        self.PasFini = False
        return
    
    def IsRunning(self):
        return self.PasFini
        
    def stopper(self):
        print "stop"
        self.Terminated = True    
#        self._Thread__stop()



#########################################################################################################
class DCPlus(wx.BufferedDC):
    def __init__(self, *args, **kwargs ):
        wx.BufferedDC.__init__(self, *args, **kwargs)
    
    def DrawLinesArrow(self, lstpoint, taille = 0, style = 3, tanF = 0.5):
        nbPt = len(lstpoint)
        pen = self.GetPen()
        brush = self.GetBrush()
        ep = pen.GetWidth()
        lf = (taille+ep/2)/tanF
#        print "ep =",ep, "lf =", lf
        
        def SinCos(pt1, pt2):
            h = ((pt2.y-pt1.y)**2+(pt2.x-pt1.x)**2)**0.5
            if h == 0:
                s = 0
                c = 1
            else:
                s = (pt2.y-pt1.y)/h
                c = (pt2.x-pt1.x)/h
            return s,c
        
        def LocToGlob(org, pt, s, c):
            pt2 = wx.Point(0,0)
            pt2.x = org.x+c*pt.x-s*pt.y
            pt2.y = org.y+s*pt.x+c*pt.y
#            print pt2.x, pt2.y
            return pt2
        
        if style&1:
            sinA, cosA = SinCos(lstpoint[0], lstpoint[1])
#            print "sinA =", sinA, "cosA =", cosA
#            print lstpoint[0].x,lstpoint[0].y
#            lstpoint[0] = LocToGlob(lstpoint[0], wx.Point(-ep/2, 0), sinA, cosA)
            fl1 = [lstpoint[0], 
                   LocToGlob(lstpoint[0], wx.Point(lf,  taille+ep/2), sinA, cosA),
                   LocToGlob(lstpoint[0], wx.Point(lf, -taille-ep/2), sinA, cosA),
                   lstpoint[0]]
            self.SetPen(wx.Pen(pen.GetColour(), 1))
            self.SetBrush(wx.Brush(pen.GetColour()))
            self.DrawPolygon(fl1)
            self.SetPen(pen)
            self.SetBrush(brush)
            lstpoint[0] = LocToGlob(lstpoint[0], wx.Point(lf, 0), sinA, cosA)

        if style&2:
            sinB, cosB = SinCos(lstpoint[nbPt-1], lstpoint[nbPt-2])
#            print "sinB =", sinB, "cosB =", cosB
#            print lstpoint[nbPt-1].x,lstpoint[nbPt-1].y
#            lstpoint[nbPt-1] = LocToGlob(lstpoint[nbPt-1], wx.Point(-ep/2, 0), sinB, cosB)
            fl2 = [lstpoint[nbPt-1], 
                   LocToGlob(lstpoint[nbPt-1], wx.Point(lf,  taille+ep/2), sinB, cosB),
                   LocToGlob(lstpoint[nbPt-1], wx.Point(lf,  -taille-ep/2), sinB, cosB),
                   lstpoint[nbPt-1]]
            self.SetPen(wx.Pen(pen.GetColour(), 1))
            self.SetBrush(wx.Brush(pen.GetColour()))
            self.DrawPolygon(fl2)
            self.SetPen(pen)
            self.SetBrush(brush)
            lstpoint[nbPt-1] = LocToGlob(lstpoint[nbPt-1], wx.Point(lf, 0), sinB, cosB)
            
        self.DrawLines(lstpoint)

    def DrawLineArrow(self, x1, y1, x2, y2, taille = 0, style = 3, tanF = 0.5):
        lstPt = [wx.Point(x1,y1), wx.Point(x2,y2)]
        self.DrawLinesArrow(lstPt, taille, style, tanF)
        
    def DrawArcArrow(self, x1, y1, x2, y2, xc, yc, taille = 0, style = 3, tanF = 0.5):
        if style&1:
            xv, yv = 1.0*(x2-xc), 1.0*(y2-yc)
            if yv != 0.0:
                xu, yu = 1.0, -xv/yv
            else:
                xu, yu = -yv/xv, 1.0
            self.DrawArrow((x2, y2), (x2+xu, y2+yu), taille, tanF)
        
        if style&2:
            xv, yv = 1.0*(x1-xc), 1.0*(y1-yc)
            if yv != 0.0:
                xu, yu = 1.0, -xv/yv
            else:
                xu, yu = -yv/xv, 1.0
            self.DrawArrow((x1, y1), (x1+xu, y1+yu), taille, tanF)
            
        self.DrawArc(x1, y1, x2, y2, xc, yc)
        
    def DrawArrow(self, pt1, pt2, taille = 0, tanF = 0.5):
        pen = self.GetPen()
        brush = self.GetBrush()
        ep = pen.GetWidth()
        lf = (taille+ep/2)/tanF
#        print "ep =",ep, "lf =", lf
        
        def SinCos(pt1, pt2):
            h = ((pt2[1]-pt1[1])**2+(pt2[0]-pt1[0])**2)**0.5
            if h == 0:
                s = 0
                c = 1
            else:
                s = (pt2[1]-pt1[1])/h
                c = (pt2[0]-pt1[0])/h
            return s,c
        
        def LocToGlob(org, pt, s, c):
            pt2 = wx.Point(0,0)
            pt2.x = org[0]+c*pt[0]-s*pt[1]
            pt2.y = org[1]+s*pt[0]+c*pt[1]
#            print pt2.x, pt2.y
            return pt2
        
        
        sinA, cosA = SinCos(pt1, pt2)
#            print "sinA =", sinA, "cosA =", cosA
#            print lstpoint[0].x,lstpoint[0].y
#            lstpoint[0] = LocToGlob(lstpoint[0], wx.Point(-ep/2, 0), sinA, cosA)
        fl1 = [wx.Point(pt1[0], pt1[1]), 
               LocToGlob(pt1, wx.Point(lf,  taille+ep/2), sinA, cosA),
               LocToGlob(pt1, wx.Point(lf, -taille-ep/2), sinA, cosA),
               wx.Point(pt1[0], pt1[1])]
        self.SetPen(wx.Pen(pen.GetColour(), 1))
        self.SetBrush(wx.Brush(pen.GetColour()))
        self.DrawPolygon(fl1)
        self.SetPen(pen)
        self.SetBrush(brush)
#        lstpoint[0] = LocToGlob(lstpoint[0], wx.Point(lf, 0), sinA, cosA)


class MyCustomToolbar(NavigationToolbar2Wx): 
    ID_ZOOM_TOUT = wx.NewId()
    def __init__(self, plotCanvas, panel):
        # create the default toolbar
        NavigationToolbar2Wx.__init__(self, plotCanvas)
        
        self.panel = panel
        
        # remove the unwanted button
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 6
        self.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)
        
        bmp = wx.Bitmap(os.path.join("Images", "zoomtout.png"))
#        bmp = wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_TOOLBAR, (20,20))
        self.AddSimpleTool(self.ID_ZOOM_TOUT, bmp,
                           u"Zoom au mieux", u"Zoom au mieux")
        wx.EVT_TOOL(self, self.ID_ZOOM_TOUT, self.zoomTout)
        
    def zoomTout(self, evt):
        self.panel.zoomTout()
    
       
        
        
def mm2m(a):  
    return a*0.001     
        
def m2mm(a):
    return round(a*1000)
 
        
class T3DApp(wx.App):
    def OnInit(self):
        global PORT, DEBUG
        if len(sys.argv)>1: #un paramètre a été passé
            for param in sys.argv:
                parametre = param.upper()
                # on verifie que le fichier passé en paramètre existe
                if parametre in [COM1, COM2, COM3, COM4]:
                    PORT  = parametre
         
                elif parametre == "DEBUG":
                    DEBUG = True
            
        frame = Torseur3D()
        frame.Show()
        return True


if __name__ == '__main__':
    app = T3DApp(False)
##    frame = PlotFigure()
##    
##
##    # Initialise the timer - wxPython requires this to be connected to
##    # the receiving event handler
##    t = Timer(frame, TIMER_ID)
##    t.Start(200)
##
##    frame.Show()
    app.MainLoop()
