import pytest
import tempfile

from ckanext.fulltext.postprocess import resource_fulltext_process as ftprocess
from ckanext.fulltext.postprocess.resource_fulltext_process import hmbtg_config
from ckanext.hmbtgharvesters import fetch as hmbtg_fetch
from ckanext.fulltext.parser.tikaparser import parser as tika_parser


import ckan.tests.helpers as helpers
from ckan import model
import tempfile, os
import nose
from nose.tools import assert_in, assert_not_in
from mock import patch
from ckan.lib.search.index import PackageSearchIndex

from ckanext.fulltext.tests.test_tikaparser import DATA_PATH
from ckanext.fulltext.tests.server_mock import SERVER_URL
from .helpers import get_package_from_index, create_dataset 


def commit_index():
    PackageSearchIndex().commit()

def create_archive(files, contents, asZip=False):
    import patoolib
    path = tempfile.mkdtemp()
    files = [os.path.join(path, f) for f in files]
    for f, c in zip(files, contents):
        with open(f, 'wb') as f:
            f.write(c.encode("utf-8"))
    if asZip:
        p = os.path.join(path, 'archive.zip')
    else:
        p = os.path.join(path, 'archive.rar')
    patoolib.create_archive(p, files)
    return path, p


def create_file(dir, file, content):
    p = os.path.join(dir, file)
    with open(p, 'wb') as f:
        f.write(content.encode("utf-8"))
    return p


DATA_PATH = f'{os.getcwd()}/ckanext/fulltext/tests/data/'


class TestFulltext(object):

    def get_package(self, id, login=True):
            if login:
                context = {
                    'ignore_auth': False,
                    'user': self._get_sysadmin(),
                    'model': model
                }
            else:
                context = {'ignore_auth': False, 'model': model}
            return helpers.call_action('package_show', id=id, context=context)

    def _get_sysadmin(self):
        name = 'sysadmin'
        return name

    def _get_context(self):
        context = {
            'model': model,
            'session': model.Session,
            'ignore_auth': True
        }
        return context

    def _process(self, package_id, index=False, clean=False):
        context = self._get_context()
        ftprocess.process(context, index, clean, False, False, False,
                          package_id)


    def test_get_fulltext_withlogin(self):
        # Arrange
        pkg = create_dataset('fulltext')

        # Act
        pkgdb = self.get_package(pkg['id'])

        # Assert
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert resources[0]['fulltext'] == 'fulltext'

    def test_get_fulltext_nologin(self):
        # Arrange
        pkg = create_dataset('fulltext')

        # Act
        pkgdb = self.get_package(pkg['id'], False)

        # Assert
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert 'fulltext' not in resources[0]

    def test_fulltext_process_with_url(self, server):
        # Arange
        pkg = create_dataset(url=SERVER_URL)
        server.set_text('fulltext')

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert resources[0]['fulltext'].strip() == 'fulltext'


    def test_fulltext_process_with_url_and_index_and_clean(self, monkeypatch, server):
        # Arange
        def mockGet(key, d):
            if key == 'fulltext.clean.sources':
                return 'source'
            return d
        monkeypatch.setattr(ftprocess, "get_harvest_source", lambda **kwargs: 'source')
        monkeypatch.setattr(hmbtg_config, "get", mockGet)
        pkg = create_dataset(url=SERVER_URL+'.pdf')
        server.set_text('H a u s')

        # Act
        ftprocess.process_package_id(pkg['id'], True, True, False)

        # Assert
        pkg = get_package_from_index(pkg['id'])
        #assert len(ret) == 1
        # print ret
        # pkg = ret[0]
        resources = pkg['resources']
        assert len(resources) == 1
        assert resources[0]['fulltext'].strip() == 'H a u s'
        assert resources[0]['fulltext_clear'].strip() == '(Haus,{})'

    def test_fulltext_process_with_long_url(self, server):
        # Arange
        pkg = create_dataset(
            url=SERVER_URL +
            'https-geodienste-hamburg-de-hh_wfs_statistik_stadtteile_wohnungsdaten-service-wfs-version-1-1-0-request-getfeature-typename-app-wohnstatistik_wohnfl_31122014-app-wohnstatistik_wohngr_31122014-app-wohnstatistik_wohn_31122014-app-wohnstatistik_wohn_efh_zfh_prz_31122014'
        )
        server.set_text('fulltext')

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert resources[0]['fulltext'].strip() == 'fulltext'

    def test_fulltext_process_with_url_does_not_pollute_tmp(self, server):
        # Arange
        pkg = create_dataset(url=SERVER_URL)
        server.set_text('fulltext')
        count = len(os.listdir(tempfile.gettempdir()))

        # Act
        self._process(pkg['id'])

        # Assert
        nose.tools.assert_equal(count, len(os.listdir(tempfile.gettempdir())))


