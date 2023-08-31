#NEEDS TO MOVE TO hmbtg_utils
from ckanext.fulltext.model.setup_fulltext_table import PackageFulltext, setup
from ckan.model import Session
from sqlalchemy import or_
from sqlalchemy.sql.expression import func

UNPROCESSED_FULLTEXT = 'UNPROCESSED_FULLTEXT'
FULLTEXT_UNAVAILABLE = 'NOT_AVAILABLE'
FULLTEXT_ERROR = 'ERROR_FULLTEXT'

error_fulltexts = [UNPROCESSED_FULLTEXT, FULLTEXT_ERROR,
 'Es ist ein interner Serverfehler aufgetreten.',
 'Wrong parameter set',
 'Wrong parameter set!',
 'Portlet Application ingrid-portal-apps not available',
 '404 Not Found   Not Found  The requested URL was not found on this server.',
 'Service Unavailable  Service Unavailable   HTTP Error 503. The service is unavailable.']

def all_fulltext_package_ids():
    ids = Session.query(PackageFulltext.package_id).with_entities(PackageFulltext.package_id).distinct()
    return [i for i, in ids]

def package_ids_with_fulltext(text):
    if type(text) == str:
        ids =  Session.query(PackageFulltext.package_id).filter(PackageFulltext.text == text).distinct()
    else:
        ids =  Session.query(PackageFulltext.package_id).filter(or_(*[func.trim(PackageFulltext.text) == t for t in text])).distinct()
    return [i for i, in ids]

def package_ids_with_error():
    return package_ids_with_fulltext(error_fulltexts)

def package_ids_min_fulltext_size(max_size):
    ids = Session.query(PackageFulltext.package_id).filter(func.length(PackageFulltext.text)>max_size).distinct()
    return [i for i, in ids]

def get_first_fulltext_obj(resource_id):
    return Session.query(PackageFulltext).filter(PackageFulltext.resource_id == resource_id).first()

def get_all_fulltext_objs(resource_id):
    return Session.query(PackageFulltext).filter(PackageFulltext.resource_id == resource_id).all()

def find_fulltext_object_delete_other(csession, resource_id):
    all_fulltext_obj = get_all_fulltext_objs(resource_id)
    if len(all_fulltext_obj) > 1:
        fulltext_processed_obj = csession.query(PackageFulltext).filter(PackageFulltext.resource_id == resource_id).filter(or_(PackageFulltext.text != UNPROCESSED_FULLTEXT , PackageFulltext.text != FULLTEXT_ERROR)).first()
        if fulltext_processed_obj:
            csession.query(PackageFulltext).filter(PackageFulltext.resource_id == resource_id).filter(PackageFulltext.id != fulltext_processed_obj.id).delete()
            fulltext_obj = fulltext_processed_obj
        else:
            fulltext_obj = all_fulltext_obj[0]
            csession.query(PackageFulltext).filter(PackageFulltext.resource_id == resource_id).filter(PackageFulltext.id != fulltext_obj.id).delete()
    else:
        fulltext_obj = all_fulltext_obj[0]
    return fulltext_obj

def create_fulltext_obj(resource_id, fulltext):
    fulltext_obj = PackageFulltext()
    fulltext_obj.package_id = id
    fulltext_obj.resource_id = resource_id
    fulltext_obj.text = fulltext
    fulltext_obj.text_clear = None
    fulltext_obj.save()
    return fulltext_obj

def package_fulltext_error_count():
    q = ' or '.join(["text='%s'"%s for s in error_fulltexts])
    return Session.execute("select count(distinct(package_id)) from resource_fulltext where " + q).first()[0]
    # return Session.query(PackageFulltext).filter(or_(*[func.trim(PackageFulltext.text) == t for t in error_fulltexts])).count()

def package_fulltext_unprocessed_count():
    return Session.execute("select count(distinct(package_id)) from resource_fulltext where text = 'UNPROCESSED_FULLTEXT'").first()[0]

def package_fulltext_unavailable_count():
    return Session.execute("select count(distinct(package_id)) from resource_fulltext where text = 'NOT_AVAILABLE'").first()[0]