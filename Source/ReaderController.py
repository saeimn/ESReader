"""
Copyright (c) 2009 Simon Hofer

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

from Foundation import *
from AppKit import *
from objc import IBOutlet
from PyObjCTools import NibClassBuilder, AppHelper
from QTKit import QTCaptureView
from PIL import Image
import PySight
from Reader import Reader
from tempfile import mktemp
import re

PIL_TEMP_FILE = mktemp() + '.png'

class ReaderController(NSWindowController):

    # IB Outlets
    cameraView = IBOutlet()
    codeView = IBOutlet()
    resetButton = IBOutlet()
    msgLabel = IBOutlet()

    def awakeFromNib(self):
        self.red_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.3, 0.3, 1.0)
        self.green_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.6, 0.2, 1.0)
        self.blue_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.3, 0.7, 1.0)
        self.white_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0)

        self.reader = Reader()
        self.code = None
        self.scanning = True
        
        transform = NSAffineTransform.transform()
        transform.scaleXBy_yBy_(-1.0, 1.0)
        self.flipFilter = CIFilter.filterWithName_("CIAffineTransform")
        self.flipFilter.setValue_forKey_(transform, "inputTransform")
    
        self.isight = PySight.ISight.alloc().init()
        session = self.isight.start()
        
        self.cameraView.setCaptureSession_(session)
        self.cameraView.setDelegate_(self)

        self.codeView.setString_("Initializing...")
        self.codeView.setTextColor_(self.white_color)

        self.msgLabel.setHidden_(True)
        
        window = self.window()
        window.setAspectRatio_(window.frame().size)

        self.showWindow_(None)
        self.thread = NSThread.alloc().initWithTarget_selector_object_(self,self.updateLoop, None)
        self.thread.start()


    def copyCode(self, code):
        if code is not None:
            pb = NSPasteboard.generalPasteboard()
            types = [NSStringPboardType]
            pb.declareTypes_owner_(types, self)
            pb.setString_forType_(code, NSStringPboardType)


    def nsimage2pil(self, image):
        # save as png and reopen with pil
        rep = image.representations().objectAtIndex_(0)
        data = rep.representationUsingType_properties_(NSPNGFileType, None)
        f = PIL_TEMP_FILE
        data.writeToFile_atomically_(f, False)
        return Image.open(f)


    # IB Action resetClicked:

    def resetClicked_(self, e):
        self.msgLabel.setHidden_(True)
        self.reader.reset()
        self.scanning = True
        

    def displayDoneState(self):
        strcode = str(self.code)
        self.codeView.setString_(strcode)
        self.codeView.setTextColor_(self.green_color)
        self.resetButton.setEnabled_(True)
        self.copyCode(strcode)
        self.msgLabel.setStringValue_("Code copied")
        self.msgLabel.setHidden_(False)


    def displayReadingState(self):
        code = self.code
        strcode = str(code)
        self.codeView.setString_(strcode)
        self.codeView.setTextColor_(self.white_color)
        self.resetButton.setEnabled_(True)
        pos = code.get_active_positions()
        i = 0
        while i < len(strcode):
            l = 1
            if i in pos:
                while i + l < len(strcode) and i + l in pos:
                    l += 1
                self.codeView.setTextColor_range_(self.blue_color, NSMakeRange(i, l))
            elif strcode[i] == 'x':
                while i + l < len(strcode) and strcode[i + l] == 'x':
                    l += 1
                self.codeView.setTextColor_range_(self.red_color, NSMakeRange(i, l))
            i += l


    def displayErrorState(self, message):
        strcode = str(self.code)
        self.codeView.setString_(strcode)
        self.codeView.setTextColor_(self.red_color)
        self.resetButton.setEnabled_(True)
        self.msgLabel.setStringValue_(message)
        self.msgLabel.setHidden_(False)


    def updateLoop(self):
        while True:
            loopPool = NSAutoreleasePool.alloc().init()
            if self.scanning:
                frame = self.isight.consumeFrame()
                reschedule = True
                if frame:
                    frame.retain()
                    self.code = self.reader.process(self.nsimage2pil(frame))
                    (result, message) = self.code.check()
                    strcode = str(self.code)
                    if result == 0:
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(self.displayDoneState, None, True)
                        self.scanning = False
                    elif result == 1:
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(self.displayReadingState, None, True)
                    else:
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(self.displayErrorState, message, True)
                        self.scanning = False
                    frame.release()
            del loopPool
            NSThread.sleepForTimeInterval_(0.3)
        
        
    # QTCaptureView delegate
        
    def view_willDisplayImage_(self, view, image):
        self.flipFilter.setValue_forKey_(image, "inputImage")
        image.release() # why oh why?
        return self.flipFilter.valueForKey_("outputImage")

    
    # NSWindow delegate
    
    def windowWillClose_(self, notification):
        self.isight.stop()

