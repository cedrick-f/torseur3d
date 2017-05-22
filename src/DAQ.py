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
import os, sys, glob

#from CedWidgets import *

import wx
import struct

import torseur

# Pour faire un buffer
import collections
import time


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



################################################################################
################################################################################

###########################################################################
def testPort(port, BaudRate, dlg, message, count):
    """ Création et ouverture du port série
    
        2 étapes de gauge
    """
    wx.BeginBusyCursor()    
    count += 1
    message += u"Test port" + str(port) + u" (" + str(BaudRate) + u"baud) ..."
    dlg.Update(count, message)
    
    try :
#         print "test port", port, BaudRate, "...", 
        s = serial.Serial(port=port, baudrate = BaudRate, bytesize = 8,
                                    parity='N', stopbits=1,
                                    timeout=5, xonxoff=0, rtscts=0)
#        s.timeout = 0.5   #make sure that the alive event can be checked from time to time
        count += 1
        message += u"Ok\n"
        dlg.Update(count, message)
        
        port = port
        time.sleep(3) # à voir s'il faut garder ça ...
        
    except: #SerialException
        s = None
        port = None
        count += 1
        message += u"ERREUR\n"
        dlg.Update(count, message)
    
    wx.EndBusyCursor()
    
    return s, port
    
   
################################################################################
#
#   Interface d'acquisition
#
################################################################################
class InterfaceAcquisition():

    def __init__(self, dlg, message, count, serial = None, port = None):
        #
        # La connection série
        #
        if serial is None or port is None:
            self.serial, self.port = testPort(PORT, self.BaudRate, dlg, message, count)
        else:
            self.serial, self.port = serial, port
            count += 2
            message += u"Port ouvert " + port + u" (" + str(self.BaudRate) + u"baud)\n"
            dlg.Update(count, message)
        
        #
        # Les paramètres liés au torseur
        #
        self.tare = [0] * 6
        self.code = [0] * 6
#         self.codeBrut = [0] * 6
        self.codeBrut = [collections.deque(maxlen=3) for i in range(6)]
        self.temps = [collections.deque(maxlen=3) for i in range(6)]


    
    
    
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


    ###########################################################################
    def __init__(self, dlg, message, count):
        self.BaudRate = 9600
        InterfaceAcquisition.__init__(self, dlg, message, count)
        

  
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
        
        # On vide le buffer
        self.serial.flush()
        
        # On écrit le code de la 1ère jauge sur le port série
        self.serial.write(chr(self.LST_CODE[0]))
            
        # On lit la réponse du banc (2 caractères)         
        text = self.serial.read(2)          
        if text:
            # On vérifie que le buffer est vide
            if not self.serial.inWaiting():
                print "Ok"
                return True
        print
        return False
    
    
    ###########################################################################
    def tarer(self):
        for i, c in enumerate(self.codeBrut):
            self.tare[i] = c[-1]
            
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
                self.codeBrut[i].append(_n10)
                
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

    # Les codes à envoyer au banc
    CODE_MSR = ord('M')     # Mesure
    CODE_TAR = ord('T')     # Tarage
    
    # Les coefficients pour convertir les valeurs brutes en Newton
    COEF = [9.21e-7*9.81, 
            8.71e-7*9.81, 
            9.25e-7*9.81, 
            9.18e-7*9.81, 
            9.14e-7*9.81, 
            8.97e-7*9.81]
    
    # Valeur maxi admissible sur la jauge de déformation (BIP si dépassée)
    MAX_JAUGE = 10 # Newton


    ###########################################################################
    def __init__(self, dlg, message, count):
        self.BaudRate = 115200
        InterfaceAcquisition.__init__(self, dlg, message, count)
        
    
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
        
        # On applique la transformation
        tors.R = sum([self.code[i]*torseur.vec_dir[i] for i in range(6)])        
        tors.M = sum([(-self.code[i]*torseur.vec_dir[i])*torseur.pt_app[i]/1000 for i in range(6)])
        
        return
    
    
    ###########################################################################
    def tarer(self):
        """ Tarage du banc
            Pris en charge au niveau du firmware
        """
        self.serial.write(chr(self.CODE_TAR))
    
    
    ###########################################################################
    def testFirmware(self):
        print "testFirmware Arduino",
        wx.BeginBusyCursor()
        self.serial.flush()
        time.sleep(1)
        self.serial.write('A')   # Code pour tester qu'il s'agit bien du banc Arduino
