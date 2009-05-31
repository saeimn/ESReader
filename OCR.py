import os
import sys
import re
from commands import getoutput
from tempfile import mktemp
from math import sqrt
from PIL import Image, ImageFilter, ImageStat


path = os.getcwd()
GOCR_CMD = path + '/gocr'
GOCR_ARGS = ' -s 20 -u x -C "0-9>+ " -p %s -m %d %s'
GOCR_DATABASE = path + '/database/'


def recognize(image):
    """
    Perform OCR on a PIL image of a bill.
    
    image -- The source image.

    Returns the recognized text as string if any, None otherwise.
    """
    image = preprocess(image)
    if image:
        f = mktemp() + '.png'
        image.save(f, 'PNG')
        string = getoutput(GOCR_CMD + (GOCR_ARGS % (GOCR_DATABASE, 2, f)))
        os.remove(f)

        # search for string in the output
        result = None
        for l in string.split('\n'):
            if l.count('x') < 5 and re.search('[x\d>\+ ]{10}', l):
                result = re.sub('([^\+]) +', '\1', l[:-1])
                break
        
        return result
    else:
        return None
    

def preprocess(image):
    # convert image to B/W
    image = image.convert('L')

    image = crop_to_code(image)

    if image:
        # sharpen the image
        kx = ImageFilter.Kernel((5, 5), ( 0, -1, -1, -1,  0, 
                                         -1,  0,  0,  0, -1,
                                         -1,  0, 14,  0, -1,
                                         -1,  0,  0,  0, -1,
                                          0, -1, -1, -1,  0 ))
        return image.filter(kx)
    else:
        return None


def crop_to_code(image):
    """
    Crop an image of a bill to its code region.

    image -- The source image.

    Returns the cropped PIL image if the region is found and None otherwise.
    """
    (x1, y1, x2, y2) = locate_code_box(image)
    (top, bottom) = calculate_text_yinsets(image, (x1, y1, x2, y2))

    tolerance = 3
    y1 = max(y1 + top - tolerance, 0)
    y2 = min(y2 - bottom + tolerance, image.size[1])

    if x1 < x2 and y1 < y2:
        return image.crop((x1, y1, x2, y2))
    else:
        return None


def locate_code_box(image):
    """
    Locate a light box in the image (which hopefully contains the code).

    image -- The source image.

    Returns the coordinates of the box in a tuple (x1, y1, x2, y2).
    """
    w = image.size[0]
    h = image.size[1]
    data = list(image.getdata())

    stat = ImageStat.Stat(image)
    mean = stat.mean[0]
    stddev = stat.stddev[0]
    stddev2 = stddev / 2

    winsize = 10
    winsize2 = winsize*winsize
    x1 = w
    y1 = h
    x2 = 0
    y2 = 0

    for y in range(0, h - winsize, winsize):
        for x in range(0, w - winsize, winsize):
            wmean = 0
            for iy in range(y, y + winsize):
                iywx = iy * w + x
                wmean += sum(data[iywx:iywx + winsize])
            wmean /= winsize2
            if wmean > mean + stddev:
                if x < x1:
                    x1 = x
                if y < y1:
                    y1 = y
                if x + winsize > x2:
                    x2 = x + winsize
                if y + winsize > y2:
                    y2 = y + winsize

    if x1 >= x2:
        x1 = 0
        x2 = w

    if y1 >= y2:
        y1 = 0
        y2 = h

    return (x1, y1, x2, y2)


def calculate_text_yinsets(image, (x1, y1, x2, y2)):
    """
    Calculate the y insets of the text in an image with
    light background and dark text.
    
    image -- The source image.
    (x1, y1, x2, y2) -- The restricted image range.

    Returns the tuple with the insets (top, bottom).
    """
    g = calculate_row_gradients(image, (x1, y1, x2, y2))

    # cutoff the extrema on the border
    cutoff = len(g) - 1
    while g[cutoff] < 0:
        cutoff -= 1
    g = g[:cutoff]
    
    # find min, max, mean and stddev
    gmax = max(g)
    gmin = min(g)
    mean = 0
    mean2 = 0
    for i in g:
        mean += i
        mean2 += i*i
    mean /= len(g)
    mean2 /= len(g)
    stddev = sqrt(mean2 - mean*mean)
    stddev2 = stddev / 2

    # find range for pattern tick down followed by tick up
    top = 0
    bottom = len(g)
    lastmin = -1
    for i in range(len(g)):
        if 2*g[i] > gmax: # tick up
            if top > 0:
                bottom = i
                break
        elif 2*g[i] < gmin: # tick down
            top = i

    # grow range to not cutoff too much content
    while top > 0 and g[top] < mean - stddev2:
        top -= 1
    while bottom < len(g) - 1 and g[bottom] > mean + stddev2:
        bottom += 1

    bottom = len(g) - bottom - 1

    return (top, bottom)
        

def calculate_row_gradients(image, (x1, y1, x2, y2)):
    """
    Calculate the mean gradient for each row in an image.
    
    image -- The source image.
    (x1, y1, x2, y2) -- The restricted image range.

    Returns the gradient values as list (with size y2 - y1 - 1).
    """
    w = image.size[0]
    h = image.size[1]
    data = list(image.getdata())

    mw = x2 - x1
    mh = y2 - y1

    g = []
    ynext = sum(data[y1*w + x1:y1*w + x2])
    for y in range(mh - 1):
        yiw = (y1 + y + 1) * w
        y = ynext
        ynext = sum(data[yiw + x1 : yiw + x2])
        dy = ynext - y
        g.append(dy)

    return g


if __name__ == '__main__':
    i = 1
    mode = -1
    prepf = mktemp() + '.png'
    save = False
    while i < len(sys.argv) and sys.argv[i].startswith('-'):
        if sys.argv[i] == '-l' or sys.argv[i] == '--learn':
            mode = 130
        elif sys.argv[i] == '-r' or sys.argv[i] == '--recognize':
            mode = 2
        elif sys.argv[i] == '-s' or sys.argv[i] == '--save':
            save = True
        else:
            print 'Unrecognized option "' + sys.argv[i] + '"'
            sys.exit(1)
        i += 1

    fl = sys.argv[i:]


    for f in fl:
        if not os.path.exists(f):
            print "File not found: " + f
            sys.exit(1)

    for f in fl:
        print 'Processing "' + f + '"... '
        if save:
            prepf = f[:f.rfind('.')] + '-out.png'
        image = Image.open(f)
        image = preprocess(image)
        if image:
            image.save(prepf, 'PNG')
            if mode >= 0:
                os.system(GOCR_CMD + (GOCR_ARGS % (GOCR_DATABASE, mode, prepf)))
            if not save:
                os.remove(prepf)
        else:
            print 'Preprocessing failed'
