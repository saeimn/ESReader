import os
import re
import OCR


logfile = open('/tmp/reader.log', 'w')


class Reader:


    def __init__(self):
        self.code = Code() 


    def process(self, image):
        scan = OCR.recognize(image)
        self.code.add_scan(scan)
        return self.code


    def reset(self):
        self.code = Code()
        

    

class Character:


    def __init__(self, char, index):
        self.char = char
        self.index = index


class Code:


    def __init__(self):
        template = 'xxxxxxxxxxxxx>xxxxxxxxxxxxxxxxxxxxxxxxxxx+ xxxxxxxxx>'
        self.template = template

        self.fixed_indices = []
        for i in range(len(template)):
            if template[i] != 'x':
                self.fixed_indices.append(i)

        self.code = None
        self.char_table = [[] for i in range(len(template))]
        self.scans = []

        self.add_scan(template)
        self.active_positions = []
        
    
    def add_scan(self, scan):
        """
        Add a scan that represents parts of the code.
        """
        self.active_positions = []
        if scan is None:
            return

        logfile.write("\nscan: " + scan)
        ps = self.find_positions(scan)
        logfile.write("\nps: " + str(ps))
        chars = []
        for i in range(len(scan)):
            c = Character(scan[i], ps[i])
            chars.append(c)
            if self.code is None or (c.index >= 0 and 
                                     c.index not in self.fixed_indices and
                                     c.char.isdigit()):
                self.char_table[c.index].append(c)
                self.active_positions.append(c.index)
        self.scans.append(chars)
 
        self.code = self.calc_code()
        logfile.write("\ncode: " + str(self.code))
        logfile.flush()


    def check(self):
        code = self.code

        if not re.match('^\d{13}>\d{27}\+ \d{9}>$', code):
            return (1, None)

        def checksum(n):
            table = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5, 
                     9, 4, 6, 8, 2, 7, 1, 3, 5, 0, 
                     4, 6, 8, 2, 7, 1, 3, 5, 0, 9, 
                     6, 8, 2, 7, 1, 3, 5, 0, 9, 4, 
                     8, 2, 7, 1, 3, 5, 0, 9, 4, 6, 
                     2, 7, 1, 3, 5, 0, 9, 4, 6, 8, 
                     7, 1, 3, 5, 0, 9, 4, 6, 8, 2, 
                     1, 3, 5, 0, 9, 4, 6, 8, 2, 7, 
                     3, 5, 0, 9, 4, 6, 8, 2, 7, 1, 
                     5, 0, 9, 4, 6, 8, 2, 7, 1, 3]
            s = 0
            for i in range(len(n)):
                c = int(n[i])
                s = table[s*10 + c]
            return (10 - s) % 10

        bc = code[0:2]
        if not re.match('01|03|04|11|14|21|23|31|33|[0123]x|x[134]$', bc):
            return (2, "BC number check failed")

        amount = code[0:12]
        amountc = int(code[12])
        if checksum(amount) != amountc:
            return (2, "Amount check failed")
        
        ref = code[14:40]
        refc = int(code[40])
        if checksum(ref) != refc:
            return (2, "Reference number check failed")
        
        account = code[43:51]
        accountc = int(code[51])
        if checksum(account) != accountc:
            return (2, "Account number check failed")
        
        return (0, None)

        
    def get_active_positions(self):
        return self.active_positions

        
    def calc_code(self):
        """
        Calculate the string value of the code.
        
        Chooses the most probable character at each position from the
        internal character table to construct the code.
        """
        code = []
        for i in range(len(self.char_table)):
            row = self.char_table[i]
            counts = {}
            maxc = self.template[i]
            maxn = 2 # require 3 occurences to accept character
            for c in row:
                if not counts.has_key(c.char):
                    counts[c.char] = 0
                if c.char != 'x':
                    counts[c.char] += 1
                if counts[c.char] > maxn:
                    maxn = counts[c.char]
                    maxc = c.char
            code.append(maxc)

        return ''.join(code)


    def find_positions(self, s):
        """
        Find the character positions of a given scan in the code.
        
        Uses dynamic programming to calculate the minimal difference
        between the code and the scan to determine the positions.
        """
        if self.code is None:
            return [i for i in range(len(s))]

        (start, top, left, diag) = range(4)
        table = [[(0, start) for j in range(len(s))] for i in range(len(self.code))]

        # calculate table
        for i in range(len(self.code)):
            for j in range(len(s)):
                props = []

                if i > 0 and j > 0:
                    # substitution/match
                    pdiag = (table[i - 1][j - 1][0], diag)
                    if i in self.fixed_indices and s[j] == self.template[i]:
                        # we have a match with a fixed template char,
                        # add special bonus
                        pdiag = (pdiag[0] + 4, pdiag[1])
                    elif self.code[i] == 'x' or s[j] == 'x' or self.code[i] == s[j]: 
                        # we have a match add bonus
                        pdiag = (pdiag[0] + 1, pdiag[1])
                    if table[i - 1][j - 1][1] == diag:
                        # add bonus to reward successive match/substitute steps
                        pdiag = (pdiag[0] + 1, pdiag[1])
                    props.append(pdiag)

                if i > 0:
                    # skip character in code
                    props.append((table[i - 1][j][0], top))
                    if table[i - 1][j][1] == top:
                        # add bonus to reward successive skip steps
                        pdiag = (pdiag[0] + 1, pdiag[1])
                
                if j > 0:
                    # skip character in scan, subtract weight
                    # (should happen very rarely)
                    props.append((table[i][j - 1][0] - 2, left))
                    
                maxp = (0, start)
                for p in props:
                    if p[0] > maxp[0]:
                        maxp = p

                table[i][j] = maxp
                
        i = len(self.code) - 1
        j = len(s) - 1
        ps = [-1 for k in range(len(s))]

        # construct result
        last_action = -1
        while True:
            c = table[i][j]
            if c[1] == top:
                if last_action != top:
                    ps[j] = i
                i -= 1
            elif c[1] == left:
                ps[j] = i
                j -= 1
            elif c[1] == diag:
                ps[j] = i
                i -= 1
                j -= 1
            else:
                if last_action != top:
                    ps[j] = i
                break
            last_action = c[1]

        return ps


    def __str__(self):
        return self.code


if __name__ == '__main__':
    import sys
    import os
    from PIL import Image

    fl = sys.argv[1:]

    for f in fl:
        if not os.path.exists(f):
            print "File not found: " + f
            sys.exit(1)

    r = Reader()

    for f in fl:
        print 'Processing "' + f + '"... '
        image = Image.open(f)
        code = r.process(image)
        print 'Code: ', code
