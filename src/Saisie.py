#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

## This file in part of Torseur3D
#############################################################################
#############################################################################
##                                                                         ##
##                                  Saisie                                 ##
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
Saisie.py
Interface de saisie des 6 composantes d'un torseur
Copyright (C) 2012 Cédrick FAURY

"""

from widgets import *
from torseur import Torseur
import wx


################################################################################
################################################################################
        
   
################################################################################
#
#   Fenetre principale 
#
################################################################################
class InterfaceSaisie(wx.Panel):

    def __init__(self, parent, ECHELLE_R, ECHELLE_M, titre = "Composantes en O"):
        wx.Panel.__init__(self, parent)
        
        self.tors = Torseur()
        self.ctrl = []
        
        sb = wx.StaticBox(self, -1, titre)
        sbs = wx.StaticBoxSizer(sb)
        
        sizer = wx.GridBagSizer()
        
        for i, c in enumerate(["X", "Y", "Z", "L", "M", "N"]):
            li = i%3
            co = i//3
            v = Variable(c, [0.0], modeLog = False)
            
            if c in ["X", "Y", "Z"]:
                coef = 4/ECHELLE_R
            else:
                coef = 3.5/ECHELLE_M
            vct = VariableCtrl(self, v, coef = coef, labelMPL = True, signeEgal = True, 
                 slider = True, fct = None, help = "", sizeh = 40) 
            
            self.ctrl.append(vct)
            sizer.Add(vct, (li, co), 
                      flag = wx.EXPAND|wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT, border = 4)
            print v.n, v.v[0]
        sbs.Add(sizer)
        self.SetSizerAndFit(sbs)

    ###########################################################################
    def OnVar(self, evt):
        v = evt.GetVar()
        if v.n == "X":
            self.tors.R.x = v.v[0]
        elif v.n == "Y":
            self.tors.R.y = v.v[0]
        elif v.n == "Z":
            self.tors.R.z = v.v[0]
        elif v.n == "L":
            self.tors.M.x = v.v[0]
        elif v.n == "M":
            self.tors.M.y = v.v[0]
        elif v.n == "N":
            self.tors.M.z = v.v[0]
        
    ###########################################################################
    def MiseAJour(self, torsO):
        for i, c in enumerate(["X", "Y", "Z", "L", "M", "N"]):
            if c == "X":
                self.ctrl[i].variable.v[0] = torsO.R.x
            elif c == "Y":
                self.ctrl[i].variable.v[0] = torsO.R.y
            elif c == "Z":
                self.ctrl[i].variable.v[0] = torsO.R.z
            elif c == "L":
                self.ctrl[i].variable.v[0] = torsO.M.x
            elif c == "M":
                self.ctrl[i].variable.v[0] = torsO.M.y
            elif c == "N":
                self.ctrl[i].variable.v[0] = torsO.M.z
            
            self.ctrl[i].mofifierValeursSsEvt()
        
#    ###########################################################################
#    def getTorseur(self, tors):
#        """ (
#        """
#        print "getTorseur"
#        print self.tors
#        tors.setElementsRed(self.tors)
#        print tors
#        return


