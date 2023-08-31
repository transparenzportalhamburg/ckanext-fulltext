
from ckanext.fulltext.postprocess.moving_window import ClearText
from nose.tools import assert_equal
from ckanext.fulltext.postprocess.utils import _get_words_arr

def test_get_words_arr():
    assert_equal(_get_words_arr('test'), ['test'])
    assert_equal(_get_words_arr('  test '), ['test'])
    assert_equal(_get_words_arr('  t&est '), ['t', 'est'])
    assert_equal(_get_words_arr('  t...est '), ['t', 'est'])
    assert_equal(_get_words_arr('  t??est '), ['t', 'est'])
    assert_equal(_get_words_arr('[test]'), ['test'])
    assert_equal(_get_words_arr('[te]st]'), ['te]st']) ## ok?
    assert_equal(_get_words_arr('['), []) 
    assert_equal(_get_words_arr(' te s   t', '   '), ['te', 's', 't'])
    assert_equal(_get_words_arr(' te s   t', ' '), ['te', 's', 't'])

def test_cleartext_complex():
    # Arrange
    ct = ClearText()
    text = 'http://mehran.ir mehran@hamburg.de P r ä s i d e n t  d e s  S e n a t s abcde-hgh de r-bahn   BgmI s-bahn st.pauli -  (Erster)  Bürgermeister Olaf Scholz ham burg-sü d un   d altona-nord oder Gesetzesbes- und test straße'
    # Act
    cleared, wrong = ct.clear_text(text)
    # Assert
    assert_equal(cleared.encode('utf-8'), b'Pr\xc3\xa4sident Senats bahn sbahn pauli B\xc3\xbcrgermeister Olaf Scholz hamburg s\xc3\xbcd altona-nord test stra\xc3\x9fe')

# def test_cleartext_preprocess():
#     # Arrange
#     ct = ClearText()
#     text = u'http://mehran.ir mehran@hamburg.de P r ä s i d e n t  d e s  S e n a t s abcde-hgh de r-bahn   BgmI s-bahn st.pauli -  (Erster)  Bürgermeister Olaf Scholz ham burg-sü d un   d altona-nord oder Gesetzesbes- und test straße'
#     # Act
#     text = ct._preprocess_text(text)
#     # Assert
#     nose.tools.assert_equal(text, '')

# def test_cleartext_preprocess():
#     # Arrange
#     ct = ClearText()
#     text = u'a ä foo-bar s-bahn st.pauli -   Erster r-bahn H-a-u-s  Ha&us test@me.com http'
#     # Act
#     ret = ct._preprocess_text(text)
#     # Assert
#     nose.tools.assert_equal(ret, ['a', u'ä', 'foo', 'bar', 'sbahn', 'st', 'pauli', 'Erster', 'r', 'bahn', 'Haus', 'Ha&us', 'test@me.com', 'http'])

def test_cleartext_simple():
    # Arrange
    ct = ClearText()
    text = 'Senat'
    # Act
    cleared, wrong = ct.clear_text(text)
    # Assert
    assert_equal(cleared, 'Senat')

def test_cleartext_skip():
    # Arrange
    ct = ClearText()
    text = 'Senat'
    # Act
    cleared, notFound = ct.clear_text('test@me.de http://test foo2bar e Ha u s')
    assert_equal(cleared, 'Haus')
    assert_equal(notFound, [])

# def test_problematic_url():
#     from ckanext.fulltext.parser.tikaparser import parse_with_tika
#     url = 'http://daten.transparenz.hamburg.de/Dataport.HmbTG.ZS.Webservice.GetRessource100/GetRessource100.svc/011c3897-d0c6-4f3e-896c-5656c707cebe/Genehmigung_nach_HBauO.pdf'
#     text = parse_with_tika(url)
#     ct = ClearText()
#     cleared, wrong = ct.clear_text(text)
#     # import ipdb; ipdb.set_trace()
