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
import os, sys, glob, time

#from CedWidgets import *

import wx
import struct

import torseur

################################################################################
################################################################################
#COM1 = 'COM1'
#COM2 = 'COM2'
#COM3 = 'COM3'
#COM4 = 'COM4'
PORT = ''


# Accélération de la pesanteur (m/s²)
G = 10
    
    
################################################################################
################################################################################

# # Les codes à envoyer au banc (LSB First)
# LST_CODE = [199, 197, 203, 201, 195 , 193]
# 
# # Les noms des composantes d'effort (niveau jauges)
# LST_COMP = ['YA','YB','ZB','ZC','XC','XA']
# 
# # Les coefficient pour afficher des N et des Nm
# COEF_R = 0.11
# COEF_M = 0.0114
# 
# PULS = [1.0, 2.0, 1.3, 0.9, 0.7, 2.5]
# 
# # Accélération de la pesanteur (m/s²)
# G = 10
# 
# # Valeur maxi admissible sur la jauge de déformation (BIP si dépassée)
# MAX_JAUGE = 260

################################################################################
################################################################################
        
   
################################################################################
#
#   Interface d'acquisition
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

#         s = serial.Serial(port=port, baudrate = self.BaudRate, bytesize=8,
#                                     parity='N', stopbits=1,
#                                     timeout=0.5, xonxoff=0, rtscts=0)
# #        s.timeout = 0.5   #make sure that the alive event can be checked from time to time
#         print "Port",port,"ouvert correctement"
#         port = port
#         return s, port
        
        
        
        try :
            print "test port", port, self.BaudRate, "...", 
            s = serial.Serial(port=port, baudrate = self.BaudRate, bytesize = 8,
                                        parity='N', stopbits=1,
                                        timeout=5, xonxoff=0, rtscts=0)
    #        s.timeout = 0.5   #make sure that the alive event can be checked from time to time
            print "Ok"
            port = port
            time.sleep(3)
        except: #SerialException
            s = None
            port = None
            print "Erreur"
            
        return s, port
    
    
    ###########################################################################
    def estOk(self):
        return self.serial != None
    
    
    
    
    ###########################################################################
    def fermer(self):
        """Called on application shutdown."""
        print "Fermeture de l'interface"

        #
        # Fermeture du port série
        #
        if self.serial != None:
            self.serial.close()             #cleanup
        
        
    



    




    


################################################################################
#
#   Interface d'acquisition JEULIN
#
################################################################################
class InterfaceAcquisitionJEULIN(InterfaceAcquisition):

    # Les codes à envoyer au banc (LSB First)
    LST_CODE = [199, 197, 203, 201, 195 , 193]
    
    # Les noms des composantes d'effort (niveau jauges)
#     LST_COMP = ['YA','YB','ZB','ZC','XC','XA']
    
    # Les coefficient pour afficher des N et des Nm
    COEF_R = 0.11
    COEF_M = 0.0114
    
    PULS = [1.0, 2.0, 1.3, 0.9, 0.7, 2.5]
    
    # Accélération de la pesanteur (m/s²)
    G = 10
    
    # Valeur maxi admissible sur la jauge de déformation (BIP si dépassée)
    MAX_JAUGE = 260

    def __init__(self):
        self.BaudRate = 9600
        InterfaceAcquisition.__init__(self)
        

  
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
     
        tors.R.x = (self.code[5]+self.code[4]) * self.COEF_R
        tors.R.y = (self.code[0]+self.code[1]) * self.COEF_R
        tors.R.z = (self.code[2]+self.code[3]) * self.COEF_R
     
        tors.M.x = (self.code[0]-self.code[3]) * self.COEF_M
        tors.M.y = (self.code[2]-self.code[5]) * self.COEF_M
        tors.M.z = (self.code[4]-self.code[1]) * self.COEF_M
        
        return
    
    
    ###########################################################################
    def testFirmware(self):
        # On écrit le code de la 1ère jauge sur le port série
        self.serial.write(chr(self.LST_CODE[0]))
            
        # On lit la réponse du banc (2 caractères)         
        text = self.serial.read(2)          
        if text:
            return True
        
        return False
    
    
    ###########################################################################
    def tarer(self):
        for i, c in enumerate(self.codeBrut):
            self.tare[i] = c
            
    ###########################################################################
    def getCodes(self):
        """ Récupération des états des jauges de déformation sous forme de "codes" sur 16bits
            Pour chaque jauge :
              - envoie d'un code (LST_CODE)
              - récupération de 2 mots de 8 bits
              - formation d'un mot de 16bits
        """
        code = []
        for i,n in enumerate(self.LST_CODE):
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
                
                if abs(c) > self.MAX_JAUGE:
                    print "\a" # Envoie un BIP en cas de dépassement
                    code.append(sign(c) * self.MAX_JAUGE)
                else:
                    code.append(c)
            else:
                pass
        return code
    
    
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
            
            
    
################################################################################
#
#   Interface d'acquisition Arduino
#
################################################################################
class InterfaceAcquisitionArduino(InterfaceAcquisition):

    # Les codes à envoyer au banc (LSB First)
    CODE_MSR = ord('M')     # Mesure
    CODE_TAR = ord('T')     # Tarage
    
    # Les coefficient pour afficher des N et des Nm
    COEF_R = 0.11
    COEF_M = 0.0114
    COEF = 0.000005
    
    # Valeur maxi admissible sur la jauge de déformation (BIP si dépassée)
    MAX_JAUGE = 100000000


    def __init__(self):
        self.BaudRate = 9600
        InterfaceAcquisition.__init__(self)
        
    
    ###########################################################################
    def getTorseur(self, tors):
        """ Calcul les composantes du torseur <tors> (en N et en Nm)
            après avoir obtenu les codes de chaque jauge par acquisition sur le port série
        """