#         print self.serial.inWaiting()
        time.sleep(2)
        # On lit la réponse du banc        
        text = self.serial.read(1)#self.serial.inWaiting())
        print "...", text
        if text and text == 'A':
            print "Ok"
            wx.EndBusyCursor()
            self.serial.flush()
            return True
        else:
            self.serial.write('A')   # Code pour tester qu'il s'agit bien du banc Arduino
    #         print self.serial.inWaiting()
            time.sleep(2)
            # On lit la réponse du banc        
            text = self.serial.read(1)#self.serial.inWaiting())
            print "...", text
            if text and text == 'A':
                print "Ok"
                wx.EndBusyCursor()
                self.serial.flush()
                return True
        print
        wx.EndBusyCursor()
        return False
    
    
    ###########################################################################
    def getCodes(self):
        """ Récupération des états des cellules du capteur
              - envoie d'un code de requete : CODE
              - récupération de 6 mots de 24 bits
        """
        code = []
        
        # On envoi le code de requete
        try:
            self.serial.write(chr(self.CODE_MSR))
        except serial.serialutil.SerialException:
            return code
#         time.sleep(1)
        # On lit la réponse du banc (2x6 caractères)         
        text = self.serial.read(24)      
#         print "getCodes", text, len(text)
        if text:
            for i in range(6):
                # Valeur "brute"
                vb = struct.unpack("<l", text[i*4:4+i*4])[0]
                
                # On ajoute la valeur au buffer
                self.codeBrut[i].append(vb)
                self.temps[i].append(time.clock())
                
                # On filtre le résultat pour éviter les erreurs de capteur
                vb = filtrer(self.temps[i], self.codeBrut[i])
                
                # On applique la tare
                c = vb - self.tare[i]
                
                # On corrige le signe (sens alternés sur le montage)
                c *= sign(i%2-0.5)
                
                # On applique le coefficient pour convertir en N
                c *= self.COEF[i]
                
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



def GetInterfaceAuto(win):
    """ Détection automatisque du type d'interface
    """
    print "GetInterfaceAuto"
    message = u"Identification de l'interface d'acquisition\n\n"
    dlg = myProgressDialog(u"Identification de l'interface d'acquisition",
                                   message,
                                   8,
                                   parent=win
                                    )
    
    count = 1
    
    
    count += 1
    message += u"Arduino ..."
    dlg.Update(count, message)
        
    daq = InterfaceAcquisitionArduino(dlg, message, count)
    if daq.estOk() and daq.testFirmware():
        count += 1
        message += u"trouvé !\n"
        dlg.Update(count, message)
        wx.Yield()
        dlg.Destroy()
        return daq
    daq.fermer()
    
    count += 1
    message += u"\nJEULIN ..."
    dlg.Update(count, message)
    daq = InterfaceAcquisitionJEULIN(dlg, message, count)
    if daq.estOk() and daq.testFirmware():
        count += 1
        message += u"trouvé !\n"
        dlg.Update(count, message)
        wx.Yield()
        dlg.Destroy()
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


class myProgressDialog(wx.Frame):
    def __init__(self, titre, message, maximum, parent, style = 0, 
                 btnAnnul = True, msgAnnul = u"Annuler l'opération"):

        wx.Frame.__init__(self, parent, -1, titre, size = (400, 200),
                          style = wx.FRAME_FLOAT_ON_PARENT| wx.CAPTION | wx.FRAME_TOOL_WINDOW | wx.STAY_ON_TOP)