# def test_fulltext_process_with_redirect_url(self):
#     # Arange
#     pkg = create_dataset(url='http://www.buergerschaft-hh.de/parldok/tcl/PDDocView.tcl?mode=get&lp=20&doknum=5315')

#     # Act
#     self._process(pkg['id'])

#     # Assert
#     pkgdb = get_package(pkg['id'])
#     resources = pkgdb['resources']
#     print(resources[0]['fulltext'].strip())
#     assert len(resources) == 1
#     assert 'gml' not in resources[0]['fulltext']

    def test_fulltext_process_with_rar(self, server):
        # Arange
        path, archive = create_archive(['test.txt'], ['fulltext'])
        pkg = create_dataset(url=SERVER_URL+'.rar')
        server.set_file(archive)

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert 'fulltext' in resources[0]['fulltext']
        assert archive[:1] in resources[0]['fulltext']

    def test_fulltext_process_with_rar_does_not_pollute_tmp(self, server):
        # Arange
        path, archive = create_archive(['test.txt'], ['fulltext'], asZip=True)
        pkg = create_dataset(url=SERVER_URL)
        server.set_file(archive)
        count = len(os.listdir(tempfile.gettempdir()))

        # Act
        self._process(pkg['id'])

        # Assert
        nose.tools.assert_equal(count, len(os.listdir(tempfile.gettempdir())))

    def test_fulltext_process_with_zip(self, server):
        # Arange
        path, archive = create_archive(['test.txt'], ['fulltext'], asZip=True)
        pkg = create_dataset(url=SERVER_URL)
        server.set_file(archive)

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert 'fulltext' in resources[0]['fulltext']
        assert archive[:1] in resources[0]['fulltext']

    def test_fulltext_process_with_broken_zip(self, server):
        # Arange
        pkg = create_dataset(url=SERVER_URL + '.zip')
        server.set_text('not an archive')

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert 'ERROR_FULLTEXT' == resources[0]['fulltext']

    def test_fulltext_process_with_broken_rar(self, server):
        # Arange
        pkg = create_dataset(url=SERVER_URL + '.rar')
        server.set_text('not an archive')

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        assert 'ERROR_FULLTEXT' == resources[0]['fulltext']

    def test_fulltext_process_with_broken_url(self):
        import uuid
        # Arange
        pkg = create_dataset(url='http://' + str(uuid.uuid4()))

        # Act
        try:
            self._process(pkg['id'])
        except:
            pass

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        assert len(resources) == 1
        print(resources[0]['fulltext'])
        assert 'ERROR_FULLTEXT' == resources[0]['fulltext']

    def test_fulltext_process_with_large_zip(self, server):
        try:
            # Arange
            self.set_config_value("fulltext.file_maxsize", '0')
            pkg = create_dataset(url=SERVER_URL + '.zip')
            self.setup_server_with_archive(['test.txt'], ['fulltext'],
                                           asZip=True, server=server)

            # Act
            self._process(pkg['id'])

            # Assert
            self.assert_fulltext(pkg, 'NOT_AVAILABLE')
        finally:
            self.set_config_value("fulltext.file_maxsize", '100000')

    def test_fulltext_process_with_large_rar(self, server):
        try:
            # Arange
            self.set_config_value("fulltext.file_maxsize", '0')
            pkg = create_dataset(url=SERVER_URL + '.rar')
            self.setup_server_with_archive(['test.txt'], ['fulltext'],
                                           asZip=False, server=server)

            # Act
            self._process(pkg['id'])

            # Assert
            self.assert_fulltext(pkg, 'NOT_AVAILABLE')
        finally:
            self.set_config_value("fulltext.file_maxsize", '100000')


    #@pytest.mark.skip(reason="file missing")
    #def test_fulltext_process_with_large_rar_real_url(self, server):
    #    # Arange
    #    self.set_config_value("fulltext.file_maxsize", str(500 * 1024**2))
    #    server.set_file(DATA_PATH + "bohrarchiv_hh_2016-05-12_13263_snap_1.RAR")
    #    url = SERVER_URL + "bohrarchiv_hh_2016-05-12_13263_snap_1.RAR"
    #    pkg = create_dataset(url=url)
    #    self.setup_server_with_archive(['test.txt'], ['fulltext'], asZip=False, server=server)
