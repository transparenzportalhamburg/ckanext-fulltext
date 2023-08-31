import os
import logging

#import ckanext.fulltext.hmbtg_config as hmbtg_config #TODO: TO CHANGE 
from hmbtg_utils.environment import load_hmbtg_ini
from ckanext.fulltext.parser.tikatools import Tikatools

logger = logging.getLogger('repair_fulltext_logger')


def hmbtg_config():
    return load_hmbtg_ini().get("hmbtg_config", {})

class Hmbtg_Utils():
    tik = Tikatools()

    def _get_fulltext_from_tika(self, url, docname, id, saveTmp, jsredirect, remove_special_characters, httpsProxy, filesize):
        # Pro Ressource in hmbtg.ini
        config = hmbtg_config()
        max_fulltext_chars = int(config.get('max_chars_fulltext'))
        url=self.tik.normalizeURL(url)        
        proxy=self.check_proxy(httpsProxy)
        if proxy:
            proxyHost=proxy[0]
            proxyPort=proxy[1]
        else:
            proxyHost, proxyPort = "",""

        no_proxy = self.get_no_proxy()

        fulltext = str(self.tik.get_text_content(url,docname,id,saveTmp=saveTmp,proxyHost=proxyHost,proxyPort=proxyPort,no_proxy=no_proxy, jsredirect=jsredirect,remove_special_characters=remove_special_characters,httpsProxy=httpsProxy,filesize=filesize))
        if max_fulltext_chars > 0 and len(fulltext) > max_fulltext_chars:
            fulltext = fulltext[:max_fulltext_chars]
        if isinstance(fulltext, str):
            return fulltext
        else:
            return [(x.encode("utf-8", 'replace')) for x in fulltext]

    def handleURLandFulltext(self,url, docname, id, saveTmp=False, jsredirect=False, remove_special_characters=True, httpsProxy=False, filesize=None, number_of_resources=1, force_get=False):
        '''
        Returns the text content of a file or URL as a unicodestring.

        @docname: title/name to identfy the document 

        @id: id to identify the object    

        @ url: url or local filepath of the object whose fulltext should be fetched.    

        @ saveTmp: If saveTmp is set the function saves the fulltext in dir: /home/ckanuser/Self.Tik./Tmp. Default is False.

        @ jsredirect: If a JavaScript redirect is expected set param jsredirect=True. Please dont set param if no redirect is expected due to performance issues. Default is False.

        '''
        config = hmbtg_config()
        format_blacklist = config.get('fulltext.format_blacklist').split()
        for format in format_blacklist:
            if url.lower().endswith(format):
                return ''

        package_blacklist = config.get('fulltext.packageid_blacklist').split()
        if id in package_blacklist:
            return ''

        return self._get_fulltext_from_tika(url, docname, id, saveTmp, jsredirect, remove_special_characters, httpsProxy, filesize)

    def check_proxy(self,httpsProxy):
        '''
        Methods checks and returns the pair of  http/s proxy ip and port if set in the enviorenment. Else returs an empty-String
        '''

        varsdict=os.environ
        keys=list(varsdict.keys())
        if not(httpsProxy) and "http_proxy" in keys:
            if "/" in varsdict['http_proxy']: 
                # expecting smth like: http://193.101.67.2:3128
                tmpdict = varsdict['http_proxy'].split("://")
                return tmpdict[1].split(":")
            else: 
                return varsdict['http_proxy'].split(":")
        if "https_proxy" in keys:
            if "/" in varsdict['https_proxy']: 
                # expecting smth like: https://193.101.67.2:3128
                tmpdict = varsdict['https_proxy'].split("://")
                return tmpdict[1].split(":")
            else: 
                return varsdict['https_proxy'].split(":")
        return ""

    def get_no_proxy(self):
        '''
        Returns the no_proxy environment settings. 
        If not found it returns the empty-String.
        '''

        environ_var_dict=os.environ
        return environ_var_dict.get('no_proxy',"") 
