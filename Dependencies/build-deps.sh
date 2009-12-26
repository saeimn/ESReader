GOCR=gocr-0.47
GOCR_ARCHIVE=$GOCR.tar.gz
GOCR_PRODUCT=gocr

if [ ! -e $GOCR_PRODUCT ]; then
    echo "Building gocr..."
    tar xzf $GOCR_ARCHIVE
    test -e gocr-build || mkdir gocr-build
    pushd $GOCR
    ./configure --prefix=$(pwd)/../gocr-build && make && make install
    popd
    mv gocr-build/bin/$GOCR_PRODUCT .
    rm -rf gocr-build $GOCR
fi
        
PIL=Imaging-1.1.6
PIL_ARCHIVE=$PIL.tar.gz
PIL_PRODUCT=PIL

if [ ! -e $PIL_PRODUCT ]; then
    echo "Building PIL..."
    tar xzf $PIL_ARCHIVE
    pushd $PIL
    patch -p0 < ../PIL.patch
    /usr/bin/python2.5 setup.py build
    mv $(echo build/lib.*) ../PIL
    popd
    rm -rf $PIL
fi
