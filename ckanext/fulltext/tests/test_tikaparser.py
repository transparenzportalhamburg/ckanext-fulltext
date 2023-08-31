import os
import nose
import subprocess
from mock import patch

from ckanext.fulltext.tests.server_mock import DATA_PATH, SERVER_URL, PORT
from ckanext.fulltext.parser.tikatools import parse_with_tika

def test_call_tika_from_many_processes():
    # Act
    exec(compile(open(os.path.join(os.path.dirname(__file__), 'call_tika.py'), "rb").read(), os.path.join(os.path.dirname(__file__), 'call_tika.py'), 'exec'))
    exec(compile(open(os.path.join(os.path.dirname(__file__), 'call_tika.py'), "rb").read(), os.path.join(os.path.dirname(__file__), 'call_tika.py'), 'exec'))
    exec(compile(open(os.path.join(os.path.dirname(__file__), 'call_tika.py'), "rb").read(), os.path.join(os.path.dirname(__file__), 'call_tika.py'), 'exec'))
    # Assert
    pl = subprocess.Popen(['ps', '-aux'], stdout=subprocess.PIPE).communicate()[0]
    nose.tools.assert_equal(pl.count('TikaServer'.encode("utf-8")), 1)


def test_parse_website(server):
    filename =  'google'
    path = DATA_PATH + filename
    url = SERVER_URL + filename
    server.set_file(path)
    # Act
    ret = parse_with_tika(url)
    nose.tools.assert_in('Google', ret)


def test_parse_longurl(server):
    # Arrange
    server.set_text('Body')
    count = len(os.listdir('/tmp'))

    # Act
    ret = parse_with_tika(f'http://localhost:{PORT}/'+'long'*100)

    # Assert
    nose.tools.assert_in('Body', ret)
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))


def test_parse_file():
    # Arrange
    with open('/tmp/test', 'wb') as f:
        f.write('test'.encode())
    # Act
    ret = parse_with_tika('/tmp/test')
    # Assert
    nose.tools.assert_equal(ret.strip(), 'test')


def test_parse_file_with_umlauts():
    # Arrange
    path = '/tmp/testö'
    with open(path, 'w') as f:
        f.write('test')
    # Act
    ret = parse_with_tika(path)
    # Assert
    nose.tools.assert_equal(ret.strip(), 'test')


def test_parse_file_with_umlauts2():
    # Arrange
    path = '/tmp/Erläuterungen.csv'
    
    with open(path, 'w') as f:
        f.write('test')
    # Act
    ret = parse_with_tika(path)
    # Assert
    nose.tools.assert_equal(ret.strip(), 'test')


def test_parse_file_with_bad_encoding():
    # Arrange
    path = '/tmp/Digitaler_Gr\x81nplan_HH-2015-07-07.xsd'
    with open(path, 'w') as f:
        f.write('test')
    # Act
    ret = parse_with_tika(path)
    # Assert
    nose.tools.assert_equal(ret.strip(), 'test')


def test_tika_does_not_pollute_tmp(server):
    # Arrange
    filename =  'google'
    path = DATA_PATH + filename
    url = SERVER_URL + filename
    server.set_file(path)
    parse_with_tika(url) ## ensure tika.jar was already downloaded
    count = len(os.listdir('/tmp'))
    # Act
    ret = parse_with_tika(url)
    # Assert
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))


@patch('ckanext.hmbtgharvesters.fetch')
def test_tika_does_not_pollute_tmp_after_exception(fetchMock):
    # Arrange
    def mock(a, b):
        raise Exception()
    fetchMock.to_file = mock
    count = len(os.listdir('/tmp'))
    # Act
    try:
        ret = parse_with_tika('http://www.google.de')
    except:
        pass
    # Assert
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))


def test_parse_bug_393(server):
    # Arrange
    filename =  'HH_WFS_INSPIRE_Hydro_Physische_Gewaesser_ATKIS'
    path = DATA_PATH + filename
    url = SERVER_URL + filename
    server.set_file(path)
    
    ret = parse_with_tika(url)
    nose.tools.assert_true('Basis-DLM' in ret)


def test_parse_bug_381(server):
    # Arrange
    filename = 'vo020.asp_VOLFDNR_1001285'
    path = DATA_PATH + filename
    url = SERVER_URL + filename
    server.set_file(path)
    
    ret = parse_with_tika(url)
    nose.tools.assert_true('Drucksache' in ret)


def test_parse_bug_30(server):
    # Arrange
    filename = 'organigramm.pdf'
    path = DATA_PATH +filename
    url = SERVER_URL + filename
    server.set_file(path)
    ret = parse_with_tika(url)
    nose.tools.assert_true('Hamburgische Bürgerschaft' in ret)

