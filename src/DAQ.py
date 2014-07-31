#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

## This file in part of Torseur3D
#############################################################################
#############################################################################
##                                                                         ##
##                                   D A Q                                 ##
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
DAQ.py
Aquisition des données provenant du banc de mesure Torseur3D (JEULIN) à travers le port série
Copyright (C) 2009 Cédrick FAURY

"""
import serial
import os

#from CedWidgets import *

import wx

################################################################################
################################################################################
#COM1 = 'COM1'
#COM2 = 'COM2'
#COM3 = 'COM3'
#COM4 = 'COM4'
PORT = ''


################################################################################
################################################################################

# Les codes à envoyer au banc (LSB First)
LST_CODE = [199, 197, 203, 201, 195 , 193]

# Les noms des composantes d'effort (niveau jauges)
LST_COMP = ['YA','YB','ZB','ZC','XC','XA']

# Les coefficient pour afficher des N et des Nm
COEF_R = 0.11
COEF_M = 0.0114

PULS = [1.0, 2.0, 1.3, 0.9, 0.7, 2.5]

# Accélération de la pesanteur (m/s²)
G = 10

# Valeur maxi admissible sur la jauge de déformation (BIP si dépassée)
MAX_JAUGE = 260

################################################################################
################################################################################
        
   
################################################################################
#
#   Fenetre principale 
#
################################################################################
class InterfaceAcquisition():

    def __init__(self):
        #
        # La connection série
        #
        
        
        self.serial, self.port = self.testPort(PORT)
        
        #
        # Les paramètres liés au torseur
        #
        self.tare = [0] * 6
        self.code = [0] * 6
        self.codeBrut = [0] * 6



    ###########################################################################
    def testPort(self, port):
        
        print "test port", port
        s = serial.Serial(port=port, baudrate=9600, bytesize=8,
                                    parity='N', stopbits=1,
                                    timeout=0.5, xonxoff=0, rtscts=0)
#        s.timeout = 0.5   #make sure that the alive event can be checked from time to time
        print "Port",port,"ouvert correctement"
        port = port
        return s, port
        
        
        
        try :
            print "test port", port
            s = serial.Serial(port=port, baudrate=9600, bytesize=8,
                                        parity='N', stopbits=1,
                                        timeout=0.5, xonxoff=0, rtscts=0)
    #        s.timeout = 0.5   #make sure that the alive event can be checked from time to time
            print "Port",port,"ouvert correctement"
            port = port
        except: #SerialException
            s = None
            port = None
    
        return s, port
    
    
    ###########################################################################
    def estOk(self):
        return self.serial != None
    
    
    ###########################################################################
    def tarer(self):
        for i, c in enumerate(self.codeBrut):
            self.tare[i] = c
    
    ###########################################################################
    def fermer(self):
        """Called on application shutdown."""
        print "Fermeture de l'interface"

        #
        # Fermeture du port série
        #
        if self.serial != None:
            self.serial.close()             #cleanup
        
        
    ###########################################################################
    def getTorseur(self, tors):
        """ Calcul les composantes du torseur <tors> (en N et en Nm)
            après avoir obtenu les codes de chaque jauge par acquisition sur le port série
        """
        try:
            self.code = self.getCodes()
        except:
            self.messageErreurCom()
            return
        
        if len(self.code) != 6:
            self.messageErreurCom()
            return
            
        
        # On applique les coefs
     
        tors.R.x = (self.code[5]+self.code[4]) * COEF_R
        tors.R.y = (self.code[0]+self.code[1]) * COEF_R
        tors.R.z = (self.code[2]+self.code[3]) * COEF_R
     
        tors.M.x = (self.code[0]-self.code[3]) * COEF_M
        tors.M.y = (self.code[2]-self.code[5]) * COEF_M
        tors.M.z = (self.code[4]-self.code[1]) * COEF_M
        
        return



    ###########################################################################
    def messageErreurCom(self):
        if not hasattr(self, "dlg"):
            self.dlg = wx.MessageDialog(None, u"Le banc torseur3D ne répond pas\n" \
                                                  u"sur le port" + PORT +u"\n\n"\
                                                  u'Causes possibles :\n\n' \
                                                  u" - le banc n'est pas allumé\n" \
                                                  u"    ==> allumer le banc !\n\n" \
                                                  u" - le banc  n'est pas connecté au port "+PORT+u"\n" \
                                                  u"    ==> fermer Torseur3D et le relancer en indiquant en argument\n" \
                                                  u"        le port sur lequel est branché le banc :\n" \
                                                  u"          par exemple : torseur3D COM2",
                               u'Pas de port série',
                               wx.OK | wx.ICON_ERROR 
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
            self.dlg.ShowModal()
            self.dlg.Destroy()




    ###########################################################################
    def getCodes(self):
        """ Récupération des états des jauges de déformation sous forme de "codes" sur 16bits
            Pour chaque jauge :
              - envoie d'un code (LST_CODE)
              - récupération de 2 mots de 8 bits
              - formation d'un mot de 16bits
        """
        code = []
        for i,n in enumerate(LST_CODE):
            # On écrit le code de la jauge sur le port série
            self.serial.write(chr(n))
            # On lit la réponse du banc (2 caractères)         
            text = self.serial.read(2)          
            if text:                            
                # On transforme les 2 caractères lus en un mot de 16 bits
                n10 = ord(text[1])*256+ord(text[0])
                if n10 > 32767:
                    _n10 = n10-65535
                else:
                    _n10 = n10
                self.codeBrut[i] = _n10
                
                # On applique la tare
                c = _n10 - self.tare[i]
                
                if abs(c) > MAX_JAUGE:
                    print "\a" # Envoie un BIP en cas de dépassement
                    code.append(sign(c) * MAX_JAUGE)
                else:
                    code.append(c)
            else:
                pass
        return code


from serial.tools import list_ports


def serial_ports():
    """
    Returns a generator for all available serial ports
    """
    if os.name == 'nt':
        # windows
        for i in range(256):
            try:
                s = serial.Serial(i)
                s.close()
                yield 'COM' + str(i + 1)
            except serial.SerialException:
                pass
    else:
        # unix
        for port in list_ports.comports():
            yield port[0]


    
    
def test():
    InterfaceDAQ = InterfaceAcquisition()
    InterfaceDAQ.serial.timeout = 1
    print 'Q = quitter'
    continuer = True
    while continuer:
        a = raw_input('>>')
        if a == 'Q' or a == 'q':
            continuer = False
    
        InterfaceDAQ.getCodes()
    InterfaceDAQ.serial.close()
    
if __name__ == '__main__':
    print(list(serial_ports()))
    test()


