import os
import sys
import re
from commands import getoutput
from tempfile import mktemp
from math import sqrt
from PIL import Image, ImageFilter, ImageStat

path = os.getcwd()
gocr_cmd = path + '/gocr'
gocr_database = path + '/database/'

def recognize(im):
    # convert to B/W
    im = im.convert('L')

    im = crop_to_code(im)

    # sharpen the image
    kx = ImageFilter.Kernel((5, 5), ( 0, -1, -1, -1,  0, 
                                      -1,  0,  0,  0, -1,
                                      -1,  0, 14,  0, -1,
                                      -1,  0,  0,  0, -1,
                                      0, -1, -1, -1,  0 ))
    im = im.filter(kx)
    f = mktemp() + '.png'
    im.save(f, "PNG")

    # run gocr on the image
    string = getoutput('%s -s 20 -u x -C "0-9>+ " -p %s %s' % (gocr_cmd, gocr_database, f))
    os.remove(f)

    # search for string in the output file
    result = None
    for l in string.split('\n'):
        if l.count('x') < 5 and re.match('([x\d>\+]{7,20}| [x\d]{9}>){1,2}', l):
            result = l[:-1]
            break
        
    return result


def crop_to_code(image):
    (x1, y1, x2, y2) = locate_code_box(image)
    (starty, endy) = calculate_text_yoffsets(image, (x1, y1, x2, y2))

    tolerance = 3
    y1 = max(y1 + starty - tolerance, 0)
    y2 = min(y2 - endy + tolerance, image.size[1])

    if x1 < x2 and y1 < y2:
        return image.crop((x1, y1, x2, y2))
    else:
        return image


def locate_code_box(image):
    w = image.size[0]
    h = image.size[1]
    data = image.getdata()

    stat = ImageStat.Stat(image)
    mean = stat.mean[0]
    stddev = stat.stddev[0]

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
                for ix in range(x, x + winsize):
                    p = data[iy*w + ix]
                    wmean += p
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


def calculate_text_yoffsets(image, (x1, y1, x2, y2)):
    g = calculate_mean_ygradients(image, (x1, y1, x2, y2))

    mean = 0
    mean2 = 0
    for i in g:
        mean += abs(i)
        mean2 += i*i
    mean /= len(g)
    mean2 /= len(g)
    stddev = sqrt(mean2 - mean*mean)
    stddev2 = stddev / 2

    start = 0
    i = len(g) - 1
    peak = -1
    while i >= 0:
        if abs(g[i]) > mean + stddev2:
            if peak < 0:
                peak = i
        elif peak >= 0:
            if peak - i > 4:
                start = i
            peak = -1
        i -= 1

    end = len(g) - 1
    i = 0
    peak = -1
    while i < len(g):
        if abs(g[i]) > mean + stddev2:
            if peak < 0:
                peak = i
        elif peak >= 0:
            if i - peak > 4:
                end = len(g) - i - 1
            peak = -1
        i += 1

    return (start, end)
        

def calculate_mean_ygradients(image, (x1, y1, x2, y2)):
    w = image.size[0]
    h = image.size[1]
    data = image.getdata()

    mw = x2 - x1
    mh = y2 - y1
    g = [0 for i in range(mh - 1)]
    for y in range(mh - 1):
        for x in range(mw):
            g[y] += (data[(y1 + y + 1)*w + x1 + x + 1]
                     - data[(y1 + y)*w + x1 + x])
    return g


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(0)
        
    f = sys.argv[1]
    image = Image.open(f)
    image = image.convert('L')
    image = crop_to_code(image)

    # sharpen the image
    kx = ImageFilter.Kernel((5, 5), ( 0, -1, -1, -1,  0, 
                                      -1,  0,  0,  0, -1,
                                      -1,  0, 14,  0, -1,
                                      -1,  0,  0,  0, -1,
                                      0, -1, -1, -1,  0 ))
    image = image.filter(kx)

    jpg = '/tmp/out.jpg'
    image.save(jpg, 'JPEG')
    os.system('open ' + f)
    os.system('open ' + jpg)
