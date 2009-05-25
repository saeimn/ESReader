import objc, AppKit, Foundation, os
if 'site-packages.zip' in __file__:
  base_path = os.path.join(os.path.dirname(os.getcwd()), 'Frameworks')
else:
  base_path = '/Library/Frameworks'
bundle_path = os.path.abspath(os.path.join(base_path, 'CocoaSequenceGrabber.framework'))
objc.loadBundle('CocoaSequenceGrabber', globals(), bundle_path=bundle_path)
del objc, AppKit, Foundation, os, base_path, bundle_path



