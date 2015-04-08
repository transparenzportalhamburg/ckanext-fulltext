# -*- coding: utf-8 -*-
import tika
import re
from singleton import Singleton
import logging
logging.basicConfig() 
log = logging.getLogger(__name__)

'''
The Tika_Wrapper_Singleton class can parse documents via http or local files.
Its a Singleton because this prevents running several JVM's.
'''

class Tika_Wrapper_Singleton(object):
    __metaclass__ = Singleton

    def __init__(self,proxy_host="", proxy_port="", httpsProxy="", no_proxy=""):
        self.proxy_host=proxy_host
        self.proxy_port=proxy_port
        # MaxHeap Argument für die JVM. Syntax like -Xmx java command line argument
        self.jvm_max_heap = '1g'
        self.vm=self.startVM(proxy_host,proxy_port,httpsProxy,no_proxy)

    def startVM(self,proxy_host,proxy_port,httpsProxy,no_proxy):
        args=self.__create_vm_args(proxy_host,proxy_port, httpsProxy,no_proxy)
        log.debug("Args for JVM: {}. Maxheap: {}".format(args,self.jvm_max_heap))
        vm=tika.initVM(maxheap=self.jvm_max_heap, vmargs=args)
        return vm

        
    def __create_vm_args(self,proxyHost,proxyPort,httpsProxy,no_proxy):
        '''
        Returns a string of java vm arguments. These can be passed to initVM function.
        '''
        vm_args=[]

        if not(httpsProxy) and proxyHost and proxyPort:
            vm_args.append("-Dhttp.proxyHost="+proxyHost)
            vm_args.append("-Dhttp.proxyPort="+proxyPort)
        if httpsProxy and proxyHost and proxyPort:
            vm_args.append("-Dhttps.proxyHost="+proxyHost)
            vm_args.append("-Dhttps.proxyPort="+proxyPort)
        if no_proxy:
            vm_args.append(self.__create_no_proxy_vm_arg(no_proxy))
        
        arg_string=",".join(vm_args)
        print arg_string
        return arg_string

    def __create_no_proxy_vm_arg(self,no_proxy):
        '''
        Returns a string, which can be passed to a JVM for no_proxy setting.
        '''
        #Sollte so aussehen: -Dhttp.nonProxyHosts=”localhost|host.example.com” 
        replaced_with_pipe=no_proxy.replace(",","|")
        replaced_with_pipe=replaced_with_pipe.replace(" ","")
        return "-Dhttp.nonProxyHosts="+replaced_with_pipe
        
    def parse_with_tika(self,locator,proxy_host=None,proxy_port=None):
        '''
        Parse locator (http or absolute file_path) using tika with AutodetectParser. Returns a String.
        '''
        if not locator:
            raise ValueError("Cant parse fulltext.No locator for File given.")
        
        config = self._create_tika_conig() 
            
        if not locator.startswith("http"): #Very sophisticated way to distinguish URLS and filepaths :)
            return self._from_file(locator, config)
                
        else:
            return self._from_url(locator, proxy_host,proxy_port, config)
        

    def _create_tika_conig(self):
        '''
        Method which creates a dictionary which contains Objects for Tika Configuration.
        Returns:
             {
               'BodyContentHandler' : tika.BodyContentHandler
              }
        '''
        config ={
                'BodyContentHandler' : tika.BodyContentHandler(-1) # No MaxChar restriction
        }
        return config
        

    def _from_file(self,filename, config = None):
        """Parse filename using tika's AutoDetectParser."""
        stream = tika.FileInputStream(tika.File(filename))
        return self.__parse(stream,config)

    def _from_url(self,string,proxy_host,proxy_port, config = None):
        '''
        Parse from URL.
        '''
        url = tika.URL(string)
        stream = url.openStream()
        return self.__parse(stream,config)

       # if proxy_host and proxy_port:
           # proxy= tika.Proxy(aaah!,tika.InetSocketAddress(proxy_host,int(proxy_port)))

    def __parse(self,stream, config):
        parsed = {}
        parser = tika.AutoDetectParser()
        content = config.get('BodyContentHandler',tika.BodyContentHandler())
        metadata = tika.Metadata()
        context = tika.ParseContext()
        parser.parse(stream, content, metadata, context)
        parsed["content"] = content.toString()
        parsed["metadata"] = {}
        for n in metadata.names():
            parsed["metadata"][n] = metadata.get(n)
        return parsed['content']
