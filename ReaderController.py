from Foundation import *
from AppKit import *
from PySight import *
from PyObjCTools import NibClassBuilder, AppHelper
from PIL import Image
from Reader import Reader
from tempfile import mktemp
import re

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
        self.convolution = None
        w = 640
        h = 480
        self.frame2 = NSImage.alloc().initWithSize_(NSMakeSize(w, h))
        self.frameRep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, w, h, 8, 1, False, False, NSCalibratedWhiteColorSpace, 0, 0
            )

        self.frame2.addRepresentation_(self.frameRep)

        self.frame = None
        self.reader = Reader()

        self.camera = CSGCamera.alloc().init()
        self.camera.setDelegate_(self)
        self.camera.startWithSize_((w, h))
        
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
            if code is not None:
                self._numberLabel.setStringValue_(code)
                self._resetButton.setEnabled_(True)

                if re.match('^\d{13}>\d{27}\+ \d{9}>$', code):
                    # code has valid format, stop reader and copy code
                    self._numberLabel.setTextColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.6, 1.0, 0.6, 1.0))
                    self.copyCode(code)
                    self._msgLabel.setStringValue_("Code copied")
                    self._msgLabel.setHidden_(False)
                    reschedule = False
                else:
                    self._numberLabel.setTextColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.6, 0.6, 1.0))

            else:
                self._numberLabel.setTextColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0))
                self._numberLabel.setStringValue_("Reading...")
                self._resetButton.setEnabled_(False)

        if reschedule:
            self.scheduleTimer(2.0)
        
    # IB Outlets

    def setCameraView_(self, cameraView):
        cameraView.setImage_(None)
        self._cameraView = cameraView
    
    def cameraView(self):
        return self._cameraView

    def setNumberLabel_(self, numberLabel):
        self._numberLabel = numberLabel

    def numberLabel(self):
        return self._numberLabel

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
