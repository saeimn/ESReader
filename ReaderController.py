from Foundation import *
from AppKit import *
from PySight import *
from PyObjCTools import NibClassBuilder, AppHelper
from PIL import Image
from Reader import Reader
from tempfile import mktemp
import re
import cProfile

class CameraView(NSView):
    
    def drawRect_(self, rect):
        if self._image:
            # flip context horizontally
            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(NSMaxX(rect), rect.origin.y)
            transform.scaleXBy_yBy_(-1.0, 1.0)
            transform.concat()

            self._image.drawInRect_fromRect_operation_fraction_(
                rect, NSZeroRect, NSCompositeSourceOver, 1.0)
            
            # revert transformation
            transform.invert()
            transform.concat()

    def setImage_(self, image):
        self._image = image
        
    def image(self):
        return self._image

class ReaderController(NSWindowController):

    def awakeFromNib(self):
        self.red_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.5, 0.5, 1.0)
        self.green_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.6, 1.0, 0.6, 1.0)
        self.blue_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.5, 0.85, 1.0)
        self.white_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0)

        self.frame = None
        self.reader = Reader()

        self.camera = CSGCamera.alloc().init()
        self.camera.setDelegate_(self)
        self.camera.startWithSize_((640, 480))

        self._codeView.setString_("Initializing...")
        self._codeView.setTextColor_(self.white_color)

        self._msgLabel.setHidden_(True)
        
        window = self.window()
        window.setAspectRatio_(window.frame().size)

        self.showWindow_(None)
        self.scheduleTimer(0.0)

    def scheduleTimer(self, time):
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            time, self, 'fireTimer:', None, False)

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
        f = mktemp() + '.png'
        data.writeToFile_atomically_(f, False)
        return Image.open(f)

    # IB Action resetClicked:
    def resetClicked_(self, e):
        self._msgLabel.setHidden_(True)
        self.reader.reset()
        if self.timer:
            self.timer.invalidate()
        self.scheduleTimer(0.0)
        
    # Timer selector fireTimer:
    def fireTimer_(self, e):
        reschedule = True
        if self.frame:
            code = self.reader.process(self.nsimage2pil(self.frame))
            strcode = str(code)
            if strcode is not None:
                self._codeView.setString_(strcode)
                if re.match('^\d{13}>\d{27}\+ \d{9}>$', strcode):
                    # code has valid format, stop reader and copy code
                    self._codeView.setTextColor_(self.green_color)
                    self.copyCode(strcode)
                    self._msgLabel.setStringValue_("Code copied")
                    self._msgLabel.setHidden_(False)
                    reschedule = False
                else:
                    self._resetButton.setEnabled_(True)
                    self._codeView.setTextColor_(self.white_color)
                    pos = code.get_active_positions()
                    i = 0
                    while i < len(strcode):
                        l = 1
                        if i in pos:
                            while i + l < len(strcode) and i + l in pos:
                                l += 1
                            self._codeView.setTextColor_range_(self.blue_color, NSMakeRange(i, l))
                        elif strcode[i] == 'x':
                            while i + l < len(strcode) and strcode[i + l] == 'x':
                                l += 1
                            self._codeView.setTextColor_range_(self.red_color, NSMakeRange(i, l))
                        i += l
            else:
                self._codeView.setTextColor_(self.white_color)
                self._codeView.setString_("Reading...")
                self._resetButton.setEnabled_(False)

        if reschedule:
            self.scheduleTimer(0.5)
        
    # IB Outlets

    def setCameraView_(self, cameraView):
        cameraView.setImage_(None)
        self._cameraView = cameraView
    
    def cameraView(self):
        return self._cameraView

    def setCodeView_(self, codeView):
        self._codeView = codeView

    def codeView(self):
        return self._codeView

    def setResetButton_(self, resetButton):
        self._resetButton = resetButton

    def resetButton(self):
        return self._resetButton

    def setMsgLabel_(self, msgLabel):
        self._msgLabel = msgLabel

    def msgLabel(self):
        return self._msgLabel
    
    # CSGCamera delegate
    
    def camera_didReceiveFrame_(self, aCamera, aFrame):
        self._cameraView.setImage_(aFrame)
        self._cameraView.display()
        self.frame = aFrame
    
    # NSWindow delegate
    
    def windowWillClose_(self, notification):
        self.camera.stop()

AppHelper.runEventLoop()
