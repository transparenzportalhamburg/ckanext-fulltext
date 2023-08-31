
from mock import patch, MagicMock
from ckanext.fulltext.parser import hmbtg_utils
from ckanext.fulltext.parser.tikaparser import ResourceNotFound
import ckanext.fulltext.hmbtg_config as hmbtg_config
import nose

@patch('ckanext.fulltext.parser.tikatools.parse_with_tika')
@nose.tools.raises(ResourceNotFound)
def test_handleURLandFulltext_with_exception(tikaMock):
    # Arrange
    tikaMock.side_effect = ResourceNotFound()
    utils = hmbtg_utils.Hmbtg_Utils()
    # Act
    fulltext = utils.handleURLandFulltext('/tmp/test2.txt', '', '', False, False, True, False, None, 1, True)

@patch('ckanext.fulltext.parser.hmbtg_utils.hmbtg_config')
def test_handleURLandFulltext_with_blacklist(mock):
    try:
        # Arrange
        mock.getConfValueFromSection.return_value = 'txt'
        utils = hmbtg_utils.Hmbtg_Utils()
        # hmbtg_config.setConfValue("fulltext.format_blacklist", 'txt')
        # Act
        fulltext = utils.handleURLandFulltext('/tmp/test2.txt', '', '', False, False, True, False, None, 1, True)
        # Assert
        nose.tools.assert_equals(fulltext, '')
    finally:
        hmbtg_config.setConfValue("fulltext.format_blacklist", '')

# seems to be flaky
def test_handleURLandFulltext_existing_url():
    utils = hmbtg_utils.Hmbtg_Utils()
    fulltext = utils.handleURLandFulltext('https://metaver.de/trefferanzeige?docuuid=57C90E27-5116-4221-A9D9-E02C8FEE245D', '', '', False, False, True, False, None, 1, True)
    assert fulltext.startswith("Teilbebauungsplan TB 17 Hamburg - MetaVer ")