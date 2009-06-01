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
    
    image -- The source PIL image.

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
    """
    Crop the image to the region containing the code and improve the
    sharpness of the code.

    image -- The source PIL image

    Returns the preprocessed image or None on error.
    """
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
    Crop an image of a bill to the region that contains the code.

    image -- The source PIL image.

    Returns the cropped PIL image if the region is found and None otherwise.
    """
    bounds = (0, 0, image.size[0], image.size[1])
    ydiffs = calculate_row_diffs(image, bounds)
    (x1, y1, x2, y2) = locate_code_global(ydiffs, bounds)
    (x1, y1, x2, y2) = locate_code_local(ydiffs, (x1, y1, x2, y2))

    tolerance = 3
    y1 = max(y1 - tolerance, 0)
    y2 = min(y2 + tolerance, image.size[1])

    if y1 < y2:
        return image.crop((x1, y1, x2, y2))
    else:
        return None


def locate_code_global(ydiffs, (x1, y1, x2, y2)):
    """
    Locate the global region that contains the code.

    Based on the row differences of the image, this function narrows
    the bounds of the image to the region containing the code.

    ydiffs - The list of the row differences of the image.
    (x1, y1, x2, y2) - The coordinates of the image bounds.

    Returns the coordinates of the bounds as tuple (x1, y1, x2, y2).
    """
    w = x2 - x1
    h = y2 - y1

    y1 += h
    y2 -= h

    dmin = min(ydiffs)
    dmax = max(ydiffs)    
    for y in range(h-1):
        if ydiffs[y] == dmax or ydiffs[y] == dmin:
            if y < y1:
                y1 = y - 50
            if y > y2:
                y2 = y + 50
            break

    return (x1, y1, x2, y2)


def locate_code_local(ydiffs, (x1, y1, x2, y2)):
    """
    Refine the bounds for the region that contains the code.

    Based on the row differences of the image, this function narrows
    the bounds of the image to the region containing the code.

    ydiffs - The list of the row differences of the image.
    (x1, y1, x2, y2) - The coordinates of the image bounds.

    Returns the coordinates of the bounds as tuple (x1, y1, x2, y2).
    """
    d = ydiffs[y1:y2]
    if not d:
        return (x1, y1, x2, y2)

    d2 = map(lambda x : x * x, d)
    dmin = min(d)
    dmax = max(d)
    mean = sum(d) / len(d)
    mean2 = sum(d2) / len(d2)
    stddev = sqrt(mean2 - mean*mean)
    stddev2 = stddev / 2

    # find range for pattern tick down followed by tick up
    top = 0
    bottom = len(d)
    lastmin = -1
    for i in range(len(d)):
        if 2*d[i] > dmax: # tick up
            if top > 0:
                bottom = i
                break
        elif 2*d[i] < dmin: # tick down
            top = i

    # grow range to not cutoff too much content
    while top > 0 and d[top] < mean - stddev2:
        top -= 1
    while bottom < len(d) - 1 and d[bottom] > mean + stddev2:
        bottom += 1

    return (x1, y1 + top, x2, y1 + bottom)
        

def calculate_row_diffs(image, (x1, y1, x2, y2)):
    """
    Calculate the differences of the average row values of an image.

    image -- The source PIL image.
    (x1, y1, x2, y2) -- The coordinates of the image bounds.

    Returns the differences values as list (with size y2 - y1 - 1).
    """
    w = image.size[0]
    h = image.size[1]
    data = list(image.getdata())

    mw = x2 - x1
    mh = y2 - y1

    d = []
    ynext = sum(data[y1*w + x1:y1*w + x2])
    for y in range(mh - 1):
        yiw = (y1 + y + 1) * w
        y = ynext
        ynext = sum(data[yiw + x1 : yiw + x2])
        dy = ynext - y
        d.append(dy)

    return d


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
