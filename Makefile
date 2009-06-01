PYTHON=/opt/local/bin/python2.6
GOCR=gocr-0.47
GOCR_ARCHIVE=deps/$(GOCR).tar.gz
GOCR_PRODUCT=gocr
CSG=CocoaSequenceGrabber
CSG_ARCHIVE=deps/$(CSG).zip
CSG_PRODUCT=$(CSG).framework

all: app

$(CSG_PRODUCT): $(CSG_ARCHIVE)
	rm -rf $(CSG)
	unzip -u $(CSG_ARCHIVE)
	xcodebuild -project $(CSG)/$(CSG)/$(CSG).xcode -configuration Deployment "INSTALL_PATH"="@executable_path"
	mv $(CSG)/$(CSG)/build/Deployment/$(CSG_PRODUCT) .
	rm -rf $(CSG)

$(GOCR_PRODUCT): $(GOCR_ARCHIVE)
	tar xvzf $(GOCR_ARCHIVE)
	test -e gocr-build || mkdir gocr-build
	cd $(GOCR) && ./configure --prefix=$(shell pwd)/gocr-build && make && make install
	mv gocr-build/bin/$(GOCR_PRODUCT) .
	rm -rf gocr-build $(GOCR)

app: gocr $(CSG).framework
	rm -rf build dist
	$(PYTHON) setup.py py2app

clean:
	rm -rf $(CSG_PRODUCT) $(GOCR_PRODUCT) build dist *.pyc