#
#        # Act
#        self._process(pkg['id'])
#        pkg = create_dataset(url=SERVER_URL)
#        server.set_text('fulltext')
#        # Assert
#        self.assert_fulltext(pkg, 'NOT_AVAILABLE')

    def test_fulltext_allris_protocol(self, server):
        # Arange
        server.set_text("Test123")
        url = SERVER_URL + "/sitzungsdienst/test"
        pkg = create_dataset(url=url)
        pkg["title"] = "Sitzungsprotokoll (Druckversion) "
        self._process(pkg['id'])
        # Assert
        self.assert_fulltext(pkg, 'Test123')
    
    def test_fulltext_allris_document(self, server):
        # Arange
        server.set_text("Test123")
        url = SERVER_URL + "/sitzungsdienst/test"
        pkg = create_dataset(url=url)
        pkg["title"] = "Drucksache "
        self._process(pkg['id'])
        # Assert
        self.assert_fulltext(pkg, 'Test123')
    
    def test_fulltext_allris_none(self, server):
        # Arange
        server.set_text("Test123")
        url = SERVER_URL + "/sitzungsdienst/test"
        pkg = create_dataset(url=url)
        self._process(pkg['id'])
        # Assert
        self.assert_fulltext(pkg, 'Test123')
    
    def test_fulltext_process_with_rar_and_blacklist(self, server):
        # Arange
        self.set_config_value("fulltext.format_blacklist", 'gml')
        pkg = create_dataset(url=SERVER_URL + '.rar')
        __ , archive = self.setup_server_with_archive(['test.txt', 'test.gml'], ['fulltext', 'gml'], server=server)
        files_befor = os.listdir(tempfile.gettempdir())

        # Act
        self._process(pkg['id'])

        # Assert
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        files_after = os.listdir(tempfile.gettempdir())

        assert set(files_befor).symmetric_difference(set(files_after)) == set()
        assert len(files_befor) == len(files_after)

        assert len(resources) == 1
        assert 'fulltext' in resources[0]['fulltext']
        assert os.path.join(archive[:1], 'test.txt') in resources[0]['fulltext']
        assert os.path.join(archive[:1], 'test.gml') not in resources[0]['fulltext']
        assert 'gml' not in resources[0]['fulltext']

    def test_fulltext_process_local_file(self):
        # Arange
        path = tempfile.mkdtemp()
        file = os.path.join(path, 'test.txt')
        with open(file, 'w') as f:
            f.write('fulltext')
        pkg = create_dataset(url=file)

        # Act
        self._process(pkg['id'])

        # Assert
        self.assert_fulltext(pkg, 'fulltext')

    def test_process_package(self, server):
        pkg = create_dataset(url=SERVER_URL)
        server.set_text('fulltext')
        ftprocess.process_package_id(pkg['id'], False, False, False)
        self.assert_fulltext(pkg, 'fulltext')

    def test_process_package_retry(self, server):
        pkg = create_dataset(url=SERVER_URL, fulltext='ERROR_FULLTEXT')
        server.set_text('fulltext')
        ftprocess.process_package_id(pkg['id'], False, False, True)
        self.assert_fulltext(pkg, 'fulltext')

    def test_set_fulltext_for_package(self, server):
        from ckan.model import Session
        pkg = create_dataset(url=SERVER_URL)
        server.set_text('fulltext')
        session = Session()
        ftprocess._set_fulltext_for_package(pkg['id'], session, False, False)
        session.commit()
        self.assert_fulltext(pkg, 'fulltext')

    def test_set_fulltext_for_package_max_chars(self, server):
        from ckan.model import Session
        self.set_config_value("max_chars_fulltext", '10')
        pkg = create_dataset(url=SERVER_URL)
        server.set_text('_'*20)
        session = Session()
        ftprocess._set_fulltext_for_package(pkg['id'], session, False, False)
        session.commit()
        self.assert_fulltext(pkg, '_'*10)
        
    def test_reset_fulltext_for_package_max_chars(self, server):
        from ckan.model import Session
        self.set_config_value("max_chars_fulltext", '30')
        pkg = create_dataset(url=SERVER_URL)
        server.set_text('_'*20)
        session = Session()
        ftprocess._set_fulltext_for_package(pkg['id'], session, False, False)
        session.commit()
        self.assert_fulltext(pkg, '_'*20)

        self.set_config_value("max_chars_fulltext", '10')
        ftprocess._set_fulltext_for_package(pkg['id'], session, False, False)
        session.commit()
        self.assert_fulltext(pkg, '_'*10)

    @patch('ckanext.fulltext.postprocess.resource_fulltext_process.jobs.add')
    def test_only_process_unprocessed(self, mock):
        from ckan.model import Session
        pkg1 = create_dataset(url=SERVER_URL, fulltext='fulltext')
        pkg2 = create_dataset(url=SERVER_URL, fulltext='ERROR_FULLTEXT')
        pkg3 = create_dataset(url=SERVER_URL, fulltext='UNPROCESSED_FULLTEXT')

        context = self._get_context()
        ftprocess.process(context, False, False, use_jobs=True, force_all=False)

        assert_not_in(pkg1['id'], self._job_ids(mock))
        assert_not_in(pkg2['id'], self._job_ids(mock))
        assert_in(pkg3['id'], self._job_ids(mock))

    @patch('ckanext.fulltext.postprocess.resource_fulltext_process.jobs.add')
    def test_only_process_unprocessed_and_error(self, mock):
        mock.reset_mock()
        pkg1 = create_dataset(url=SERVER_URL, fulltext='fulltext')
        pkg2 = create_dataset(url=SERVER_URL, fulltext='ERROR_FULLTEXT')
        pkg3 = create_dataset(url=SERVER_URL, fulltext='UNPROCESSED_FULLTEXT')
        pkg4 = create_dataset(url=SERVER_URL, fulltext='Wrong parameter set')
        pkg5 = create_dataset(url=SERVER_URL, fulltext='   Wrong parameter set   ')

        context = self._get_context()
        ftprocess.process(context, False, False, use_jobs=True, force_all=False, retry=True)
        
        assert_not_in(pkg1['id'], self._job_ids(mock))
        assert_in(pkg2['id'], self._job_ids(mock))
        assert_in(pkg3['id'], self._job_ids(mock))
        assert_in(pkg4['id'], self._job_ids(mock))
        assert_in(pkg5['id'], self._job_ids(mock))

    def _job_ids(self, mock):
        return [c[0][1][0] for c in mock.call_args_list]

    def test_process_package_with_exception(self, monkeypatch):
        # Arrange
        def mock(a, b=None):
            raise Exception()

        monkeypatch.setattr(hmbtg_fetch, "to_file", mock)
        pkg = create_dataset(url=SERVER_URL)
        try:
            ftprocess.process_package_id(pkg['id'], False, False, False)
        except:
            pass
        self.assert_fulltext(pkg, 'ERROR_FULLTEXT')


    def test_process_package_with_tika_returns_none(self, monkeypatch):
        # Arrange
        def mock(a, b):
            return [None, None]
        def mockParser(a):
            return {'status':'500'}
        monkeypatch.setattr(hmbtg_fetch, "to_file", mock)
        monkeypatch.setattr(tika_parser, "from_file", mockParser)

        pkg = create_dataset(url=SERVER_URL)
        try:
            ftprocess.process_package_id(pkg['id'], False, False, False)
        except:
             pass
        self.assert_fulltext(pkg, 'ERROR_FULLTEXT')

    def assert_fulltext(self, pkg, fulltext):
        pkgdb = self.get_package(pkg['id'])
        resources = pkgdb['resources']
        nose.tools.assert_equal(len(resources), 1)
        nose.tools.assert_equal(resources[0]['fulltext'].strip(), fulltext)

    def setup_server_with_archive(self, files, contents, asZip=False, server=None):
        path, archive = create_archive(files, contents, asZip=asZip)
        pkg = create_dataset(url=SERVER_URL + '.zip')
        server.set_file(archive)
        return path, archive
    

    def set_config_value(self, key, value):
        hmbtg_config.setConfValue(key, value)

    
