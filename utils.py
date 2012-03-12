#!/usr/bin/python

import fileinput
import sys

prj_name="myca"

#
# Replace all occurances of searchExp with replaceExp
#
def replaceAll(file, searchExp, replaceExp):
    for line in fileinput.input(file, inplace=1):
        line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

