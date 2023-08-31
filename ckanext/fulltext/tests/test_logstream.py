import logging
from nose.tools import assert_equal
from ckanext.fulltext.jobs import LogStream

def log(msg):
    logger = logging.getLogger(__name__)
    logger.debug(msg)


def create_logger():
    stream = LogStream()
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return stream


def test_unicode():
    stream = create_logger()
    log('/tmp/tmpVMwsYC/vorl\xe4ufig_gesicherte_\xdcberschwemmungsgebiete.xsd')
    log('äöü')
    log('sdsfsa')
    log('äöü')

    assert_equal(len(str(stream).split('\n')), 5)


def test_unicode_format():
    stream = create_logger()
    msgs = [
        '/tmp/tmpVMwsYC/vorl\xe4ufig_gesicherte_\xdcberschwemmungsgebiete.xsd',
        'äöü',
        'sdsfsa', 
        'äöü'
    ]

    for locator in msgs:
        log(f'start fetching {locator}')

    assert_equal(len(str(stream).split('\n')), 5)
