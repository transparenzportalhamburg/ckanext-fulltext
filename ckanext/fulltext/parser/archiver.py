from typing import Union, List

import os
import errno
import shutil
import tempfile
import logging
from xmlrpc.client import boolean


from zipfile import BadZipfile
from zipfile import ZipFile
from rarfile import BadRarFile, NotRarFile
from rarfile import RarFile


logger = logging.getLogger(__name__)


class BadArchive(Exception):
    pass


def is_rar(filename: str) -> boolean:
    return filename.lower().endswith('rar')


def is_zip(filename: str) -> boolean:
    return filename.lower().endswith('zip')


def is_archive(filename: str) -> boolean:
    return is_rar(filename) or is_zip(filename)


def archive_of(filename: str) -> Union[RarFile, ZipFile] :
    if is_rar(filename):
        return RarFile(filename)
    if is_zip(filename):
        return ZipFile(filename)
    raise ValueError(f'unsupported archive: {filename}')


def list_files(filename: str) -> List[str]:
    f = archive_of(filename)
    files = (x.filename for x in f.infolist())
    return [r for r in files if not r.endswith('/')]


def extract_file(filename: str, archive: str, destination: str) -> None:
    f = archive_of(archive)
    for r in f.infolist():
        if r.filename == filename:
            f.extract(r, destination)
            return
    raise ValueError(f'could not find filename {filename} in archive {archive}')


def process_archive(archive: str, process_call, format_blacklist=[]) -> None:
    try:
        tmp = tempfile.mkdtemp()
        stack = [archive]

        while stack:
            archive = stack.pop(0)
            logger.debug(f"archive: {archive} \n stack: {stack}")
            for file in list_files(archive):
                if is_archive(file):
                    extract_file(file, archive, tmp)
                    stack.append(os.path.join(tmp, file))
                else:
                    process = True
                    for fmt in format_blacklist:
                        if file.lower().endswith(fmt):
                            process = False
                            break
                    if process:
                        extract_file(file, archive, tmp)
                        p = os.path.join(tmp, file)
                        if not os.path.isdir(p):
                            process_call(p)
    except (BadZipfile, BadRarFile, NotRarFile) as e:
        raise BadArchive(archive)
    except Exception as e:
        logger.error(f"Error while processing archive ({archive}): {e}")
        raise
    finally:
        try:
            shutil.rmtree(tmp)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise
