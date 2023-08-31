#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy

from sqlalchemy import types, Column, Table, ForeignKey
from sqlalchemy.orm import  relation
from ckan import model

from ckan.model import meta
from ckan.model.meta import mapper
from ckan.model.resource import Resource
from ckan.model import domain_object
import ckan.model.types as _types


try:
    RowProxy = sqlalchemy.engine.result.RowProxy
except AttributeError:
    RowProxy = sqlalchemy.engine.base.RowProxy

__all__ = ['PackageFulltext', 'package_fulltext_table', 'PackageFulltextRevision',
'fulltext_revision_table']

package_fulltext_table  = None

def setup():
    '''
    Creates a new fulltext table if it does not exist in the database. 
    '''
    if package_fulltext_table is None:
        define_tables()
    
    if model.package_table.exists():
        if not package_fulltext_table.exists():
            package_fulltext_table.create()

    

class PackageFulltext(domain_object.DomainObject):
    ''' Object-relational mapper class for the fulltext table.'''
    @classmethod
    def get(cls, key, default=None, attr=None):
        '''Finds a single entity in the register.'''
        if attr == None:
            attr = cls.key_attr
        kwds = {attr: key}
        o = cls.filter(**kwds).first()
        if o:
            return o
        else:
            return default
 
    
def define_tables():
    '''Mappes the fulltext table.'''
    global package_fulltext_table
    package_fulltext_table = Table('resource_fulltext', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('resource_id', types.UnicodeText, ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=True),
    Column('package_id', types.UnicodeText, ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=True),
    Column('text', types.UnicodeText, nullable=True),
    Column('text_clear', types.UnicodeText, nullable=True),
    extend_existing=True
    )

    mapper(
        PackageFulltext,
        package_fulltext_table,
        properties={
            'packageFulltext':relation(
                Resource,
                lazy=True,
                backref='fulltext'
             )
        }
    )



        