#         try:
        self.code = self.getCodes()
#         except:
#             self.messageErreurCom()
#             return
        
        if len(self.code) != 6:
            self.messageErreurCom()
            return
        
        # On applique les coefs
        for i in range(6):
            self.code[i] *= self.COEF
            
        # On applique le transformation
        
        tors.R = sum([self.code[i]*torseur.vec_dir[i] for i in range(6)]) 
#         tors.R.y = sum([self.code[i]*torseur.vec_dir[i].y for i in range(6)]) 
#         tors.R.z = sum([self.code[i]*torseur.vec_dir[i].z for i in range(6)]) 
        
        
        
        tors.M = sum([(self.code[i]*torseur.vec_dir[i])*torseur.pt_app[i]/1000 for i in range(6)])
       
#         tors.M.x = (self.code[0]-self.code[3]) * self.COEF_M
#         tors.M.y = (self.code[2]-self.code[5]) * self.COEF_M
#         tors.M.z = (self.code[4]-self.code[1]) * self.COEF_M
        
        return
    
    
    ###########################################################################
    def tarer(self):
        self.serial.write(chr(self.CODE_TAR))
        for i, c in enumerate(self.codeBrut):
            self.tare[i] = c
    
    
    ###########################################################################
    def testFirmware(self):
        print "testFirmware Arduino ...",
        self.serial.write('A')   # Code pour tester qu'il s'agit bien du banc Arduino
#         print self.serial.inWaiting()
        time.sleep(1)
        # On lit la réponse du banc        
        text = self.serial.read(self.serial.inWaiting())
#         print text, ord(text)
        if text and text == 'A':
            print "Ok"
            return True
        print
        return False
    
    
    ###########################################################################
    def getCodes(self):
        """ Récupération des états des cellules du capteur
              - envoie d'un code de requete : CODE
              - récupération de 6 mots de 16 bits
        """
        code = []
        
        # On envoi le code de requete
        self.serial.write(chr(self.CODE_MSR))
#         time.sleep(1)
        # On lit la réponse du banc (2x6 caractères)         
        text = self.serial.read(24)      
#         print "getCodes", text, len(text)
        if text:
            for i in range(6):
                _n10 = struct.unpack("<l", text[i*4:4+i*4])[0]
                                    
                # On transforme les 2 caractères lus en un mot de 16 bits
#                 n10 = ord(text[1+i*2])*256+ord(text[i*2])+ord(text[1+i*2])*256+ord(text[i*2])
#                 if n10 > 2147483648:
#                     _n10 = n10-4294967295
#                 else:
#                     _n10 = n10
                    
#                 print _n10
                self.codeBrut.append(_n10)
                
                # On applique la tare
                c = _n10 - self.tare[i]
                
                if abs(c) > self.MAX_JAUGE:
#                     print "\a" # Envoie un BIP en cas de dépassement
                    code.append(sign(c) * self.MAX_JAUGE)
                else:
                    code.append(c)
            else:
                pass
        return code
        
    
    ###########################################################################
    def messageErreurCom(self):
        if not hasattr(self, "dlg"):
            self.dlg = wx.MessageDialog(None, u"L'Arduino ne répond pas\n" \
                                                  u"sur le port" + PORT +u"\n\n"\
                                                  u'Causes possibles :\n\n' \
                                                  u" - l'Arduino n'est pas sous tension\n" \
                                                  u"    ==> l'allumer !\n\n" \
                                                  u" - l'Arduino n'est pas connecté au port "+PORT+u"\n" \
                                                  u"    ==> fermer Torseur3D et le relancer en indiquant en argument\n" \
                                                  u"        le port sur lequel est branché l'Arduino :\n" \
                                                  u"          par exemple : torseur3D COM2\n" \
                                                  u" - l'Arduino n'a pas le bon firmware\n" \
                                                  u"    ==> installer le dernier firmware\n" \
                                                  u"        le port sur lequel est branché l'Arduino :\n" ,
                                                  
                               u'Pas de port série',
                               wx.OK | wx.ICON_ERROR 
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
            self.dlg.ShowModal()
            self.dlg.Destroy()



def GetInterfaceAuto():
    """ Détection automatisque du type d'interface
    """
    print "GetInterfaceAuto"
    
    daq = InterfaceAcquisitionArduino()
    if daq.testFirmware():
        return daq
    daq.fermer()
    
    daq = InterfaceAcquisitionJEULIN()
    if daq.testFirmware():
        return daq
    daq.fermer()
    
        


from serial.tools import list_ports


# def serial_ports():
#     """
#     Returns a generator for all available serial ports
#     """
#     if os.name == 'nt':
#         # windows
#         for i in range(256):
#             try:
#                 s = serial.Serial(i)
#                 s.close()
#                 yield 'COM' + str(i + 1)
#             except serial.SerialException:
#                 pass
#     else:
#         # unix
#         for port in list_ports.comports():
#             yield port[0]


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

    
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

def sign(v):
    if v>0:
        return 1
    elif v<0:
        return -1
    else:
        return 0


if __name__ == '__main__':
    print(list(serial_ports()))
    test()


