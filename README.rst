======================================================
ckanext-fulltext - full text searching plugin for CKAN
======================================================
|

This extension provides plugins that allow CKAN to store and search full text data. It uses a new Solr field 
to do a full text search and then display the matches in CKAN. 

The full text field enables the user to find datasets that contain text he or she is looking for, without the text being 
part of one of the CKAN fields. That means the full text will be stored separate and apart from other CKAN package data in 
Solr as well as in the PostgreSQL database.

Additionaly you can parse the fulltext of documents using a JCC-Wrapper for Apache Tika.
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
Tika-Wrapper Installation (for Ubuntu)
======================================

In order to use the tikaparser you have to install jcc (http://lucene.apache.org/jcc/).
JCC requieres a recent  cpp compliler, Java JDK 1.7+. 

If you dont have the above installed just do:
 sudo apt-get update
 sudo apt-get install build-essential
 sudo apt-get install openjdk-7-jdk

After that you should be able to install jcc:
 pip install jcc

Now install the tikaparser:
 cd /path/to/ckanext-fulltext/ckanext/fulltext/parser
 python setup.py build
 python setup.py install
 

Parse Fulltxt with Tika
=======================

Parsing the fulltext is easy:

 from tikaparser import TikaWrapperSingleton

 tika_parser = TikaWrapperSingleton()
 fulltext = tika_parser.parse_with_tika('path_to_local_file_or_url')

For advanced configuration (proxy, max_heap of the JVM) check the docs of ckanext/fulltext/tikaparser.py.


API usage
=========
|

Once you've downloaded a full text online resource that you want to search in, create a package
with a new metadata field `full_text_search` to store the full text or add this field to an 
exististing package by calling package_update::
    package_entity = {
       'name': package_name,
       'url': package_url,
       'notes': package_long_description,
       'extras': [{'key':'full_text_search', 'value':'full text online resource'}]
    }

|

After rebuilding the search index you should get results from your full-text searches::
   paster --plugin=ckan search-index rebuild --config=/etc/ckan/default/development.ini

   http://test.ckan.net/api/3/action/package_search?q=full

|

The following CKAN API functions will return complete packages that means the full text of each package will 
be added to the metadata field 'full_text_search'::
   package_show
   user_show
   package_search
   current_package_list_with_resources

>>>>>>> 24c3399c24e2debd659ceadbb64ea88b81702996
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
=======
You can set an option in the CKAN config file (hmbtg.ini) to specify extras fields and standard CKAN fields which are not
visible (GUI and API functions) for any user except sysadmin::     

     hide.extras.fields = full_text_search extras_field1 extras_field2 ...
     hide.main.fields = maintainer_email author_email ...

|
|

Copying and License
===================
|
This material is copyright (c) 2015  Fachliche Leitstelle Transparenzportal, Hamburg, Germany.

|

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0 whose full text may be found at:
http://www.fsf.org/licensing/licenses/agpl-3.0.html

|
|
>>>>>>> 24c3399c24e2debd659ceadbb64ea88b81702996
