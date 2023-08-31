from ckanext.fulltext.parser.tikatools import Tikatools
from nose.tools import assert_equal
def test_handle_redirect():
    tools = Tikatools()
    url = 'http://www.buergerschaft-hh.de/parldok/tcl/PDDocView.tcl?mode=get&lp=21&doknum=14487'
    ret = tools.handle_JS_redirect(url)
    assert_equal(ret,url)

