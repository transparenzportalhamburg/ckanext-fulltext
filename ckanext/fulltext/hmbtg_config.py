#!/usr/bin/python
import sys
from ConfigParser import SafeConfigParser

hmbtgparser = SafeConfigParser()
hmbtgparser.read('/etc/ckan/default/hmbtg.ini')


def ensureParser():
	hmbtgparser = SafeConfigParser()
	hmbtgparser.read('/etc/ckan/default/hmbtg.ini')

#if len(sys.argv) > 1:
#	print hmbtgparser.get('hmbtg_config', sys.argv[1])

def getConfValue(val):
	ensureParser()
	return hmbtgparser.get('hmbtg_config', val)

def setGlobalVars():
	ensureParser()
	options = hmbtgparser.options('hmbtg_config')
        for item in options:
        	os.system("export " + item + "=" + hmbtgparser.get('hmbtg_config',item))

