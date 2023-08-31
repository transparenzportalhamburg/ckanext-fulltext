import subprocess
import sys 
import importlib
import ckanext.fulltext.hmbtg_config as hmbtg_config
import configparser

found_error = False

config = configparser.RawConfigParser()
config.read(['/etc/ckan/default/development.ini'])

def assert_pip(val, exp):
    if not exp in val:
        global found_error
        found_error = True
        print(('expected "%s" to be installed via pip' % exp))


def assert_module(m):
    try:
        importlib.import_module(m)
    except:
        global found_error
        found_error = True
        print(('failed to import "%s"' % m))


def assert_conf_subset(key, exp):
    val = hmbtg_config.getConfValue(key)
    if not set(exp.split(' ')).issubset(set(val.split(' '))):
        global found_error
        found_error = True
        print((
            'expected list config value for key "%s" to contain "%s", but was "%s"'
            % (key, exp, val)))


def assert_hmbtg_conf_equal(key, exp):
    val = None
    try:
        val = hmbtg_config.getConfValue(key)
    except configparser.NoOptionError:
        pass
    if not val == exp:
        global found_error
        found_error = True
        print(('expected config value for key "%s" to be "%s", but was "%s"' %
              (key, exp, val)))

def assert_conf_equal(key, exp):
    val = None
    try:
        val = config.get('app:main', key)
    except configparser.NoOptionError:
        pass
    if not val == exp:
        global found_error
        found_error = True
        print(('expected config value for key "%s" to be "%s", but was "%s"' %
              (key, exp, val)))


def check_pip():
    reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    assert_pip(reqs, 'rq==0.6.0')
    # assert_pip(reqs, 'rq-dashboard')
    assert_pip(reqs, 'patool')
    assert_pip(reqs, 'rarfile')


def check_modules():
    assert_module('zipfile')
    assert_module('rarfile')

def check_config():
    assert_conf_subset('fulltext.format_blacklist', 'gml xml tiff shp png jpg jpeg pgw xyz')
    assert_hmbtg_conf_equal('fulltext.maxchars_from_db', '52428800')
    assert_hmbtg_conf_equal('fulltext.file_maxsize', '104857600')
    assert_hmbtg_conf_equal('fulltext.clean.sources', 'Workflow')

def check_redis():
    import rq
    rq.use_connection()
    try:
        q = rq.Queue()
        q.all()
    except:
        print('could not connect to redis')
        global found_error
        found_error = True

def check_directories():
    #TODO
    pass


if __name__ == '__main__':
    check_pip()
    check_modules()
    check_config()
    check_redis()