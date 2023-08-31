import nose, os
from ckanext.fulltext.parser import tikatools
from .test_archiver import create_nested_archive, create_file, create
from mock import patch
from ckanext.fulltext.tests.server_mock import PORT
def test_extract_fulltext_from_archive():
    # Arrange
    path, archive = create_nested_archive()
    tika = tikatools.Tikatools()
    def clb(p): return 'fulltext'
    # Act
    fulltext = tika.extract_fulltext_from_archive(archive, clb, [])
    # Assert
    nose.tools.assert_in(path, fulltext)
    nose.tools.assert_equals(fulltext.count('fulltext'), 10)

def test_extract_fulltext_from_archive_with_exception():
    # Arrange
    path, archive = create_nested_archive()
    tika = tikatools.Tikatools()
    count = len(os.listdir('/tmp'))
    def clb(p): raise Exception()
    # Act
    try:
        fulltext = tika.extract_fulltext_from_archive(archive, clb, [])
    except:
        pass
    # Assert
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))

@patch('ckanext.fulltext.parser.tikatools.parse_with_tika')
def test_get_text_content_for_filepath_with_none(tikaMock):
    # Arrange
    tikaMock.return_value = None
    tika = tikatools.Tikatools()
    # Act
    fulltext = tika.get_text_content_for_filepath('/tmp/test2.txt', '', '', False, '', '', '', '', False, '')
    # Assert
    nose.tools.assert_equals(fulltext, '')

def test_get_text_content_for_filepath_for_file():
    # Arrange
    tika = tikatools.Tikatools()
    create_file('/tmp', 'test2.txt', 'test2.txt')
    # Act
    fulltext = tika.get_text_content_for_filepath('/tmp/test2.txt', '', '', False, '', '', '', '', False, '')
    # Assert
    nose.tools.assert_in('test2.txt', fulltext)

def test_get_text_content_for_filepath_can_handle_utf8():
    # Arrange
    tika = tikatools.Tikatools()
    xml ="""
    <?xml version="1.0" encoding="UTF-8"?>
    <schema>
    </schema>
    """
    create_file('/tmp', 'test.xml', xml)
    # Act
    fulltext = tika.get_text_content_for_filepath('/tmp/test.xml', '', '', False, '', '', '', '', False, '')
    # Assert
    nose.tools.assert_in(xml.strip(), fulltext)

def test_get_text_content_for_archive(server):
    try:
        tika = tikatools.Tikatools()
        path, archive = create(['test.txt'], ['fulltext'], asZip=True)
        server.set_file(archive)
        # Act
        fulltext = tika.get_text_content(f'http://localhost:{PORT}/archive.zip','','',False,'','','',False,False,False,None)
        # Assert
        nose.tools.assert_in('fulltext', fulltext)
    finally:
        pass
