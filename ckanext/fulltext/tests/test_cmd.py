from ckanext.fulltext.postprocess.clean import main as clean
from ckanext.fulltext.postprocess.clean import _clean_text
from ckanext.fulltext.tests.helpers import create_dataset

def test_empty_clean():
    clean(mode="empty")

def test_all_clean():
    clean(mode="all")

def test_id_clean():
    r_id = "some_id"
    clean(mode=r_id)

def test_clear_text():
    pkg = create_dataset(fulltext="t e s t")
    _clean_text(pids=[pkg["id"]])
    #pkgdb = get_package(pkg['id'])
    #resources = pkgdb['resources']
    #assert resources[0]['fulltext'] == 'fulltext
