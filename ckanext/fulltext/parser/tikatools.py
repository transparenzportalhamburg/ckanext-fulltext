import re
import os
import urllib.request
import urllib.error
import urllib.parse
import codecs

from ckanext.fulltext.files import create_temp_file_path 
import posixpath as po
try:
    import requests
except ImportError:
    print("Cant find requests module")
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Cant find bs4 module")

import ckanext.fulltext.hmbtg_config as hmbtg_config 
from .tikaparser import parse_with_tika
from . import archiver
from ckanext.fulltext.parser.tikaparser import UnprocessableEntity
from hmbtg_utils.net.url import URL
import logging

tika = '/home/ckanuser/Tika/tika-app-1.4.jar'
tmpdir = "/home/ckanuser/Tika/Tmp"

logger = logging.getLogger('repair_fulltext_logger')


class Tikatools():

    # Don'text read just get the file handle and check content-length
    def get_file_size(self, filepath, jsredirect=False):
        '''
        Determines the filesize given filepath/url in Byte as an Integer. If filesize cant be determinded the function returns 0. Check logs in this case for further information. If a JavaScript is expected        set param jsredirect.  
        '''
        logger.debug(f"Try get filesize for {filepath}")
        if filepath.strip() == "":
            logger.debug(f"No Url given. Cant determine filesize of {filepath}.")
            return 0
        filepath = self.normalizeURL(filepath)
        if filepath.strip() == "":
            logger.debug(f"No Url given. Cant determine filesize of normalized filepath {filepath}.")
            return 0
        if jsredirect:
            try:
                filepath = self.handle_JS_redirect(filepath)
            except requests.exceptions.HTTPError as e:
                logger.error(f"could not process jsredirect: {e}")
                return 'ERROR_FULLTEXT'

        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            logger.debug(f"Size {size} for {filepath}")
            return size

        else:
            try:
                d = urllib.request.urlopen(filepath)
                size = d.headers.get('Content-Length')

                if not size:
                    # if no Header is recieved.
                    logger.debug(f"Cant get Filesize of {filepath}. No header 'Content-length' recieved. Continuing with reading file content.")
                    size = self.filesizeWithProxy(filepath)
                logger.debug(f"Tikatool: Size {size} for {filepath}")

                # the header is a string and must be converted
                return int(size)

            except Exception as e:
                # Problems opening the given url
                size = self.filesizeWithProxy(filepath)

                if size:
                    logger.debug("Tikatool: Size %s for %s" % (size, filepath))

                return size

    def filesizeWithProxy(self, filepath):
        try:
            https_proxy = os.environ['https_proxy']
            http_proxy = os.environ['http_proxy']
            logger.debug("Tikatool, proxies: http = %s and https = %s" %
                         (http_proxy, https_proxy))
            if https_proxy is not None and http_proxy is not None:
                proxies = {'http': http_proxy, 'https': https_proxy}
                logger.debug("Tikatool, requests with proxies: http = %s and https = %s" % (
                    http_proxy, https_proxy))
                size = len(requests.get(filepath, proxies=proxies).content)
            else:
                size = self.requestFilesizeWithoutProxy(filepath)
            return size

        except Exception as e:
            size = self.requestFilesizeWithoutProxy(filepath)

            if not size:
                logger.debug(
                    f"Cant determine filesize of {filepath}. Reason {e}")
                return 0
            else:
                return size

    def requestFilesizeWithoutProxy(self, filepath):
        try:

            logger.debug("Tikatool, requests without proxies:")
            size = len(requests.get(filepath).content)

            if not size:
                size = self.filesizeWithUnquote(filepath)

            logger.debug("Tikatool: Size %s for %s" % (size, filepath))
            return size

        except Exception as e:
            size = self.filesizeWithUnquote(filepath)
            if not size:
                logger.debug(
                    f"Cant determine filesize of {filepath} without Proxy. Reason {e}")
                return 0
            else:
                return size

    def filesizeWithUnquote(self, filepath):
        try:
            logger.debug("Try filesize with Unquote")
            filepath = urllib.parse.unquote(filepath)
            d = urllib.request.urlopen(filepath)
            size = d.headers.get('Content-Length')
            logger.debug("second try: filepath %s, Size %s" % (filepath, size))
            return int(size)  # the header is a string and must be converted
        except Exception as e:
            logger.debug(f"Got no filesize {filepath}")
            logger.debug(
                f"Cant get Filesize of {filepath} with Unquote. Failed with Exception:  {e} ")
            return 0

    def is_large_file(self, filepath, jsredirect=False, filesize=None):
        maxSize = int(hmbtg_config.getConfValue(
            "fulltext.file_maxsize", 5*1024**2))

        try:
            if not filesize:
                filesize = self.get_file_size(filepath, jsredirect=jsredirect)
            return int(filesize) > maxSize
        except:
            return False

    def is_archive(self, filepath):
        return ".zip" in filepath.lower() or ".rar" in filepath.lower()

    def extract_fulltext_from_archive(self, archive, fulltext_call, format_blacklist=[]):
        fulltext = ['']  # use array to prevent UnboundLocalError
        texts = []
        if archive.startswith("/"):
            archive = f"file://{archive}"
        url = URL(archive)

        def clb(p):
            try:
                text = fulltext_call(p)
                if text is not None and (type(text) is str or type(text) is str) and len(text) > 0:
                    fulltext[0] += p + '\n'
                    texts.append(text)
            except UnprocessableEntity as e:
                logger.error(f"file unprocessable: {e}")
        logger.info('Retrieving ' + archive)
        try:
            target, path = create_temp_file_path(archive)
            filename, _ = url.to_file(archive, target)

            archiver.process_archive(filename, clb, format_blacklist)
            fulltext[0] += '\n'.join(texts)
            return fulltext[0]
        except archiver.BadArchive:
            return 'ERROR_FULLTEXT'
        finally:
            try:
                urllib.request.urlcleanup()
                os.remove(target)
                os.rmdir(path)
            except Exception as e:
                logger.error("failed to delete tmp file")

    def get_text_content_for_filepath(self, filepath, doctitle, docID, saveTmp, proxyHost, proxyPort, no_proxy, jsredirect, remove_special_characters, httpsProxy):
        #    kg JavaScriptRedirect
        logger.debug(f"get_text_content_for_filepath: filepath->{filepath}")
        if jsredirect:
            try:
                filepath = self.handle_JS_redirect(filepath)
            except requests.exceptions.HTTPError as e:
                logger.error(f"could not process jsredirect: {e}")
                return 'ERROR_FULLTEXT'
            except Exception as e:
                logger.error(
                    f"Error while handling Javascript Redirect {filepath}, {doctitle}, {docID}")
                raise

        text = parse_with_tika(filepath)

        if text is None:
            return ''

        if saveTmp:
            tmp_file = tmpdir+"/" + self.getFilename(filepath) + "_tmp"

            with codecs.open(tmp_file, 'w', encoding='utf8') as f:
                f.write(text)

        return self.beautifulFulltext(text, filepath, remove_special_characters, is_csv=filepath.endswith(".csv"))

    def get_text_content(self, filepath, doctitle, docID, saveTmp=False, proxyHost="", proxyPort="80", no_proxy="", jsredirect=False, remove_special_characters=True, httpsProxy=True, filesize=None):
        '''Returns the text content of a file or URL as a unicodestring or as a list of unicodestrings
        Also saves a tmp-File with the text-Content in /home/ckanuser/Tika/Tmp. You can also get the Content via a http proxy (e.g. proxyHost="www.example.com" proxyPort="5000").Default proxyPort is 80. If         Tika throws an Error it will be logged in tikaerror.log
         '''
        if filepath.strip() == "":
            logger.error("No URL given %s, %s, %s" %
                         (filepath, doctitle, docID))
            return ""

        if self.is_large_file(filepath, jsredirect=jsredirect, filesize=filesize):
            logger.debug("File too large %s" % filepath)
            return ""

        if self.is_archive(filepath):
            blacklist = hmbtg_config.getConfValue(
                "fulltext.format_blacklist", "").split()
            if blacklist:
                def clb(path): return self.get_text_content_for_filepath(
                    path, doctitle, docID, False, '', '', '', '', remove_special_characters, '')
                return self.extract_fulltext_from_archive(filepath, clb, blacklist)

        return self.get_text_content_for_filepath(filepath, doctitle, docID, saveTmp, proxyHost, proxyPort, no_proxy, jsredirect, remove_special_characters, httpsProxy)

    def getFulltextType(self):
        try:
            res = hmbtg_config.getConfValue("fulltexttype")
            return res
        except Exception as e:
            return "str"

    @staticmethod
    def getFilename(filepath):
        '''
        Returns the filename without extension as a string given a filepath or tmpfilename for a url
        '''
        filepath = r""+filepath
        is_url = filepath.startswith("htt")
        if is_url:
            ausgabe = re.sub("[/:]", "", filepath).replace(".", "_")

        else:
            ausgabe = filepath.split(
                os.sep)[-1].split(os.path.extsep)[0].strip()
        return ausgabe

    def removeSpecialChars(self, text, is_csv):
        ''' Removes Digits and some special chars. 
        '''
        if is_csv:
            text = re.sub(";", " ", text)

        text = re.sub('[!(),;?:]', "", text)

        text = re.sub('[\n\t\xe2\x80\xa2\xef\xbf\xbd]', " ", text)

        return text

    def beautifulFulltext(self, fulltext, filepath, remove_special_characters, is_csv=False):
        if self.getFulltextType() == "list":
            newText = []
            count = 0
            for text in fulltext:
                count = count + 1
                newText.append(self.beautiful(
                    text, filepath, remove_special_characters, is_csv))
            return newText

        else:
            newText = self.beautiful(
                fulltext, filepath, remove_special_characters, is_csv)
            return newText

    def beautiful(self, text, filepath, remove_special_characters, is_csv):
        ''' Uses Methods to manipulate the String text for Fulltext-search
        '''

        text = text.replace('\ufffd', '')  # Ignoriere nicht Unicode-Chars
        text = text.replace("-\n", "")  # Trennstriche beseitigen
        if remove_special_characters:
            text = self.removeSpecialChars(text, is_csv)  # Sonderzeichen

        return text

    # kg Javascript-Redirect. Hier koennte man noch testen, ob die Seite zu groß ist, um ein redirect zu sein, falls fälschlicherweise ein redirect gesetzt wurde.
    def handle_JS_redirect(self, url):
        ''' Returns a new url, if the given url gets redirected with JavaScript. If there is no JavaScript redirect found it returns the initial url. Might raise an HTTP-Error if problems concerning Opening        the webpage occur.
        '''
        # rege=re.compile("window.location.replace(.*?);")
        # textFromReg=requests.get(url).text
        # patternresult=re.search(rege,textFromReg).group()

        request = requests.get(url)
        if not request.status_code == 200:
            raise requests.exceptions.HTTPError(request.status_code)
        soup = BeautifulSoup(request.text)
        if soup.script and soup.script.string:
            jscode = soup.script.string
        else:
            return url  # Seite hat keine JS-Code
        redirectCommandPosition = jscode.find("window.location.")
        if not redirectCommandPosition == -1:  # Nur wenn Redirect existiert.
            jscode = jscode[redirectCommandPosition:]
            argument = jscode[jscode.find("(") + 1: jscode.find(")")].strip("'").encode()
            # kg Hier nun Fallunterscheidung!
            # kg Ganz neue URL mit absolten Pfad
            if argument.startswith("http"):
                return argument
            # kg Redirect über relativen Pfad
            if argument.startswith("."):
                newurl = self.getNewUrl(argument, url)
                return newurl
        return url

    def getNewUrl(self, relativepath, url):
        parsedUrl = urllib.parse.urlsplit(url)
        urlpath = parsedUrl.path
        append = "/" + relativepath.strip("./")
        if not relativepath.startswith(".."):
            begin = self.getNParent(urlpath, 0)
            newpath = begin + append
        if relativepath.startswith(".."):
            times = relativepath.count("../")
            begin = self.getNParent(urlpath, times)
            newpath = begin + append
        newurl = urllib.parse.urlunsplit((parsedUrl.scheme, parsedUrl.netloc, newpath, "", ""))
        return newurl

    def getNParent(self, path, n):
        if n < 0:
            return path
        else:
            return self.getNParent(po.split(path)[0], n-1)

    def normalizeURL(self, url):
        # ZS Urls mit Akte koennen nicht verarbeitet werden, daher Patch
        # http://10.61.49.38/Dataport.HmbTG.ZS.Webservice.GetRessource100/GetRessource100.svc/dddb2aa6-147d-47e7-8748-c89604cb2039/Akte:AFB2a.835.52-20/0008.pdf
        if url.startswith('/'):
            return url
        if url.find("/Akte") > 0:
            url = self.niceFilename(url)
        #logger.debug("Tikatools normalizeURL before urlparse %s"% url)
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        upath = urllib.parse.urlparse(url).path
        if isinstance(path, str):
            upath = upath.encode('utf-8')
        urlpath = urllib.parse.quote(upath)
        # es koennte ein %20 im path vorkommen, dies wird zu %2520
        # mit folgendem wieder zu %20!
        urlpath = urlpath.replace('%25', '%')
        res = (parsed[0], parsed[1], urlpath, parsed[3], parsed[4])
        newURL = parsed[0] + "://" + parsed[1] + urlpath
        if len(parsed[3]) > 0:
            newULR = newURL + "?" + parsed[3] + parsed[4]
            return newURL
        if len(parsed[4]) > 0:
            newURL = newURL + "?" + parsed[4]
        # return urlparse.urlunsplit(res) liefert "#" statt "?"
        return newURL

    # Aktuell liefert der ZS eine nicht korrekte URL. Es gibt ":" und "/"
    # der Filename zum Ende der URL wird laut Soeren nicht beachtet
    # ersetze ":" durch nichts und letztes "/" durch nichts
    # url='http://10.61.49.38/Dataport.HmbTG.ZS.Webservice.GetRessource100/GetRessource100.svc/dddb2aa6-147d-47e7-8748-c89604cb2039/Akte:FB2a.835.52-20/0008.pdf'
    # oder mit "%3A" statt ":"
    def niceFilename(self, url):
        logger.debug("Tikatools nicefilename entering %s" % url)
        if url.find("///") > 0:
            url = url.replace('///', '//')
        beforeSlashes = url[:url.find("//")+2]
        # http://

        urlwithoutpath = url[url.find("//")+2:]
        # 10.61.49.38/Dataport.HmbTG.ZS.Webservice.GetRessource100/GetRessource100.svc/dddb2aa6-147d-47e7-8748-c89604cb2039/Akte:FB2a.835.52-20/0008.pdf'

        beforeColon = urlwithoutpath[:urlwithoutpath.find('/Akte')+1]
        # 10.61.49.38/Dataport.HmbTG.ZS.Webservice.GetRessource100/GetRessource100.svc/dddb2aa6-147d-47e7-8748-c89604cb2039/Akte

        restFilename = urlwithoutpath[urlwithoutpath.find('/Akte')+1:].replace("/", "").replace("%", "").replace(":", "")
        # 'Akte3AFB2a.835.52-200008.pdf'

        result = beforeSlashes + beforeColon + restFilename
        logger.debug("Tikatools nicefilename %s" % result)
        return result
