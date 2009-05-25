import os
import re
from PIL import Image, ImageFilter
from commands import getoutput
from tempfile import mktemp

path = os.getcwd()
cuneiform_cmd = path + '/cuneiform/bin/cuneiform'
os.environ['DYLD_LIBRARY_PATH'] = path + '/cuneiform/lib/'
os.environ['CF_DATADIR'] =  path + '/cuneiform/share/cuneiform/'


class Reader:

    def __init__(self):
        self.code = None 

    def process(self, image):
        return self.merge_code(self.extract_code(image))

    def reset(self):
        self.code = None
        
    def extract_code(self, im):
        # convert to B/W
        im = im.convert('L')

        # sharpen the image
        kx = ImageFilter.Kernel((5, 5), ( 0, -1, -1, -1,  0, 
                                         -1,  0,  0,  0, -1,
                                         -1,  0, 14,  0, -1,
                                         -1,  0,  0,  0, -1,
                                          0, -1, -1, -1,  0 ))
        im = im.filter(kx)
        bmp = mktemp() + '.bmp'
        im.save(bmp, "BMP")

        # run cuneiform on the image
        txt = mktemp() + '.txt'
        getoutput(cuneiform_cmd + ' -o ' + txt + ' ' + bmp)
        os.remove(bmp)

        # search for string in the output file
        result = None
        if os.path.exists(txt):
            f = open(txt, 'r')
            for l in f:
                if re.match('([\d>\+]{7,}| [\d]{9}>){1,2}', l):
                    result = l[:-1]
                    break
            f.close()
            os.remove(txt)
        return result
    
    def merge_code(self, code):
        if self.code is None:
            self.code = code
        elif code is not None:
            index = self.lcsubstr(self.code, code)
            if index[1] > 4: # require some overlap to merge code parts
                l2 = index[1]/2
                index0 = index[0][0] + l2
                index1 = index[0][1] + l2
                if index[0][0] > index[0][1]:
                    # merge with the tail of the old code
                    self.code = self.code[:index0] + code[index1:]
                else:
                    # merge with the head of the old code
                    self.code = code[:index1] + self.code[index0:]
            else:
                self.code = code

        return self.code

    def lcsubstr(self, s, t):
        """
        Get the longest common substring of two strings.
        
        The resulting tuple ((i, j), l) encodes the substring as
        i -- the start index of the substring in s
        j -- the start index of the substring in t
        l -- the length of the substring
        """
        ret = (0, 0)
        l = [(0, 0) for i in range(len(t))]
        lprev = [(0, 0) for i in range(len(t))]
        for i in range(len(s)):
            for j in range(len(t)):
                if s[i] == t[j]:
                    index = lprev[j-1][0]
                    length = lprev[j-1][1]
                    if length == 0:
                        index = (i, j)
                    l[j] = (index, length + 1)
                    if l[j][1] > ret[1]:
                        ret = l[j]
                else:
                    # missing skip/swap for similar substrings
                    l[j] = ((0, 0), 0)
            temp = lprev
            lprev = l
            l = temp
        
        return ret
