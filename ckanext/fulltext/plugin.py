#! /usr/bin/env python
# -*- coding: utf-8 -*-


from logging import getLogger

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IPackageController
from ckan.plugins import IActions

from ckan.lib.helpers import json
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
        if ('type' in pkg_dict and pkg_dict['type'] == 'harvest'):
            # not for datasets that are harvesters                                                                                                                                     
            return pkg_dict

        try:
            package_id = pkg_dict['id']
            data_dict = json.loads(pkg_dict['data_dict'])
            if 'resources' in data_dict:
                fulltext = _get_fulltext(package_id, data_dict['resources'])

                if fulltext is not None:
                    pkg_dict['res_fulltext'] = [ft['text'] for ft in fulltext]
                    pkg_dict['res_fulltext_clear'] = [ft.get('text_clear', '') for ft in fulltext]
            
                for res in data_dict['resources']:
                    if 'fulltext' in res:
                        del res['fulltext']
                    if 'fulltext_clear' in res:
                        del res['fulltext_clear']
                pkg_dict['data_dict'] = json.dumps(data_dict)
                # temporary set old fashioned(!) fulltext to empty str
                pkg_dict['fulltext'] = ''
                pkg_dict['fulltext_clear'] = ''
        except Exception as e:
            # todo log error
            log.error('error setting resource fulltext for package %s, error: %s' % (package_id, str(e)))

        try:
            if 'validated_data_dict' in pkg_dict:
                validated_data_dict = json.loads(pkg_dict['validated_data_dict'])
                for res in validated_data_dict['resources']:
                    if 'fulltext' in res:
                        del res['fulltext']
                    if 'fulltext_clear' in res:
                        del res['fulltext_clear']
                pkg_dict['validated_data_dict'] = json.dumps(validated_data_dict)
        except:
            log.error('error removing resource fulltext from package validated data dict %s, error: %s' % (package_id, str(e)))

        return pkg_dict


    # for IActions
    def get_actions(self):
        '''Returns a dict containing the keys being the name of the logic 
        function and the values being the functions themselves.
        
        @return: dict containing the logic functions
        '''
        action_functions = get_functions()
        return action_functions
    
     

