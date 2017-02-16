#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
It takes a FASTQ file generated by Illumina Solexa pipeline version 1.8 (or newer) and it
converts the header of the reads (i.e. read names have one space) to the older Solexa Fastq
format (where the reads end with /1 or /2). Also the reads marked as filtered can be
optionally be filtered out.



Author: Daniel Nicorici, Daniel.Nicorici@gmail.com

Copyright (c) 2009-2017 Daniel Nicorici

This file is part of FusionCatcher.

FusionCatcher is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

FusionCatcher is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with FusionCatcher (see file 'COPYING.txt').  If not, see
<http://www.gnu.org/licenses/>.

By default, FusionCatcher is running BLAT aligner
<http://users.soe.ucsc.edu/~kent/src/> but it offers also the option to disable
all its scripts which make use of BLAT aligner if you choose explicitly to do so.
BLAT's license does not allow to be used for commercial activities. If BLAT
license does not allow to be used in your case then you may still use
FusionCatcher by forcing not use the BLAT aligner by specifying the option
'--skip-blat'. Fore more information regarding BLAT please see its license.

Please, note that FusionCatcher does not require BLAT in order to find
candidate fusion genes!

This file is not running/executing/using BLAT.
"""

#
"""
Example:
It changes:
@GQWE8:57:C00T6ABXX:2:1101:1233:2230 1:N:0:CTTGTA

to

