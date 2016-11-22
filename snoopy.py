#!/usr/bin/python

# snoopy version 1.0
# Author: Bobby Wade
# Date:   January 5 2012


import sys
import re
import csv
import os.path

# Filters file for valid events. 
class Filter:
    def __init__(self, f):
        self.f = f
        self.commentstring = "#" 
    def next(self):
        line = self.f.next()
        while line.startswith(self.commentstring) or not line.strip():
            line = self.f.next()
        return line
    def __iter__(self):
        return self

# Main class. 
class Snoopy:
    def __init__(self,args):
        # Command line arguments
        self.args = args
        self.specblade      = '0'

        # Counts
        self.totreads       = 0
        self.totreadaddrnak = 0
        self.totreaddatanak = 0
        self.totreadbothnak = 0
        self.totreadsucc    = 0
        self.totwrits       = 0
        self.totwritaddrnak = 0
        self.totwritdatanak = 0
        self.totwritbothnak = 0
        self.totwritsucc    = 0
        self.totcorrupt     = 0
        self.addrstring     = 'NULL'

        # ANSI Color settings
        self.resetcolor     = '\033[0m'
        self.c_black        = '\033[0;30;40m'
        self.c_red          = '\033[0;31;40m'
        self.c_redblink     = '\033[5;31;40m'
        self.c_green        = '\033[0;32;40m'
        self.c_yellow       = '\033[0;33;40m'
        self.c_blue         = '\033[0;34;40m'
        self.c_magenta      = '\033[0;35;40m'
        self.c_cyan         = '\033[0;36;40m'
        self.c_white        = '\033[0;37;40m'
        self.c_bluedim      = '\033[2;34;40m'

        self.blade          = 'NULL'

        # For graphing.....
        self.arrowr         = self.c_green   + '-------------------------------->' + self.resetcolor + '|'
        self.arrowl         = self.c_magenta + '<--------------------------------' + self.resetcolor + '|'
        self.columns        = '{0:>78}'.format('     Index                 Time            NODE1                               NODE2\n')
        self.underline      = '{0:>78}'.format('     --------------------------------------+---------------------------------+----')
        self.blankline      = '{0:>78}'.format('|                                 |')
        self.cmdnone        = '{0:>78}'.format('|           CMD NONE              |')
        self.cmdfailed      = '{0:>78}'.format('|           CMD FAILED            |')
        self.getslpto       = '{0:>78}'.format('|           GET SLP TO            |')
        self.ack            = '{0:>78}'.format('|           ACK                   |')
        self.cmmready       = '{0:>78}'.format('|           NODE1 READY             |')
        self.getmac         = '{0:>78}'.format('|           GET MAC ADDR          |')
        self.blademac       = '{0:>78}'.format('|           NODE2 MAC ADDR        |')
        self.getprov        = '{0:>78}'.format('|           GET PROV              |')
        self.provresults    = '{0:>78}'.format('|           PROV RESULTS          |')
        self.rsisready      = '{0:>78}'.format('|           RSIS READY            |')
        self.secalertready  = '{0:>78}'.format('|           SEC ALERT READY       |')
        self.secalertcomm   = '{0:>78}'.format('|           SET ALERT COMM        |')
        self.secalertinfo   = '{0:>78}'.format('|           SET ALERT INFO        |')
        self.setcmmaddr     = '{0:>78}'.format('|           SET NODE1 ADDR          |')
        self.setpassword    = '{0:>78}'.format('|           SET PASSWORD          |')
        self.setprovdata    = '{0:>78}'.format('|           SET PROV DATA         |')
        self.asterisks      = self.c_redblink + '|*********************************|' + self.resetcolor
        self.heading        = (self.c_yellow + self.columns + self.underline + self.resetcolor) 
        self.fromblade      = '|' + self.arrowl 
        self.toblade        = '|' + self.arrowr 

        self.graphdict  = {
                 '00' : self.cmdnone, 
                 '01' : self.setpassword, 
                 '10' : self.getslpto, 
                 'GM' : self.getmac,
                 'MR' : self.blademac,
                 '21' : self.setcmmaddr, 
                 'GP' : self.getprov,
                 'PR' : self.provresults,
                 'SP' : self.setprovdata,
                 'SR' : self.ack,
                 'A1' : self.ack, 
                 'AC' : self.secalertcomm, 
                 'AD' : self.secalertready, 
                 'FF' : self.cmdfailed 
        }

        # Flags
        self.verbose        = 0
        self.convert        = 0
        self.graph          = 0 

        self.processCmdLine()
        # Grab an iterator for a filtered version of the input beagle trace.
        self.reader = csv.reader(Filter(open(args[1], "rt")),delimiter=',')


    # Help output.
    def printUsage(self):
        print self.c_green  + "snoopy version 1.0\n" + self.resetcolor
        print self.c_green  + "Parses comma separated values from a beagle trace .csv file" + self.resetcolor
        print self.c_green  + "and presents the information in a more meaningful format." + self.resetcolor
        print ""
        print self.c_magenta + "Best used in a color terminal with a black background" + self.resetcolor
        print ""
        print self.c_yellow + "Usage:" + self.resetcolor
        print self.c_yellow + "snoopy <csv filename> <option> <optional: specific blade number>" + self.resetcolor
        print self.c_yellow + "Where:" + self.resetcolor
        print self.c_yellow + "Option = :" + self.resetcolor
        print self.c_yellow + "\t-s\tSummary  (default)" + self.resetcolor
        print self.c_yellow + "\t-c\tConvert  (convert to actual register names etc.)" + self.resetcolor
        print self.c_yellow + "\t-v\tVerbose" + self.resetcolor
        print self.c_yellow + "\t-g\tGraph    <optional blade number 1..14> (no blade entered graphs all blades)" + self.resetcolor

    # User input handling.
    def processCmdLine(self):
        numsysargs = len(self.args)
        if (numsysargs < 2):
            self.printUsage()
            sys.exit(0)
        elif (numsysargs == 2):
            if ('-h' in self.args[1]):
                self.printUsage()
                sys.exit(0)
            if not os.path.exists(self.args[1]):
                print '\n'
                print "Invalid file or pathname"
                print '\n'
                self.printUsage()
                sys.exit(0)
        elif ((numsysargs == 3) or (numsysargs == 4)):
               if (numsysargs == 4):
                     if (len(self.args[3]) == 1):
                         self.specblade = ('0' + self.args[3])
                     else:
                         self.specblade = self.args[3]
                     print 'specblade: ' + self.specblade
               if '-v' in self.args[2]:
                     self.verbose = 1
               elif '-c' in self.args[2]:
                    self.convert = 1
               elif '-g' in self.args[2]:
                    self.graph = 1
               elif '-s' in self.args[2]:
                    self.graph   = 0
                    self.convert = 0
                    self.verbose = 0 
               else:
                   print "Invalid option"
                   self.printUsage()
                   sys.exit(0)
        else:
            print "invalid number of arguments %d" % numsysargs
            self.printUsage()
            sys.exit(0)

    # Handle read event
    def processRead(self,Index,Addr,Time,Data,Err,Record):
        if ('*' in Addr) and ('*' in Data):
            if ((self.verbose == 1) or (self.convert == 1)):
        		print self.resetColor + Index + ' ' + self.c_red + Time,Err,Record if self.convert == 0 else 'Read from Register ',self.addrstring,Data + self.resetcolor
            self.totreads = self.totreads +1
            self.totreadbothnak = self.totreadbothnak + 1
        elif '*' in Addr:
            if ((self.verbose == 1) or (self.convert == 1)):
        		print self.resetcolor + Index + ' ' + self.resetcolor + Time,Err,Record if self.convert == 0 else 'Read from Register ',self.addrstring,Data + self.resetcolor
            self.totreads = self.totreads +1
            self.totreadaddrnak = self.totreadaddrnak + 1
        elif ('*' in Data) and ('Read' not in Record): # bypass if read cause they all show nak (revisit)
            if ((self.verbose == 1) or (self.convert == 1)):
        		print self.resetcolor + Index + ' ' + self.c_magenta + Time,Err,Record if self.convert == 0 else 'Read from Register ',self.addrstring,Data + self.resetcolor
            self.totreads = self.totreads +1
            self.totreaddatanak = self.totreaddatanak + 1
        else: 
            if ((self.verbose == 1) or (self.convert == 1)):
        	    print self.resetcolor + Index + ' ' + self.c_cyan + Time,Err,Record if self.convert == 0 else 'Read from Register ',self.addrstring,Data + self.resetcolor
            self.totreads = self.totreads +1
            self.totreadsucc = self.totreadsucc +1
    
    # Handle write event
    def processWrite(self,Index,Addr,Time,Data,Err,Record):
        if ('*' in Addr) and ('*' in Data):
            if ((self.verbose == 1) or (self.convert == 1)):
        		print self.resetcolor + Index + ' ' + self.c_red + Time,Err,Record if self.convert == 0 else 'Write to Register  ',self.addrstring,Data + self.resetcolor
            self.totwrits = self.totwrits +1
            self.totwritbothnak = self.totwritbothnak + 1
        elif '*' in Addr:
            if ((self.verbose == 1) or (self.convert == 1)):
        		print self.resetcolor + Index + ' ' + self.resetcolor + Time,Err,Record if self.convert == 0 else 'Write to Register  ',self.addrstring,Data + self.resetcolor
            self.totwrits = self.totwrits +1
            self.totwritaddrnak = self.totwritaddrnak + 1
        elif ('*' in Data):
            if ((self.verbose == 1) or (self.convert == 1)):
        		print self.resetcolor + Index + ' ' + self.c_magenta + Time,Err,Record if self.convert == 0 else 'Write to Register  ',self.addrstring,Data + self.resetcolor
            self.totwrits = self.totwrits +1
            self.totwritdatanak = self.totwritdatanak + 1
        else: 
            if ((self.verbose == 1) or (self.convert == 1)):
        	    print self.resetcolor + Index + ' ' + self.c_green + Time,Err,Record if self.convert == 0 else 'Write to Register  ',self.addrstring,Data + self.resetcolor
            self.totwrits = self.totwrits +1
            self.totwritsucc = self.totwritsucc +1

    # Handle corrupt event
    def processCorrupt(self,Index,Addr,Time,Data,Err,Record):
        if (self.verbose == 1) or (self.convert == 1):
            print Index + self.c_redblink + Time,Err,Record,Addr,Data + self.resetcolor
        elif (self.graph == 1):
            print self.blankline
            sys.stdout.write(self.c_red   + '{0:>10} '.format(Index) + self.resetcolor)
            sys.stdout.write(self.c_red   + '{0:>20} '.format(Time)  + self.resetcolor)
            sys.stdout.write('{0:>60}'.format(self.asterisks))
            sys.stdout.write(self.c_red   + '({0:2})'.format(self.blade) + self.resetcolor)
            print self.c_red   + Err,Record,Addr,Data + self.resetcolor
        self.totcorrupt = self.totcorrupt + 1

    # Graph the event
    def graphIt(self,Index,Addr,Time,Data,Err,Record):
        info = Data.split() 
        paint = self.blankline
        try:
            if ('68' in Addr) and ('Write' in Record):
                self.blade = info[0]
            if ((self.blade not in self.specblade) and (len(self.args) == 4)):
                return 
            if ('FD' in info[0]):
                try:
                    print self.blankline
                    if ('31' in info[2]):
                        if ('Write' in Record):
                            print self.graphdict['GP']
                            paint = self.toblade
                        elif ('Read' in Record):
                            print self.graphdict['PR']
                            paint = self.fromblade
                    elif ('30' in info[2]):
                        if ('Write' in Record):
                            print self.graphdict['SP']
                            paint = self.toblade
                        elif ('Read' in Record):
                            print self.graphdict['SR']
                            paint = self.fromblade
                    elif ('20' in info[2]):
                        if ('Write' in Record):
                            print self.graphdict['GM']
                            paint = self.toblade
                        elif ('Read' in Record):
                            print self.graphdict['MR']
                            paint = self.fromblade
                    else:
                        if ('01' in info[2]) or \
                           ('10' in info[2]) or \
                           ('A1' in info[2]) or \
                           ('21' in info[2]) or \
                           ('AD' in info[2]) :
                              print self.graphdict[info[2]]
                              if ('Write' in Record):
                                   paint = self.toblade
                              elif ('Read' in Record):
                                   paint = self.fromblade
                    sys.stdout.write(self.c_cyan   + '{0:>10} '.format(Index) + self.resetcolor)
                    sys.stdout.write(self.c_yellow + '{0:>20} '.format(Time)  + self.resetcolor)
                    sys.stdout.write('{0:>60}'.format(paint))
                    sys.stdout.write('({0:2})'.format(self.blade))
                    sys.stdout.write('\n')
                except:
                    pass 
        except:
            pass

    # Determine address (register being read to or written to) and how it is to be represented.
    def setAddr(self,Addr):
        if (self.convert == 1):
            if '1C'in Addr:
                self.addrstring = '38'        
            if '68'in Addr:
                self.addrstring = 'D0'        
            if '5A'in Addr:
                self.addrstring = 'B4'        
            if '72'in Addr:
                self.addrstring = 'E4'        
            if '1B'in Addr:
                self.addrstring = '36'        
            if '71'in Addr:
                self.addrstring = 'E2'        
        else:
            self.addrstring = Addr

        
    # File cruncher 
    def processFile(self):  
        # Get the columns for parsing.
        if (self.graph == 1):
                print self.heading
        for Level,Index,Time,Dur,Len,Err,SP,Addr,Record,Data in self.reader:
            self.setAddr(Addr) 
            if 'Corrupt' in Record:
                self.processCorrupt(Index,Addr,Time,Data,Err,Record)
            if (self.graph == 0):
                if 'Read' in Record:
                    self.processRead(Index,Addr,Time,Data,Err,Record) 
                elif 'Write' in Record:
                    self.processWrite(Index,Addr,Time,Data,Err,Record)
            else:
                self.graphIt(Index,Addr,Time,Data,Err,Record)
     
    def printSummary(self):  
        # Print summary information.
        print '\n'
        print '=================================================================='
        print '\n'
        print (self.c_bluedim if self.totreads           == 0 else self.c_white)    + 'READ attempts:\t\t\t% 12d'    % self.totreads        + self.resetcolor
        print (self.c_bluedim if self.totreadaddrnak     == 0 else self.c_yellow)   + '\tread addr nacked:\t% 12d'   % self.totreadaddrnak  + self.resetcolor
        print (self.c_bluedim if self.totreaddatanak     == 0 else self.c_magenta)  + '\tread data nacked:\t% 12d'   % self.totreaddatanak  + self.resetcolor
        print (self.c_bluedim if self.totreadbothnak     == 0 else self.c_red)      + '\tread both nacked:\t% 12d'   % self.totreadbothnak  + self.resetcolor
        print (self.c_bluedim if self.totreadsucc        == 0 else self.c_green)    + '\tread successful:\t% 12d'    % self.totreadsucc     + self.resetcolor
        if (self.totreads != 0):
            print (self.c_bluedim if self.totreads       == 0 else self.c_white)    +  '\tread success rate:\t' + "{0:12.2f}%".format(float(self.totreadsucc)/self.totreads * 100) + self.resetcolor
            print '\n'
            print (self.c_bluedim if self.totwrits       == 0 else self.c_white)    + 'WRITE attempts:\t\t\t% 12d'   % self.totwrits        + self.resetcolor
            print (self.c_bluedim if self.totwritaddrnak == 0 else self.c_yellow)   + '\twrite addr nacked:\t% 12d'  % self.totwritaddrnak  + self.resetcolor
            print (self.c_bluedim if self.totwritdatanak == 0 else self.c_magenta)  + '\twrite data nacked:\t% 12d'  % self.totwritdatanak  + self.resetcolor
            print (self.c_bluedim if self.totwritbothnak == 0 else self.c_red)      + '\twrite both nacked:\t% 12d'  % self.totwritbothnak  + self.resetcolor
            print (self.c_bluedim if self.totwritsucc    == 0 else self.c_green)    + '\twrite successful:\t% 12d'   % self.totwritsucc     + self.resetcolor
        if (self.totwrits != 0):
            print (self.c_bluedim if self.totwrits       == 0 else self.c_white)    + '\twrite success rate:\t' + "{0:12.2f}%".format(float(self.totwritsucc)/self.totwrits * 100) + self.resetcolor
            print '\n'
            print (self.c_bluedim if self.totcorrupt     == 0 else self.c_redblink) + 'CORRUPTED events:\t\t% 12d'   % self.totcorrupt      + self.resetcolor
        
    def main(self):
        self.processFile()
        if (self.graph != 1):
            self.printSummary()
        
def main(argv=None):
    s = Snoopy(sys.argv)
    s.main()

   
if __name__ == '__main__':
    status = main()
    sys.exit(status)
