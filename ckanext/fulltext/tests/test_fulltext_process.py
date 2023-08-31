import pytest
from ckanext.fulltext.tests.helpers import create_dataset
from ckanext.fulltext.postprocess.resource_fulltext_process import get_pkg_ids
from nose.tools import assert_in, assert_not_in

def seq_assert_in(expt, act):
    for e in expt:
        assert_in(e['id'], act)

def seq_assert_not_in(expt, act):
    for e in expt:
        assert_not_in(e['id'], act)

def test_get_pkg_ids():
    pkg1 = create_dataset()
    pkg2 = create_dataset(fulltext='UNPROCESSED_FULLTEXT')
    pkg3 = create_dataset(fulltext='ERROR_FULLTEXT')
    pkg4 = create_dataset(fulltext='_'*21)

    ids = get_pkg_ids(force_all=False, retry=False)
    seq_assert_in([pkg2], ids)
    seq_assert_not_in([pkg1, pkg3, pkg4], ids)

    ids = get_pkg_ids(force_all=False, retry=True)
    seq_assert_in([pkg2, pkg3], ids)
    seq_assert_not_in([pkg1, pkg4], ids)

    ids = get_pkg_ids(force_all=False, retry=True, max_size=20)
    seq_assert_in([pkg2, pkg3, pkg4], ids)
    seq_assert_not_in([pkg1], ids)

def test_get_pkg_ids_max_size():
    pkg1 = create_dataset(fulltext='_'*20)
    pkg2 = create_dataset(fulltext='_'*21)

    ids = get_pkg_ids(max_size=20)
    seq_assert_in([pkg2], ids)
    seq_assert_not_in([pkg1], ids)
    
