import os
import uuid
import errno
import shutil
import logging
import tempfile

from tika import parser
from hmbtg_utils.net.url import URL

'''
TODO:
install script mit setup.py ... Warum auch immer.
'''

class ResourceNotFound(Exception):
    pass

class UnprocessableEntity(Exception):
    pass

logger = logging.getLogger('repair_fulltext_logger')

def is404(fulltext):
    return fulltext != None and ("404 - File or directory not found" in fulltext or "404 Not Found   Not Found" in fulltext or "NOT_AVAILABLE" in fulltext or "The page cannot be displayed because" in fulltext or 'The requested URL could not be retrieved' in fulltext)

def encode(msg):
    if (isinstance(msg, str)):
        return msg
    else:
        return str(msg, errors='ignore')

def clean_input(url):
    url = encode(url)

    if url.startswith("/"):
        url = f"file://{url}"
    
    return url   



def parse_with_tika(locator, proxy_host=None, proxy_port=None):
    if not locator:
        raise ValueError("Cant parse fulltext.No locator for File given.")

    loc = clean_input(locator)
    url = URL(loc)
    # handle file fetch to prevent 'filename too long' exceptions
    # use tmpdir to ensure all files were deleted after processing
    try:
        tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(tmpdir, str(uuid.uuid4()))
        try:
            logger.info('fetching %s' % loc)
            filename, _ = url.to_file(tmp)
        except IOError:
            raise ResourceNotFound(loc)
        #TODO: URL EXCEPTION HANDELING
        if os.path.getsize(filename) == 0:
            return None

        parsed = parser.from_file(filename)
        if parsed['status'] != 200:
            raise UnprocessableEntity(loc)

        if is404(parsed['content']):
            raise ResourceNotFound(loc)

        # logger.info(u'done parsing with tika')
        if 'content' in parsed and parsed['content']:
            return parsed["content"].strip()
        return None
    finally:
        try:
            shutil.rmtree(tmpdir)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise