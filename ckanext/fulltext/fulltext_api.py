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
import html
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

from ckan.model import Session
from ckanext.spatial.lib import save_package_extent,validate_bbox, bbox_query
from ckanext.spatial.model.inforeg_model import setupFulltextTable as setup_model
from ckanext.fulltext.model.setup_fulltext_table import PackageFulltext
from ckan.model.package_extra import PackageExtra
from ckanext.harvest.plugin import Harvest

from ckanext.spatial.lib import save_package_extent,validate_bbox, bbox_query
from ckanext.spatial.model.package_extent import setup as setup_model

log = getLogger(__name__)


''' Metadata  fields that are not shown by default'''
hide_fields = [] 
#['full_text_search', 'transformierteliefersystemmetadaten_encoded', 'store_date']
# 'publishing_date','exact_publishing_date', entfernt, da die Portal-Extension diese benoetigt
# Welcher Benutzer wird von der Portal-Extension verwendet?


def get_functions():
    return {
            'package_show': package_show_minimal,
            'package_show_rest': package_show_rest_minimal,
            'package_search': package_search_minimal,
            'user_show': user_show_minimal,
            'current_package_list_with_resources': current_package_list_with_resources_minimal,
            'package_create': package_create_minimal,
            'package_create_rest': package_create_rest_minimal,
            'package_update': package_update_minimal,
            'package_update_rest': package_update_rest_minimal,
            'fulltext_delete': fulltext_delete
    }


def _init_hide_fields():
    global hide_fields
    try:
        hide_fields = config.get('ckan.spatial.hide.fields').split()
    except Exception, e:
        hide_fields = []    



def check_logged_in(context):
    ''' Check if user is logged in.
    (Users must be logged-in to view all metadata fields.)
    '''
    model = context['model']
    try:
        user = context['user']
        userobj = model.User.get(user)
    except Exception, e:

        # for internal commands like reindex use the whole api (including filtered fields)
        if context['ignore_auth']:
            userobj = True
        else:
            userobj = False

    if userobj:
        return True

    return False

   
def _del_extra_field_from_list(data_dict, delete_field=None):
    if delete_field in data_dict['extras'].keys():
            del data_dict['extras'][delete_field]
            return data_dict
    
    _init_hide_fields()     
    delete_key = []
    for field in hide_fields:
        if field in data_dict['extras'].keys():
            delete_key.append(field)
     
    for key in delete_key:       
        del data_dict['extras'][key]
    return data_dict  


def _del_extra_field_from_dict(data_dict, delete_field=None):
    '''Deletes metadata fields from the extras dict'''
    if 'extras' in data_dict:
        if delete_field:
            for dict in data_dict['extras']:
                if dict['key'] in delete_field:
                    (data_dict['extras']).remove(dict) 
                    return data_dict 

        _init_hide_fields()
        delete_dicts = []
        for dict in data_dict['extras']:
            if dict['key'] in hide_fields:
                delete_dicts.append(dict)
        
        for del_dict in delete_dicts: 
            (data_dict['extras']).remove(del_dict)

    return data_dict     

    
@toolkit.side_effect_free
def package_show_rest_minimal(context, data_dict):
    package = get.package_show_rest(context, data_dict)
    
    if check_logged_in(context):       
        fulltext = _get_fulltext(package['id'])
        if fulltext:
            package['extras']['full_text_search'] = fulltext.text 
        
        return package
    
    minimal_package =  _del_extra_field_from_list(package)
    return minimal_package


@toolkit.side_effect_free
def package_show_minimal(context, data_dict):
    '''Return the metadata of a dataset (package) and its resources.

    :param id: the id or name of the dataset
    :type id: string
    :param use_default_schema: use default package schema instead of
    a custom schema defined with an IDatasetForm plugin (default: False)
    :type use_default_schema: bool
    
    :rtype: dictionary

    '''

    package = get.package_show(context, data_dict)
    
    if check_logged_in(context):
        fulltext = _get_fulltext(package['id'])
        if fulltext:
            fulltext_dict = { 'key': 'full_text_search',
                              'value': fulltext.text
                            }
            package['extras'].append(fulltext_dict) 
        return package
    
    minimal_package =  _del_extra_field_from_dict(package)
    return minimal_package



def _get_fulltext(package_id):
    from ckanext.spatial.model.inforeg_model.setupFulltextTable import setup
    setup()
    if package_id:
        fulltext = Session.query(PackageFulltext) \
                            .filter(PackageFulltext.package_id==package_id) \
                            .first()
                            
        return fulltext
    return None


@toolkit.side_effect_free
def package_search_minimal(context, data_dict):
    '''
    Searches for packages satisfying a given search criteria.
    This action accepts solr search query parameters (details below), and
    returns a dictionary of results, including dictized datasets that match
    the search criteria, a search count and also facet information.

    **Solr Parameters:**

    For more in depth treatment of each paramter, please read the `Solr
    Documentation <http://wiki.apache.org/solr/CommonQueryParameters>`_.

    This action accepts a *subset* of solr's search query parameters:


    :param q: the solr query.  Optional.  Default: ``"*:*"``
    :type q: string
    :param fq: any filter queries to apply.  Note: ``+site_id:{ckan_site_id}``
        is added to this string prior to the query being executed.
    :type fq: string
    :param sort: sorting of the search results.  Optional.  Default:
        ``'relevance asc, metadata_modified desc'``.  As per the solr
        documentation, this is a comma-separated string of field names and
        sort-orderings.
    :type sort: string
    :param rows: the number of matching rows to return.
    :type rows: int
    :param start: the offset in the complete result for where the set of
        returned datasets should begin.
    :type start: int
    :param facet: whether to enable faceted results.  Default: ``True``.
    :type facet: string
    :param facet.mincount: the minimum counts for facet fields should be
        included in the results.
    :type facet.mincount: int
    :param facet.limit: the maximum number of values the facet fields return.
        A negative value means unlimited. This can be set instance-wide with
        the :ref:`search.facets.limit` config option. Default is 50.
    :type facet.limit: int
    :param facet.field: the fields to facet upon.  Default empty.  If empty,
        then the returned facet information is empty.
    :type facet.field: list of strings


    The following advanced Solr parameters are supported as well. Note that
    some of these are only available on particular Solr versions. See Solr's
    `dismax`_ and `edismax`_ documentation for further details on them:

    ``qf``, ``wt``, ``bf``, ``boost``, ``tie``, ``defType``, ``mm``


    .. _dismax: http://wiki.apache.org/solr/DisMaxQParserPlugin
    .. _edismax: http://wiki.apache.org/solr/ExtendedDisMax


    **Results:**

    The result of this action is a dict with the following keys:

    :rtype: A dictionary with the following keys
    :param count: the number of results found.  Note, this is the total number
        of results found, not the total number of results returned (which is
        affected by limit and row parameters used in the input).
    :type count: int
    :param results: ordered list of datasets matching the query, where the
        ordering defined by the sort parameter used in the query.
    :type results: list of dictized datasets.
    :param facets: DEPRECATED.  Aggregated information about facet counts.
    :type facets: DEPRECATED dict
    :param search_facets: aggregated information about facet counts.  The outer
        dict is keyed by the facet field name (as used in the search query).
        Each entry of the outer dict is itself a dict, with a "title" key, and
        an "items" key.  The "items" key's value is a list of dicts, each with
        "count", "display_name" and "name" entries.  The display_name is a
        form of the name that can be used in titles.
    :type search_facets: nested dict of dicts.
    :param use_default_schema: use default package schema instead of
        a custom schema defined with an IDatasetForm plugin (default: False)
    :type use_default_schema: bool

    An example result: ::

     {'count': 2,
      'results': [ { <snip> }, { <snip> }],
      'search_facets': {u'tags': {'items': [{'count': 1,
                                             'display_name': u'tolstoy',
                                             'name': u'tolstoy'},
                                            {'count': 2,
                                             'display_name': u'russian',
                                             'name': u'russian'}
                                           ]
                                 }
                       }
     }

    **Limitations:**

    The full solr query language is not exposed, including.

    fl
        The parameter that controls which fields are returned in the solr
        query cannot be changed.  CKAN always returns the matched datasets as
        dictionary objects.
    '''

    result_dict = get.package_search(context, data_dict)
    
    if check_logged_in(context):
        for result in result_dict['results']:
            fulltext = _get_fulltext(result['id'])
            if fulltext:
                fulltext_dict = { 'key': 'full_text_search',
                                  'value': fulltext.text
                                }
                result['extras'].append(fulltext_dict) 
        return result_dict
    
    new_packages = []
    for result in result_dict['results']:
        new_package = _del_extra_field_from_dict(result)
        new_packages.append(new_package)
    result_dict['results'] = new_packages
    
    return result_dict


