#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

## This file in part of Torseur3D
#############################################################################
#############################################################################
##                                                                         ##
##                                   torseur                                 ##
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
torseur.py
Modèle mathématique d'un torseur d'action mécanique
Copyright (C) 2009 Cédrick FAURY

"""
from widgets import strSc, strRound
import wx
from numpy import sqrt

rapportUniteLong = {'m' : 1,
                    'mm': 0.001}

################################################################################
################################################################################
class Point():
    def __init__(self, x = 0, y = 0, z = 0, nom = "O", unite = 'm'):
        self.x = x
        self.y = y
        self.z = z
        self.nom = nom
        self.unite = unite

    def __repr__(self):
        return self.nom+"("+str(self.x)+" "+str(self.y)+" "+str(self.z)+")"
    
    def setComp(self, pt):
        """ Appliquer les composantes du Point <pt> à self
        """
        if type(pt) == list and len(pt) == 3:
            self.x = pt[0]
            self.y = pt[1]
            self.z = pt[2]
        elif isinstance(pt, Point):
            self.x = pt.x
            self.y = pt.y
            self.z = pt.z
            
    def changeUnite(self, unite):
        r = rapportUniteLong[self.unite]/rapportUniteLong[unite]
        self.x = self.x * r
        self.y = self.y * r
        self.z = self.z * r
        self.unite = unite

################################################################################
################################################################################
class Droite():
    def __init__(self, pt, vd, nom = "", unite = 'm'):
        # Point et Vecteur directeur
        self.P = pt
        self.V = vd
        self.nom = nom
        self.unite = unite

    def __repr__(self):
        print "Droite", self.P, self.V
        return ""
    
    def intersectionPlan(self, Q, N):
#        print "intersectionPlan"
#        print self
#        print Q, N

        k = self.V.prod_scal(N)
        if k == 0.0:
            return None
        PQ = Vecteur(P1 = self.P, P2 = Q)
        PI = self.V*(PQ.prod_scal(N)/k)
#        print PI
        I = Point(PI.x+self.P.x, PI.y+self.P.y, PI.z+self.P.z)
        return I
    
    def setComp(self, pt):
        """ Appliquer les composantes du Point <pt> à self
        """
        if type(pt) == list and len(pt) == 3:
            self.x = pt[0]
            self.y = pt[1]
            self.z = pt[2]
        elif isinstance(pt, Point):
            self.x = pt.x
            self.y = pt.y
            self.z = pt.z
            
    def changeUnite(self, unite):
        self.P.changeUnite(unite)
        self.unite = unite

################################################################################
################################################################################
class Vecteur():
    def __init__(self, x = 0, y = 0, z = 0, P1 = None, P2 = None, nom = ""):
        if P1 != None and P2 != None:
            self.x = P2.x - P1.x
            self.y = P2.y - P1.y
            self.z = P2.z - P1.z
        else:
            self.x = x
            self.y = y
            self.z = z
        self.nom = nom
        
    def __repr__(self):
        return self.nom+"("+str(self.x)+" "+str(self.y)+" "+str(self.z)+")"
        
    def __mul__(self, v):
        """ Produit :
            - par un scalaire si v est réel
            - vectoriel si v est Vecteur
        """
        if isinstance(v, Vecteur):
            return Vecteur(self.y * v.z - self.z * v.y,
                           self.z * v.x - self.x * v.z,
                           self.x * v.y - self.y * v.x,
                           )
        else:
            return Vecteur(self.x*v, self.y*v, self.z*v)
        
        return
    
    def __div__(self, k):
        return Vecteur(self.x/k, self.y/k, self.z/k)
        
    def prod_scal(self, v):
        return self.x*v.x + self.y*v.y + self.z*v.z
    
    def __abs__(self):
        return sqrt(self.x**2+self.y**2+self.z**2)
    
    
    def __add__(self, v):
        """ Addition
        """
        if isinstance(v, Vecteur):
            return Vecteur(self.x + v.x, 
                           self.y + v.y, 
                           self.z + v.z)

    def setComp(self, vect):
        """ Appliquer les composantes du Vecteur <vect> à self
        """
        if type(vect) == list and len(vect) == 3:
            self.x = vect[0]
            self.y = vect[1]
            self.z = vect[2]
        elif isinstance(vect, Vecteur):
            self.x = vect.x
            self.y = vect.y
            self.z = vect.z

################################################################################
################################################################################
class Torseur():
    def __init__(self, P = Point(), R = Vecteur(), M = Vecteur(), nom = ""):
        self.P = P
        self.R = R
        self.M = M
        self.nom = nom
        
    def __repr__(self):
        print self.P.x, "\t{", self.R.x, "\t", self.M.x, "\t}"
        print self.P.y, "\t{", self.R.y, "\t", self.M.y, "\t}"
        print self.P.z, "\t{", self.R.z, "\t", self.M.z, "\t}"
        return ''
    
    def changerPtRed(self, P):
        self.M = self.M + Vecteur(P1 = P, P2 = self.P)*self.R
        self.P = P
    
    def getAxeCentral(self):
        k = self.R.prod_scal(self.R)
        if k == 0.0:
            return None
        PI = self.R*self.M/k
        I = Point(self.P.x+PI.x, self.P.y+PI.y, self.P.z+PI.z)
        return Droite(I, self.R)
    
    def setElementsRed(self, tors_R, M = None):
        if isinstance(tors_R, Torseur):
            self.R.setComp(tors_R.R)
            self.M.setComp(tors_R.M)
            self.P.setComp(tors_R.P)
        elif isinstance(tors_R, Vecteur):
            self.R.setComp(tors_R)
            self.M.setComp(M)
            
    def getCopy(self, P = None):
        t = Torseur()
        t.R.setComp(self.R)
        t.M.setComp(self.M)
        t.P.setComp(self.P)
        if P != None:
            t.changerPtRed(P)
        return t
        
    def getMathText(self):
#        p = self.P.nom
#        p = r"\sideset{_"+p+"}"
#        t = r"\{" #"r"\begin{Bmatrix} "
#        t += strSc(self.R.x) +r"  "+strSc(self.M.x)
#        t += r" \n "
#        t+= strSc(self.R.y) +r"  "+strSc(self.M.y)
#        t += r" \n "
#        t+= strSc(self.R.z) +r"  "+strSc(self.M.z)
#        t+= r"\}" #r" \end{Bmatrix}"
        
        return ""

    def getBitmap(self, bg = None, ncR = 1, ncM = 2):
        tt = 88
        yt = 30
        xc = 10+tt
        xc2 = 95+tt
        yc = 0
        xr = 20+tt
        xm = 55+tt
        el = 25
        y = 5
        xp, yp = tt, y+2*el+y
        bmp = wx.EmptyBitmap(106+tt,85)
        maskColor = wx.Colour(255,255,255)
        memDC = wx.MemoryDC(bmp)
        memDC.SetBackgroundMode(wx.TRANSPARENT)
        memDC.SetBackground(wx.WHITE_BRUSH)
#        memDC.SetBackground(wx.Brush(wx.NullColour, style = wx.TRANSPARENT))#wx.Brush(bg
        memDC.Clear()
        torseur = wx.Bitmap("Torseur.png", wx.BITMAP_TYPE_PNG)
        crochet = wx.Bitmap("Crochet.png", wx.BITMAP_TYPE_PNG)
        crochet2 = crochet.ConvertToImage().Mirror().ConvertToBitmap()
        memDC.DrawBitmap(torseur, 0, yt, useMask = True)
        memDC.DrawBitmap(crochet, xc, yc, useMask = True)
        memDC.DrawBitmap(crochet2, xc2, yc, useMask = True)
        memDC.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 
                           ))
        memDC.DrawText(strRound(self.R.x, nc = ncR), xr,y)
        memDC.DrawText(strRound(self.R.y, nc = ncR), xr,y+el)
        memDC.DrawText(strRound(self.R.z, nc = ncR), xr,y+2*el)
        memDC.DrawText(strRound(self.M.x, nc = ncM), xm,y)
        memDC.DrawText(strRound(self.M.y, nc = ncM), xm,y+el)
        memDC.DrawText(strRound(self.M.z, nc = ncM), xm,y+2*el)
        memDC.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, 
                           ))
        memDC.DrawText(self.P.nom, xp,yp)
        memDC.SelectObject(wx.NullBitmap)
        bmp.SetMaskColour(maskColor)
        return bmp