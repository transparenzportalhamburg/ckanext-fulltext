
# Allris uses another url for retrieving the fulltext
# of a resource than the resource.url, i.e., the
# resource.url cannot be used for retrieving the fulltext
# Instead a url is computed from the guid of a 
# harvest_object that corresponds to the package


import urllib.parse
from ckanext.harvest.model import HarvestObject
from ckan.model import Session


# copied from allris_harvester.py for computing the fulltext url
# url is the resource.url!
# id is the guid of a harvest_object
def computeFulltextDetailedUrl(url, id, doctype):
    if doctype=='protocol':
        return computeFulltextDetailedUrlForProtocol(url, id)
    if doctype=='document':
        return computeFulltextDetailedUrlForDocument(url, id)
    return None

def computeFulltextDetailedUrlForProtocol(url, id):
    print("\n protocol identified\n")
    try:
        parsedURL=urllib.parse.urlparse(url)
        InstallationsPath  = get_installation_path(parsedURL.path)
        # resource_locator from the guid of the harvest_object  
        # see computeResourceDetailedUrl in allris_harvester
        volfdnr = id.split("#volfdnr=")[1].split("#")[0]
        # same as silfdnr (see allris_harvester
        #silfdnr = id.split("#volfdnr=")[1].split("#")[0]
        # it is the same: volfdnr and resource_locator
        resource_locator = volfdnr
        urlDokument = "https://" + parsedURL.netloc + InstallationsPath + "do027.asp?DOLFDNR=" + resource_locator + "&options=64&dtyp=116"
        return urlDokument
    except:
        print("\n error, return normal url")
        return url

def computeFulltextDetailedUrlForDocument(url, id):
    print("\n document identified\n")
    try:
        parsedURL=urllib.parse.urlparse(url)
        InstallationsPath  = get_installation_path(parsedURL.path)
        guid = id.split("#guid=")[1]
        MethadatenPath = InstallationsPath + "do027.asp"
        query="?DOLFDNR=" + guid + "&options=64&dtyp=130"
        return parsedURL.scheme + "://" + parsedURL.netloc + MethadatenPath + query
    except:
        print("\n error, return normal url")
        return url

def get_installation_path(path):
    if path.find("/bi/") > -1:
        return "/bi/"
    if path.find("/ti/") > -1:
        return "/ti/"

def get_identifier_guid_for_package(package_id):
    harvested_objects_for_package = Session.query(HarvestObject) \
                                           .filter(HarvestObject.current == True) \
                                           .filter(HarvestObject.package_id == package_id) \
                                           .filter(HarvestObject.state == 'COMPLETE') \
                                           .all()
    if len(harvested_objects_for_package) == 0:
        print("No harvested_object found")
        return None
    if len(harvested_objects_for_package) > 1:
        # to be replaced with a logger
        print("\nno exact harvest object found\n")
        return None
    else:
        guid=harvested_objects_for_package[0].guid
        print("\nfor package: %s found guid: %s\n" % \
            (package_id, guid))
        return guid

def allris_package(package_id, resource_url):
    if 'sitzungsdienst' in resource_url:
        return True
    return False

def allris_document(package_id, package_title):
    if "Drucksache " in package_title:
        return True
    return False

def allris_protocol(package_id, resource_name):
    if "Sitzungsprotokoll (Druckversion) " in resource_name:
        return True
    return False

def get_fulltext_url_for_resource(package_id, package_title, resource_url, resource_name):

    if not allris_package(package_id, resource_url):
        return resource_url
    # allris package identified
    doctype=None
    if allris_document(package_id, package_title):
            doctype="document"
    if allris_protocol(package_id, resource_name):
            doctype="protocol"
        
    if doctype==None:
        print("\n allris document not identified as document or protocoll\n")
        return resource_url
    guid = get_identifier_guid_for_package(package_id)
    if guid:
        fulltextURL=computeFulltextDetailedUrl(resource_url, guid, doctype)
        if fulltextURL:
            return fulltextURL
    print("\n no fulltext url found take resource url\n")
    return resource_url