@GQWE8:57:C00T6ABXX:2:1101:1233:2230/1
"""
import os
import sys
import optparse
import string
import shutil
import errno
import gc
import gzip

if __name__=='__main__':

    #command line parsing

    usage = "%prog [options]"
    description = """It takes a FASTQ file generated by Illumina Solexa pipeline version 1.8 (or newer) and it converts the header of the reads (i.e. read names have one space) to the older Solexa Fastq format (where the reads end with /1 or /2). Also the reads marked as filtered can be optionally be filtered out. Example: It changes @GQWE8:57:C00T6ABXX:2:1101:1233:2230 1:N:0:CTTGTA to @GQWE8:57:C00T6ABXX:2:1101:1233:2230/1"""
    version = "%prog 0.10 beta              Author: Daniel Nicorici, E-mail: Daniel.Nicorici@gmail.com"

    parser = optparse.OptionParser(usage = usage,
                                   description = description,
                                   version = version)

    parser.add_option("--input",
                      action = "store",
                      type = "string",
                      dest = "input_filename",
                      help = """The input file (in the newer Solexa FASTQ format, i.e. version 1.8 or newer) containing the short reads to be processed.""")

    parser.add_option("--output",
                      action = "store",
                      type = "string",
                      dest = "output_filename",
                      help = """The output FASTQ file containing the short read such that the read names are changed in such way that they end with /1 or /2. If the input file contains reads which end in /1 or /2 then the reads will be copied to the output without any modification""")

    parser.add_option("--skip_filter",
                      action = "store_true",
                      dest = "filter",
                      default = False,
                      help = """It filters out the reads which have been marked by Illumina as filtered. Default is %default.""")

    parser.add_option("--fail",
                      action = "store_true",
                      dest = "fail",
                      default = False,
                      help = """In case that the short reads names do not end with /1 or /2 or are not in format '@GQWE8:57:C00T6ABXX:2:1101:1233:2230 1:N:0:CTTGTA' then the script will exit with an exit error code. Default is %default.""")

    choices = ('soft','hard','copy')
    parser.add_option("--link",
                      action = "store",
                      choices = choices,
                      dest = "link",
                      default = 'soft',
                      help = """It creates a link from the output file to the input file of type ("""+','.join(choices)+""") in case that no operation is done on the input file. Default is '%default'.""")


    (options, args) = parser.parse_args()

    # validate options
    if not (options.input_filename and
            options.output_filename
            ):
        parser.print_help()
        parser.error("No inputs and outputs specified!")

    print >>sys.stderr,"Starting..."
    # check if the FASTQ file is in format produced by CASAVA pipeline version 1.8
    t = file(options.input_filename,"r").readline()
    if not t:
        print >>sys.stderr,"ERROR: The input file '%s' is empty!" % (options.input_filename,)
        sys.exit(1)
    t = t.rstrip("\r\n").rstrip()

    if not t.startswith("@"):
        print >>sys.stderr,"ERROR: The input file '%s' is not in FASTQ file format!" % (options.input_filename,)
        print >>sys.stderr,"The read names in the input file look like '%s'." % (t,)
        sys.exit(1)


    version_15 = False
    if ((t.endswith('/1') or t.endswith('/2')) and
        t.find(' ') == -1 and
        t.find('\t') == -1):
        version_15 = True

    version_18 = False
    if (not version_15) and len(t.split(" ")) >= 2:
        t = t.split(" ")
        t0 = t[0].split(":")
        t1 = t[1].split(":")
        if len(t0) == 7 and len(t1) == 4 and (t1[0] == '1' or t1[0] == '2'):
            version_18 = True

    if options.fail and (not version_15) and (not version_18):
            print >>sys.stderr,"ERROR: The input FASTQ file is not in a supported FASTQ format, which are:"
            print >>sys.stderr," - version 1.5 (i.e. read names end with /1 or /2 and contain no blank characters)"
            print >>sys.stderr," - version 1.8 (e.g. read name looks like '@GQWE8:57:C00T6ABXX:2:1101:1233:2230 1:N:0:CTTGTA')"
            print >>sys.stderr,"The read names in the input file look like this '%s' but it should look like this '@GQWE8:57:C00T6ABXX:2:1101:1233:2230 1:N:0:CTTGTA' (i.e. there should be 6 of ':' in read name, one blank space between read name and description, description should be in this format '1:N:0:CTTGTA')" % (t,)
            sys.exit(1)
    #
    if not version_18:
        print >>sys.stderr,"No changes are done!"
        if os.path.isfile(options.output_filename):
            os.remove(options.output_filename)
        if options.link == 'soft':
            if os.path.islink(options.input_filename):
                linkto = os.readlink(options.input_filename)
                os.symlink(linkto,options.output_filename)
            else:
                os.symlink(options.input_filename,options.output_filename)
        elif options.link == 'hard':
            linkto = options.input_filename
            if os.path.islink(options.input_filename):
                linkto = os.readlink(options.input_filename)
            try:
                os.link(linkto,options.output_filename)
            except OSError as er:
                print >>sys.stderr,"WARNING: Cannot do hard links ('%s' and '%s')!" % (linkto,options.output_filename)
                shutil.copyfile(linkto,options.output_filename)
#                if er.errno == errno.EXDEV:
#                    # they are on different partitions
#                    # [Errno 18] Invalid cross-device link
#                    shutil.copyfile(linkto,options.output_filename)
#                else:
#                    print >>sys.stderr,"ERROR: Cannot do hard links ('%s' and '%s')!" % (linkto,options.output_filename)
#                    print >>sys.stderr,er
#                    sys.exit(1)

        elif options.link == 'copy':
            shutil.copyfile(options.input_filename, options.output_filename)
        else:
            print >>sys.stderr, "ERROR: unknown operation of linking!", options.link
            sys.exit(1)
    else:
        print >>sys.stderr,"The input file is in FASTQ format compatible with Illumina pipeline CASAVA version 1.8!"
        print >>sys.stderr,"The short read names will be changed (i.e. adding /1 and /2)!"
        flag = options.filter
        buffer_size = 10**8
        if flag:
            fin = open(options.input_filename,'r')
            fou = open(options.output_filename,'w')
            i = -1
            while True:
                gc.disable()
                lines = fin.readlines(buffer_size)
                gc.enable()
                if not lines:
                    fou.writelines(lines)
                    break
                n = len(lines)
                for j in xrange(n):
                    i = i + 1
                    if i == 0: # id
                        r = lines[j].partition(" ")
                        if r[2].startswith("1:"):
                            lines[j] = r[0] + "/1\n"
                        elif r[2].startswith("2:"):
                            lines[j] = r[0] + "/2\n"
                    elif i == 2:
                        lines[j] = "+\n"
                    elif i == 3: # quality scores
                        i = -1
                fou.writelines(lines)
            fin.close()
            fou.close()
        else:
            print >>sys.stderr,"Filtering out the reads marked by Illumina SOLEXA as Y."
            fin = open(options.input_filename,'r')
            fou = open(options.output_filename,'w')
            i = -1
            good = False
            while True:
                gc.disable()
                lines = fin.readlines(buffer_size)
                gc.enable()
                if not lines:
                    fou.writelines(lines)
                    break
                data = []
                for line in lines:
                    i = i + 1
                    if i == 0: # id
                        r = line.partition(" ")
                        if r[2].startswith("1:N:"):
                            gc.disable()
                            data.append(r[0] + "/1\n")
                            gc.enable()
                            good = True
                        elif r[2].startswith("2:N:"):
                            gc.disable()
                            data.append(r[0] + "/2\n")
                            gc.enable()
                            good = True
                        else:
                            good = False
                    elif i == 3: # quality scores
                        i = -1
                        if good:
                            gc.disable()
                            data.append(line)
                            gc.enable()
                        good = False
                    elif good:
                        if i == 1:
                            gc.disable()
                            data.append(line)
                            gc.enable()
                        elif i == 2:
                            gc.disable()
                            data.append("+\n")
                            gc.enable()
                if data:
                    fou.writelines(data)
            fin.close()
            fou.close()


    print >>sys.stderr,"Done."
