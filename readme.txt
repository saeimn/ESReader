Install python dependencies

    sudo port install py26-pil py26-pyobjc2 py26-pyobjc2-cocoa py26-py2app-devel
    echo "__import__('pkg_resources').declare_namespace(__name__)" > /opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages/PyObjCTools/__init__.py 

Install cuneiform
        
    # install cmake to build cuneiform
    sudo port install cmake

    # to build cuneiform execute the following commands in the CamReader folder
    mkdir cuneiform
    wget http://launchpad.net/cuneiform-linux/0.6/0.6/+download/cuneiform-0.6.tar.bz2
    tar xvjf cuneiform-0.6.tar.bz2
    cd cuneiform-0.6.0
    mkdir builddir
    cd builddir
    Cmake -DCMAKE_BUILD_TYPE=debug -DCMAKE_INSTALL_PREFIX=$(pwd)/../../cuneiform/ ..
    make
    make install
    
Build CamReader

    # to clean the build
    rm -r build dist

    # to create dist/CamReader.app
    python2.6 setup.py py2app
