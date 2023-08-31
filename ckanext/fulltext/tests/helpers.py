import time
import uuid
from ckan.common import config
import ckan.tests.helpers as helpers
import ckan.tests.factories as factories

import ckan.tests.helpers as helpers
from ckan.lib.search.index import PackageSearchIndex
from ckan import model 


def wait_until(condition, timeout=5.0, granularity=0.3, time_factory=time):
    end_time = time.time() + timeout   
    ret = condition()              
    while not ret and time.time() < end_time:    
        time.sleep(granularity)        
        ret = condition()          
    return ret

def get_package_from_index(id):
    PackageSearchIndex().commit()

    context = { 'ignore_auth': False, 
                'model': model, 
                'user':'sysadmin', 
                'use_cache':False }
    
    def get(): 
        ret = helpers.call_action('package_search', q='id:{0}'.format(id), context=context)['results']
        return ret[0] if len(ret) else None
    
    return wait_until(get, timeout=10, granularity=0.5)

def create_dataset(fulltext='', url=''):
        # user = factories.User()
        guid = str(uuid.uuid4())
        guid_res = str(uuid.uuid4())
        pkg = factories.Dataset(id=guid, name=guid)
        resource = factories.Resource(package_id=guid,
                                      id=guid_res,
                                      name=guid_res,
                                      url=url,
                                      fulltext=fulltext)
        return pkg
