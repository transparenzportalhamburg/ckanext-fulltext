#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import ckan.lib.navl.dictization_functions as df

from logging import getLogger
from pylons import config
from pylons.i18n import _
from genshi.input import HTML
from genshi.filters import Transformer
from itertools import count
from sqlalchemy.orm import class_mapper

import ckan.lib.helpers as h
from ckan.lib.search import SearchError
from ckan.lib.helpers import json
from ckan.lib.base import config

from ckan.logic import ValidationError

from ckan import model
from ckan.model.package import Package

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IPackageController
from ckan.plugins import IActions
import ckan.plugins.toolkit as toolkit

from ckan.lib.helpers import json
import ckan.logic.action.get as get
import ckan.logic.action.create as create
import ckan.logic.action.update as update

from ckan import logic
from ckan.logic import get_action, ValidationError

from ckan.model import Session

from ckanext.fulltext.model.setup_fulltext_table import PackageFulltext
from ckan.model.package_extra import PackageExtra

from ckanext.fulltext.fulltext_api import get_functions
from ckanext.fulltext.fulltext_api import _get_fulltext

log = getLogger(__name__)


class InforegFulltextSearch(SingletonPlugin):
    '''Base fulltext-plugin class.'''

    implements(IPackageController, inherit=True)
    implements(IActions)

    # for IPackageController
    def before_index(self, pkg_dict):
        '''Adds the fulltext of a package to the dict what 
        will be given to the solr for indexing.
        
        @param pkg_dict: flattened dict (except for multli-valued fields such as tags) 
                         containing all the terms which will be sent to the indexer
        @return: modified package dict
        '''
        
        if pkg_dict and pkg_dict.has_key('extras_full_text_search'):
            del pkg_dict['extras_full_text_search']
        
        data_dict = json.loads(pkg_dict['data_dict'])
        fulltext = [x for x in data_dict['extras'] if 'full_text_search' in x['key']]
        
        if len(fulltext) > 0:
            extras = [x for x in data_dict['extras'] if not 'full_text_search' in x['key']]
            data_dict['extras'] = extras
            pkg_dict['fulltext'] = fulltext[0]['value']

        else:
            fulltext_dict = _get_fulltext(pkg_dict['id'])
            if fulltext_dict:
                pkg_dict['fulltext'] = fulltext_dict.text
        
        pkg_dict['data_dict'] = json.dumps(data_dict)

        return pkg_dict


    # for IActions
    def get_actions(self):
        '''Returns a dict containing the keys being the name of the logic 
        function and the values being the functions themselves.
        
        @return: dict containing the logic functions
        '''
        action_functions = get_functions()
        return action_functions
    
     

