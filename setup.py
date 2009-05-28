'''
Run with:
% python setup.py py2app
'''

from distutils.core import setup
import py2app

NAME = 'CamReader'
SCRIPT = 'ReaderController.py'
VERSION = '0.1'
ICON = ''
ID = 'com.apple.camreader'
COPYRIGHT = 'Copyright 2009 Simon Hofer'
DATA_FILES = ['English.lproj', 'gocr', 'learn/database']

plist = dict(
    CFBundleIconFile            = ICON,
    CFBundleName                = NAME,
    CFBundleShortVersionString  = ' '.join([NAME, VERSION]),
    CFBundleGetInfoString       = NAME,
    CFBundleExecutable          = NAME,
    CFBundleIdentifier          = ID,
    NSHumanReadableCopyright    = COPYRIGHT
)


app_data = dict(script=SCRIPT, plist=plist)
py2app_opt = dict(frameworks=['CocoaSequenceGrabber.framework'])
options = dict(py2app=py2app_opt,)

setup(
  data_files = DATA_FILES,
  app = [app_data],
  options = options,
)

import os
os.system('chmod +x dist/CamReader.app/Contents/Resources/gocr')
