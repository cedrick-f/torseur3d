#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys, os
from cx_Freeze import setup, Executable
import matplotlib

#################################################################################################
# Pour l'import de'mpl_toolkits.mplot3d' :
# ajouter un fichier __init__.py vide dans le dossier 
# C:\\Python27\\Lib\\site-packages\\mpl_toolkits\\

sys.path.append('C:\\Python27\\Lib\\site-packages\\mpl_toolkits\\mplot3d')
sys.path.append('C:\\Python27\\Lib\\site-packages\\mpl_toolkits')
""" C:\\Python27\\Lib\\site-packages\\mpl_toolkits\\mplot3d
"""

import importlib
# print importlib.import_module('mpl_toolkits.mplot3d').Axes3D
# print importlib.import_module('mpl_toolkits.mplot3d').__path__



print sys.path
## Remove the build folder, a bit slower but ensures that build contains the latest
import shutil
shutil.rmtree("build", ignore_errors=True)

#if 'bdist_msi' in sys.argv:
#    sys.argv += ['--install-script', 'install.py']


# Inculsion des fichiers de données
#################################################################################################
includefiles = [( matplotlib.get_data_path(),"mpl-data")]
includefiles.extend([('Images', "Images"),
                     'LICENSE.txt'])
includefiles.append(("C:/Python27/Lib/site-packages/mpl_toolkits","mpl_toolkits"))

if sys.platform == "win32":
    includefiles.extend([('C:\Users\Cedrick\Documents\Developp\Microsoft.VC90.CRT', "Microsoft.VC90.CRT"),])

import scipy
scipy_path = os.path.dirname(scipy.__file__)
#includefiles.append(scipy_path)

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os","collections", "scipy"], 
                     "includes" : ['mpl_toolkits.mplot3d', 
                                  ],
                     "excludes": ["tkinter",
                                  '_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
                                  'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
                                  'Tkconstants', 'pydoc', 'doctest', 'test', 'sqlite3',
                                  "PyQt4", "PyQt4.QtGui","PyQt4._qt",
                                  "matplotlib.backends.backend_qt4agg", 
                                  "matplotlib.backends.backend_qt4", 
                                  "matplotlib.backends.backend_tkagg",
                                  "matplotlib.numerix",
                                  "numpy.core._dotblas",
                                  "collections.sys", "collections._weakref"
                                  ],
                     "optimize" : 0,
                     "include_files": includefiles,
                     'bin_excludes' : ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl85.dll',
                                        'tk85.dll', "UxTheme.dll", "mswsock.dll", "POWRPROF.dll",
                                        "QtCore4.dll", "QtGui4.dll" ]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
#if sys.platform == "win32":
#    base = "Win32GUI"

cible = Executable(
    script = "Torseur3D.py",
    base = base,
    compress = True,
    icon = os.path.join("Images", 'Torseur3D.ico'),
    initScript = None,
    copyDependentFiles = True,
    appendScriptToExe = False,
    appendScriptToLibrary = False
    )


setup(  name = "torseur3D",
        version = "1.3.0",
        author = "Cedrick FAURY",
        description = "affichage 3D d'actions mecaniques",
        options = {"build_exe": build_exe_options},
#        include-msvcr = True,
        executables = [cible])


