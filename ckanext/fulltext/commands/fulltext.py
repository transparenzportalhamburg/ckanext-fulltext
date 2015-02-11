#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
from pprint import pprint
import logging

from ckan.lib.cli import CkanCommand
from ckanext.fulltext.model.setup_fulltext_table import setup

log = logging.getLogger(__name__)


class Fulltext(CkanCommand):
    '''Performs fulltext-related operations.

    Usage:
        fulltext init_fulltext_table 
            Creates the necessary fulltext table. 
      
    The commands should be run from the ckanext-fulltext directory and expect
    a development.ini file to be present. 

    '''
    
    summary = __doc__.split('\n')[0]

    def command(self):
        self._load_config()
        print ''

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        if cmd == 'init_fulltext_table':
            self.init_fulltext_table()     
        else:
            print 'Command %s not recognized' % cmd
            

    def init_fulltext_table(self):
        setup()


