import os
import json
from configparser import ConfigParser

hmbtgparser = ConfigParser()
hmbtgparser.read('/etc/ckan/default/hmbtg.ini')


def ensureParser():
    hmbtgparser = ConfigParser()
    hmbtgparser.read('/etc/ckan/default/hmbtg.ini')

def getConfValue(val, default=None):
    try:
        ensureParser()
        return hmbtgparser.get('hmbtg_config', val)
    except:
        if default:
            return default
        return None

def getConfJson(val, default=None):
    try:
        ret = hmbtgparser.get('hmbtg_config', val)
        return json.loads(ret)
    except:
        return default


def get(key, default=None):
    try:
        return getConfValue(key)
    except:
        return default

def setGlobalVars():
    ensureParser()
    options = hmbtgparser.options('hmbtg_config')
    for item in options:
        os.system("export " + item + "=" + hmbtgparser.get('hmbtg_config',item))


def getConfValueFromSection(section, val, default=None):
    try:
        return hmbtgparser.get(section, val)
    except:
        return default


def setConfValue(key, val):
    ensureParser()
    return hmbtgparser.set('hmbtg_config', key, val)
