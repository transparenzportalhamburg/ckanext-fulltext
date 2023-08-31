from ckanext.fulltext.parser import archiver
import os
import nose
import glob
import tempfile
import patoolib

def create_file(dir, file, content):
    p = os.path.join(dir, file)
    with open(p, 'w') as f:
        f.write(content)
    return p

def create_nested_archive():
    path1, __ = create(['test.txt', 'test.gml'], ['test.txt', 'test.gml'])
    create_file(path1, 'test2.txt', 'test2.txt')

    patoolib.create_archive(os.path.join(path1, 'archive2.zip'), glob.glob(os.path.join(path1, '*')))
    r = os.path.join(path1, 'archive3.rar')
    patoolib.create_archive(r, glob.glob(os.path.join(path1, '*')))
    return path1, r

def create(files, contents, asZip=False):
    path = tempfile.mkdtemp()
    pfiles = [path + '/' + f for f in files]
    for f, c in zip(pfiles, contents):
        with open(f, 'w') as f:
            f.write(c)
    if asZip:
        p = os.path.join(path, 'archive.zip')
    else:
        p = os.path.join(path, 'archive.rar')
    os.chdir(path)
    patoolib.create_archive(p, files)
    return path, p


def test_list_files_with_rar():
    # Arrange
    path, archive = create(['test.txt'], ['fulltext'])
    # Act
    ret = archiver.list_files(archive)
    # Assert 
    nose.tools.assert_equal(ret, ['test.txt'])

def test_list_files_with_zip():
    # Arrange
    path, archive = create(['test.txt'], ['fulltext'], asZip=True)
    print(archive)
    # Act
    ret = archiver.list_files(archive)
    # Assert 
    nose.tools.assert_equal(ret, ['test.txt'])

def test_extract_file_from_rar():
    # Arrange
    tmp = tempfile.mkdtemp()
    path, archive = create(['test.txt'], ['fulltext'], asZip=True)
    count = len(os.listdir('/tmp'))
    # Act
    ret = archiver.extract_file('test.txt', archive, tmp)
    # Assert 
    e = os.path.split(glob.glob(os.path.join(tmp,'*'))[0])[1]
    nose.tools.assert_equal(e, 'test.txt')
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))

def test_extract_file_from_zip():
    # Arrange
    tmp = tempfile.mkdtemp()
    path, archive = create(['test.txt'], ['fulltext'])
    # Act
    ret = archiver.extract_file('test.txt', archive, tmp)
    # Assert 
    e = os.path.split(glob.glob(os.path.join(tmp,'*'))[0])[1]
    nose.tools.assert_equal(e, 'test.txt')

def test_process_archive_from_rar():
    # Arrange
    tmp = tempfile.mkdtemp()
    path, archive = create(['test.txt'], ['fulltext'])
    ret = []
    txt = []
    def clb(p):
        assert os.path.exists(p)
        with open(p, 'r') as f:
            txt.append(f.read())
        ret.append(p)
    # Act
    archiver.process_archive(archive, clb, [])
    # Assert 
    # e = os.path.split(glob.glob(os.path.join(tmp,'*'))[0])[1]
    nose.tools.assert_equal(len(ret), 1)
    nose.tools.assert_true(ret[0].endswith('test.txt'))
    nose.tools.assert_equal(len(txt), 1)
    nose.tools.assert_equal(txt[0], 'fulltext')

def test_process_nested_archive():
    # Arrange
    tmp = tempfile.mkdtemp()
    path, archive = create_nested_archive()
    ret = []
    txt = []
    def clb(p):
        assert os.path.exists(p)
        with open(p, 'r') as f:
            txt.append(f.read())
        ret.append(p)
    count = len(os.listdir('/tmp'))
    # Act
    archiver.process_archive(archive, clb, [])
    # Assert 
    nose.tools.assert_equal(len(ret), 10)
    nose.tools.assert_equal(sorted(txt), sorted(['test.txt', 'test2.txt', 'test.gml', 'test.txt', 'test.gml', 'test.txt', 'test2.txt', 'test.gml', 'test.txt', 'test.gml']))
    for r in ret:
        assert not os.path.exists(r)
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))

def test_process_nested_archive_with_blacklist():
    # Arrange
    tmp = tempfile.mkdtemp()
    path, archive = create_nested_archive()
    ret = []
    txt = []
    def clb(p):
        assert os.path.exists(p)
        with open(p, 'r') as f:
            txt.append(f.read())
        ret.append(p)
    # Act
    archiver.process_archive(archive, clb, ['gml'])
    # Assert 
    nose.tools.assert_equal(len(ret), 6)
    nose.tools.assert_equal(sorted(txt), sorted(['test.txt', 'test2.txt', 'test.txt', 'test.txt', 'test2.txt', 'test.txt']))
    for r in ret:
        assert not os.path.exists(r)

def test_process_nested_archive_with_blacklist_and_exception():
    from zipfile import BadZipfile
    # Arrange
    path, archive = create_nested_archive()
    def clb(p):
        raise BadZipfile()
    count = len(os.listdir('/tmp'))
    # Act
    try:
        archiver.process_archive(archive, clb, ['gml'])
    except:
        pass
    # Assert 
    nose.tools.assert_equal(count, len(os.listdir('/tmp')))

def test_process_real_archive():
    archive = '/tmp/bohrarchiv_hh_2018-09-19_26469_snap_1.RAR'
    if os.path.exists(archive):
        def clb(p):
            assert os.path.exists(p)
            print(p)
        archiver.process_archive(archive, clb, ['gml'])