@toolkit.side_effect_free
def user_show_minimal(context, data_dict):
    '''Return a user account.

    Either the ``id`` or the ``user_obj`` parameter must be given.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary

    :rtype: dictionary

    '''
    result_dict = get.user_show(context, data_dict)
    
    if check_logged_in(context):
        for result in result_dict['datasets']:
            fulltext = _get_fulltext(result['id'])
            if fulltext:
                fulltext_dict = { 'key': 'full_text_search',
                                  'value': fulltext.text
                                }
                result['extras'].append(fulltext_dict) 
        return result_dict
    
    new_packages = []
    for result in result_dict['datasets']:
        new_package = _del_extra_field_from_dict(result)
        new_packages.append(new_package)
    result_dict['datasets'] = new_packages
    return result_dict

    
@toolkit.side_effect_free   
def current_package_list_with_resources_minimal(context, data_dict):
    '''Return a list of the site's datasets (packages) and their resources.

    The list is sorted most-recently-modified first.

    :param limit: if given, the list of datasets will be broken into pages of
        at most ``limit`` datasets per page and only one page will be returned
        at a time (optional)
    :type limit: int
    :param offset: when ``limit`` is given, the offset to start
        returning packages from
    :type offset: int
    :param page: when ``limit`` is given, which page to return,
        Deprecated: use ``offset``
    :type page: int

    :rtype: list of dictionaries

    '''
    results = get.current_package_list_with_resources(context, data_dict)
    
    if check_logged_in(context):
        for result in results:
            fulltext = _get_fulltext(result['id'])
            if fulltext:
                fulltext_dict = { 'key': 'full_text_search',
                                  'value': fulltext.text
                                }
                result['extras'].append(fulltext_dict)  
        return results
    
    new_packages = []
    for result in results:
        new_package = _del_extra_field_from_dict(result)
        new_packages.append(new_package)

    return new_packages


def package_create_minimal(context, data_dict):  
    '''Create a new dataset (package).

    You must be authorized to create new datasets. If you specify any groups
    for the new dataset, you must also be authorized to edit these groups.

    Plugins may change the parameters of this function depending on the value
    of the ``type`` parameter, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'``
    :type name: string
    :param title: the title of the dataset (optional, default: same as
        ``name``)
    :type title: string
    :param author: the name of the dataset's author (optional)
    :type author: string
    :param author_email: the email address of the dataset's author (optional)
    :type author_email: string
    :param maintainer: the name of the dataset's maintainer (optional)
    :type maintainer: string
    :param maintainer_email: the email address of the dataset's maintainer
        (optional)
    :type maintainer_email: string
    :param license_id: the id of the dataset's license, see
        :py:func:`~ckan.logic.action.get.license_list` for available values
        (optional)
    :type license_id: license id string
    :param notes: a description of the dataset (optional)
    :type notes: string
    :param url: a URL for the dataset's source (optional)
    :type url: string
    :param version: (optional)
    :type version: string, no longer than 100 characters
    :param state: the current state of the dataset, e.g. ``'active'`` or
        ``'deleted'``, only active datasets show up in search results and
        other lists of datasets, this parameter will be ignored if you are not
        authorized to change the state of the dataset (optional, default:
        ``'active'``)
    :type state: string
    :param type: the type of the dataset (optional),
        :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugins
        associate themselves with different dataset types and provide custom
        dataset handling behaviour for these types
    :type type: string
    :param resources: the dataset's resources, see
        :py:func:`resource_create` for the format of resource dictionaries
        (optional)
    :type resources: list of resource dictionaries
    :param tags: the dataset's tags, see :py:func:`tag_create` for the format
        of tag dictionaries (optional)
    :type tags: list of tag dictionaries
    :param extras: the dataset's extras (optional), extras are arbitrary
        (key: value) metadata items that can be added to datasets, each extra
        dictionary should have keys ``'key'`` (a string), ``'value'`` (a
        string)
    :type extras: list of dataset extra dictionaries
    :param relationships_as_object: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_object: list of relationship dictionaries
    :param relationships_as_subject: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_subject: list of relationship dictionaries
    :param groups: the groups to which the dataset belongs (optional), each
        group dictionary should have one or more of the following keys which
        identify an existing group:
        ``'id'`` (the id of the group, string), ``'name'`` (the name of the
        group, string), ``'title'`` (the title of the group, string), to see
        which groups exist call :py:func:`~ckan.logic.action.get.group_list`
    :type groups: list of dictionaries
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string

    :returns: the newly created dataset (unless 'return_id_only' is set to True
              in the context, in which case just the dataset id will
              be returned)
    :rtype: dictionary

    '''
    
    from ckanext.spatial.model.inforeg_model.setupFulltextTable import setup
    setup()
    package= ''
    fulltext = ''
    old_fulltext = ''
 
    if data_dict.has_key('extras'):
        contains = _contains_key(data_dict['extras'], 'full_text_search')
        if(contains): 
            fulltext = contains
            data_dict = _del_extra_field_from_dict(data_dict, 'full_text_search')
            
            package = create.package_create(context, data_dict)
            old_fulltext = None
            if package.has_key('id'):
                old_fulltext = Session.query(PackageFulltext) \
                                    .filter(PackageFulltext.package_id==package['id']) \
                                    .first()

            fulltext_dict_save(fulltext, old_fulltext, package, context)
        else:
    
            package = create.package_create(context, data_dict)
            
    else:
    
        package = create.package_create(context, data_dict)
      

    if check_logged_in(context):
        if fulltext:
            # why fulltext.text? Left it for compatibility
            if isinstance(fulltext,unicode): 
                valueFulltext = fulltext
            else:
                valueFulltext = fulltext.text
            fulltext_dict = { 'key': 'full_text_search',
                              'value': valueFulltext
                            }
            package['extras'].append(fulltext_dict) 
        return package
    
    minimal_package = _del_extra_field_from_dict(package)
    return minimal_package


