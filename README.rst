======================================================
ckanext-fulltext - full text searching plugin for CKAN
======================================================
|

This extension provides plugins that allow CKAN to store and search full text data. It uses a new Solr field 
to do a full text search and then display the matches in CKAN. 

The full text field enables the user to find datasets that contain text he or she is looking for, without the text being 
part of one of the CKAN fields. That means the full text will be stored separate and apart from other CKAN package data in 
Solr as well as in the PostgreSQL database.
|
|
Plugin Installation
===================
|
1. Install the extension into your python environment::
   
     (pyenv) $ pip install -e git+https://race.informatik.uni-hamburg.de/inforeggroup/ckanext-fulltext.git#egg=ckanext-fulltext
       
2. Your CKAN configuration ini file should contain the following plugin::

      ckan.plugins = inforeg_solr_search

3. Add a new field to your conf/schema.xml that acts like a catch-all field for the content of all resources::

     ...
     <field name="fulltext" type="textgen" indexed="true" stored="true"/>
     ...
     <copyField source="fulltext" dest="text"/> 
     
4. Create a fulltext table::

     paster --plugin=ckanext-fulltext fulltext init_fulltext_table --config=/etc/ckan/default/development.ini

     
|
|
|
API usage
=========
|
|
|

Hide extras fields
==================
|
Hidden fields are fields that are used for e.g. administrative purposes, but not shown to the user.

You can set an option in the CKAN config file to specify extras fields which are not
visible (GUI and API functions) for any user except sysadmin. By default, the field ''full_text_search'' will 
also be not shown::     

     ckan.fulltext.hide.fields = extras_field1 extras_field2 ...

|
|
|
License
=======