#         pre = wx.PreDialog()
#         pre.Create(parent, -1, titre)
#         self.PostCreate(pre)
#         print "myProgressDialog", maximum

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour(wx.WHITE)
        
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        
        self.count = 0
        self.maximum = maximum
        self.stop = False # Pour opération "Annuler"
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.titre = wx.StaticText(panel, -1)
#         self.titre.SetLabelMarkup(u"<big><span fgcolor='blue'>%s</span></big>" %t)
        self.titre.SetFont(wx.Font(11, wx.SWISS, wx.FONTSTYLE_NORMAL, wx.NORMAL))
        self.titre.SetForegroundColour((50,50,200))
        sizer.Add(self.titre, 0, wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, 20)

        self.message = wx.TextCtrl(panel, -1, size = (-1, 200), 
                                   style = wx.TE_MULTILINE|wx.TE_READONLY|wx.VSCROLL|wx.TE_NOHIDESEL)
        sizer.Add(self.message, 1, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.EXPAND, 15)
         
        self.SetMessage(message)
        
        
        self.gauge = wx.Gauge(panel, -1, maximum)
        sizer.Add(self.gauge, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5)
#         print dir(self.gauge)
        if maximum < 0:
            self.gauge.Pulse()
            
        line = wx.StaticLine(panel, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5)

        self.btn = wx.Button(panel, -1, u"Annuler")
        self.btn.SetHelpText(msgAnnul)
        self.btn.Enable(btnAnnul)
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        
        sizer.Add(self.btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        mainsizer.Add(panel, 1, flag = wx.EXPAND)
        
        panel.SetSizer(sizer)
        panel.Layout()
        self.panel = panel
        self.SetSizer(mainsizer)
#         sizer.Fit(self)
        
        self.sizer = sizer

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
        self.CenterOnParent()
        self.SetMinSize((400, -1))
        self.GetParent().Enable(False)
        wx.Frame.Show(self)
        
        
#         self.Show()#WindowModal()
#         print "fini"

#     def Show(self):
#         self.CenterOnParent()
#         self.GetParent().Enable(False)
#         wx.Frame.Show(self)
#         self.Raise()
        
        



    def OnDestroy(self, event):
        self.GetParent().Enable(True)
        event.Skip()
    
    def Update(self, count, message):
#         print "Update", count
        self.SetMessage(message)
        self.count = count
        
        if self.maximum >= 0 and (self.count >= self.maximum or self.count < 0):
            self.GetParent().Enable(True)
            self.btn.SetLabel(u"Ok")
        self.panel.Layout()
        self.Fit()

        wx.Frame.Update(self)
        
        if self.maximum >= 0:
            wx.CallAfter(self.gauge.SetValue, self.count)
    #         self.gauge.SetValue(self.count)
            self.gauge.Update()
            self.gauge.Refresh()
            
            wx.Yield()
            try:
                self.gauge.UpdateWindowUI()
            except:
                pass
            
        self.gauge.Refresh()
#         time.sleep(.1)
#         self.Refresh()
        
        

    def SetMessage(self, message):
        m = message.split(u"\n\n")
        if len(m) > 1:
            t, m = m[0], u"\n\n".join(m[1:])
        else:
            t, m = m[0], u""
            
        self.titre.SetLabel(t)
        self.message.ChangeValue(m)
#         self.message.ScrollLines(-1)
#         self.message.ScrollPages(1) 
        self.message.ShowPosition(self.message.GetLastPosition ())
        
    
    def OnClick(self, event):
        self.GetParent().Enable(True)
        if event.GetEventObject().GetLabel()[0] == u"A":
            self.stop = True
        else:
            self.Destroy()







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



def filtrer(temps, v):
    u""" Vérifie la validité des données
        >>> si l'accélération est trop forte (erreur capteur)
            on renvoie la donnée précédente
    """
    if len(temps) < 3:
        return v[-1]
    
    dt1 = temps[1] - temps[0]
    dt2 = temps[2] - temps[1]
    dt3 = temps[2] - temps[0]

    acc = abs(((v[0]-v[1])*dt2-(v[1]-v[2])*dt1)/(dt1*dt2*dt3))
#     print temps, v, acc
    # Si l'accélération est trop forte, on remplace la dernière valeur par la précédente
    if acc > 10000000:
        print acc
        v[2] = v[1]

    return v[2]



if __name__ == '__main__':
    print(list(serial_ports()))
    test()