def _contains_key(data_list, key):
    for dict in data_list:
        if(dict['key'] == key):
            return dict['value']
    
    return None


def _get_extras_dict(extras):
    from numbers import Number
    extras_as_dict = []
    
    if isinstance(extras, dict):
        for key, value in extras.iteritems():
            if isinstance(value, (basestring, Number)):
                extras_as_dict.append({'key': key, 'value': value})
            else:
                extras_as_dict.append({'key': key, 'value': json.dumps(value, ensure_ascii=False)})
        
        return extras_as_dict
    return extras


def package_create_rest_minimal(context, data_dict):
   
    from ckanext.spatial.model.inforeg_model.setupFulltextTable import setup
    setup()
    package= ''
    fulltext = ''
    old_fulltext = ''

    categories = []

    if all(isinstance(n, basestring) for n in data_dict['groups']):
        groups = data_dict['groups']
        for g in groups:
             categories.append({'name': g})
        data_dict['groups']= categories
        
    
    if all(isinstance(n, basestring) for n in data_dict['tags']):
        tags = []
        for tag in data_dict['tags']:
            tags.append({'name': tag})
        
        data_dict['tags'] = tags

    if data_dict.has_key('extras'):
        if 'full_text_search' in data_dict['extras'].keys():
            fulltext = data_dict['extras']['full_text_search']
            data_dict = _del_extra_field_from_list(data_dict, 'full_text_search')
    
            data_dict['extras'] = _get_extras_dict(data_dict['extras'])
            
            package = create.package_create(context, data_dict)

            old_fulltext = None
            if package.has_key('id'):
                old_fulltext = Session.query(PackageFulltext) \
                                    .filter(PackageFulltext.package_id==package['id']) \
                                    .first()

            fulltext_dict_save(fulltext, old_fulltext, package, context)
        else:
            data_dict['extras'] = _get_extras_dict(data_dict['extras'])
            package = create.package_create(context, data_dict)

    else:
        data_dict['extras'] = _get_extras_dict(data_dict['extras'])
        package = create.package_create(context, data_dict)

            
    
    if check_logged_in(context):
        fulltext = _get_fulltext(package['id'])
        if fulltext:
            package['extras']['full_text_search'] = fulltext.text 
        return package
    
    minimal_package = _del_extra_field_from_list(package)
    return minimal_package



