#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of Torseur3D
#############################################################################
#############################################################################
##                                                                         ##
##                                  setup-T3D                              ##
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
setup-T3D.py
Script pour empacqueter Torseur3D avec py2exe
Copyright (C) 2009 Cédrick FAURY

"""

from distutils.core import setup
import glob, sys, py2exe, os
from glob import glob

sys.path.append('..')

#sys.argv.extend("py2exe --bundle 1".split())

# Remove the build folder, a bit slower but ensures that build contains the latest
import shutil
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("bin", ignore_errors=True)

# my setup.py is based on one generated with gui2exe, so data_files is done a bit differently
# add the mpl mpl-data folder and rc file
import matplotlib as mpl
data_files = mpl.get_py2exe_datafiles()
data_files.extend(glob(r'*.png'))

includes = []
excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter', 'pydoc', 'doctest', 'test', 'sqlite3',
            'javax.comm',"PyQt4", "PyQt4.QtGui","PyQt4._qt",
            "matplotlib.backends.backend_qt4agg", "matplotlib.backends.backend_qt4",
            "matplotlib.numerix"]
packages = ['pytz']
dll_excludes = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl84.dll',
                'tk84.dll', "QtCore4.dll", "QtGui4.dll"]


setup(
    console = ["Torseur3D.py"],
    #name='Torseur_3D',
    #~ version='0.5',
#    zipfile=None,
    data_files=data_files,
    options = {"py2exe":
                    {
                        "includes": includes,
                        "excludes": excludes,
                        "packages": packages,
                        "dll_excludes": dll_excludes,
                        'dist_dir': 'bin',
                        'compressed': 2,
                        "bundle_files": 3,
                        "optimize" : 2
                    }
    },
    
)
