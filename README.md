# ckanext-fulltext - Fulltext searching plugin for CKAN #
This extension provides plugins that allow CKAN to store and search full text data. It uses a new Solr field 
to do a full text search and then display the matches in CKAN. 

The full text field enables the user to find datasets that contain text he or she is looking for, without the text being 
part of one of the CKAN fields. That means the full text will be stored separate and apart from other CKAN package data in 
Solr as well as in the PostgreSQL database.

Additionaly you can parse the fulltext of documents using a [JCC](https://lucene.apache.org/pylucene/jcc/)-Wrapper for [Apache Tika](https://tika.apache.org/).

## Plugin Installation ##
- Install the extension into your python environment:
   
	   (pyenv) $ pip install -e git + https://github.com/transparenzportalhamburg/ckanext-fulltext.git#egg=ckanext-fulltext
      
- Your CKAN configuration ini file should contain the following plugin:

		ckan.plugins = inforeg_solr_search

- Add a new field to your conf/schema.xml that acts like a catch-all field for the content of all resources:
 
		<field name="fulltext" type="textgen" indexed="true" stored="true"/>
		...
		<copyField source="fulltext" dest="text"/> 
     
- Create a fulltext table:

		paster --plugin=ckanext-fulltext fulltext init_fulltext_table --config=/etc/ckan/default/development.ini


## Tika-Wrapper Installation (for Ubuntu) 
In order to use the tikaparser you have to install jcc (http://lucene.apache.org/jcc/).  
JCC requieres a recent  cpp compliler, Java JDK 1.7+. 

If you dont have the above installed just

	sudo apt-get update
	sudo apt-get install build-essential
	sudo apt-get install openjdk-7-jdk

After that you should be able to install jcc

	 pip install jcc

Now install the tikaparser

    cd /path/to/ckanext-fulltext/ckanext/fulltext/parser
    python setup.py build
    python setup.py install

## API usage

Once you've downloaded a full text online resource that you want to search in, create a package
with a new metadata field `full_text_search` to store the full text or add this field to an 
exististing package by calling package_update:

    package_entity = {
       'name': package_name,
       'url': package_url,
       'notes': package_long_description,
       'extras': [{'key':'full_text_search', 'value':'full text online resource'}]
    }


After rebuilding the search index 

	paster --plugin=ckan search-index rebuild --config=/etc/ckan/default/development.ini

you should get results from your full-text searches via http://test.ckan.net/api/3/action/package_search?q=full



The following CKAN API functions will return complete packages that means the full text of each package will 
be added to the metadata field 'full_text_search':

	package_show
	user_show
	package_search
	current_package_list_with_resources


## Hide extras fields

Hidden fields are fields that are used for e.g. administrative purposes, but not shown to the user.

You can set an option in the CKAN config file to specify extras fields which are not
visible (GUI and API functions) for any user except sysadmin. By default, the field ''full_text_search'' will 
also be not shown:

     ckan.fulltext.hide.fields = extras_field1 extras_field2 ...

You can set an option in the CKAN config file (hmbtg.ini) to specify extras fields and standard CKAN fields which are not visible (GUI and API functions) for any user except sysadmin:

	hide.extras.fields = full_text_search extras_field1 extras_field2 ...
	hide.main.fields = maintainer_email author_email ...


## Parse Fulltext with Tika


Parsing the fulltext is easy:

```python
 from ckanext.fulltext.parser.tikaparser import Tika_Wrapper_Singleton

 tika_parser = Tika_Wrapper_Singleton()
 fulltext = tika_parser.parse_with_tika('path_to_local_file_or_url')
```

For advanced configuration (proxy, max_heap of the JVM) check the docs of tikaparser.py.

## Copying and License

This material is copyright (c) 2015  Fachliche Leitstelle Transparenzportal, Hamburg, Germany.

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0 whose full text may be found at:

http://www.fsf.org/licensing/licenses/agpl-3.0.html