def fulltext_dict_save(fulltext_dict, old_fulltext, pkg, context):
    if fulltext_dict is None:
        return
    
    model = context["model"]
    session = context["session"]
    id = pkg['id']

    
    #deleted
    if pkg['state'] == 'deleted' and old_fulltext:
        from ckan import model
        model.Session.delete(old_fulltext)
        try:
            model.repo.commit_and_remove()
            log.info(u'Purged fulltext row with package id {}'.format(pkg['id']))
        except IntegrityError,e:
            log.error(u'An integrity error while purging (package id {})'.format(pkg['id']))

    #new   
    elif not old_fulltext and fulltext_dict:
        state = 'pending' if context.get('pending') else 'active'
        fulltext = PackageFulltext()
        fulltext.package_id=id
        fulltext.text=fulltext_dict
        fulltext.save()
        model.Session.flush()
        
    #changed
    elif old_fulltext != fulltext_dict:
        state = 'pending' if context.get('pending') else 'active'
        old_fulltext.text = fulltext_dict
        old_fulltext.save()
        model.Session.commit()
        model.Session.flush()


    

def package_update_minimal(context, data_dict):
    '''Update a dataset (package).

    You must be authorized to edit the dataset and the groups that it belongs
    to.
    
    It is recommended to call
    :py:func:`ckan.logic.action.get.package_show`, make the desired changes to
    the result, and then call ``package_update()`` with it.

    Plugins may change the parameters of this function depending on the value
    of the dataset's ``type`` attribute, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    For further parameters see
    :py:func:`~ckan.logic.action.create.package_create`.

    :param id: the name or id of the dataset to update
    :type id: string

    :returns: the updated dataset (if ``'return_package_dict'`` is ``True`` in
              the context, which is the default. Otherwise returns just the
              dataset id)
    :rtype: dictionary

    '''
    from ckanext.spatial.model.inforeg_model.setupFulltextTable import setup
    setup()
    package= ''
    fulltext = ''
    old_fulltext = ''
    if data_dict.has_key('extras'):
        contains = _contains_key(data_dict['extras'], 'full_text_search')
        if(contains): 
            fulltext = contains
            data_dict = _del_extra_field_from_dict(data_dict, 'full_text_search')
        
            package = update.package_update(context, data_dict)
            old_fulltext = None
            if package.has_key('id'):
                old_fulltext = Session.query(PackageFulltext) \
                                    .filter(PackageFulltext.package_id==package['id']) \
                                    .first()

            fulltext_dict_save(fulltext, old_fulltext, package, context)
        else:
            package = update.package_update(context, data_dict)
    else:
        package = update.package_update(context, data_dict)
        

    if check_logged_in(context):
        fulltext = _get_fulltext(package['id'])
        if fulltext:
            fulltext_dict = { 'key': 'full_text_search',
                              'value': fulltext.text
                            }
            package['extras'].append(fulltext_dict) 
        return package
    
    minimal_package = _del_extra_field_from_dict(package)
    return minimal_package



def package_update_rest_minimal(context, data_dict):
    from ckanext.spatial.model.inforeg_model.setupFulltextTable import setup
    setup()

    package= ''
    fulltext = ''
    old_fulltext = ''
    if data_dict.has_key('extras'):
        if 'full_text_search' in data_dict['extras'].keys():
            fulltext = data_dict['extras']['full_text_search']
            data_dict = _del_extra_field_from_list(data_dict, 'full_text_search')
            
            
            package = update.package_update_rest(context, data_dict)
            
            old_fulltext = None
            if package.has_key('id'):
                old_fulltext = Session.query(PackageFulltext) \
                                    .filter(PackageFulltext.package_id==package['id']) \
                                    .first()

            fulltext_dict_save(fulltext, old_fulltext, package, context)
        else:
            package = update.package_update(context, data_dict)

    else:
        package = update.package_update_rest(context, data_dict)
    
    if check_logged_in(context):
        fulltext = _get_fulltext(package['id'])
        if fulltext:
            package['extras']['full_text_search'] = fulltext.text 
        return package
    
    minimal_package = _del_extra_field_from_list(package)
    
    return minimal_package


def fulltext_delete(context, data_dict):  
    '''Deletes Fulltext.'''
    from ckanext.spatial.model.inforeg_model.setupFulltextTable import setup
    setup()
   
    old_fulltext = ''
    if package.has_key('id'):
        old_fulltext = Session.query(PackageFulltext) \
                            .filter(PackageFulltext.package_id==package['id']) \
                            .first()

        fulltext_dict_save(None, old_fulltext, data_dict, context)    
    return true
    





