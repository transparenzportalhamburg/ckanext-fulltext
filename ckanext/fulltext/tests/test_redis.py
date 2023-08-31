import uuid
from mock import patch

import rq
import ckanext.fulltext.jobs as fulltext_jobs
from ckan.lib import jobs
from ckan.lib.search.common import SearchIndexError

from nose.tools import  assert_equal
from .helpers import get_package_from_index
import ckan.tests.factories as factories


def run_job(fn, args=[]):
    queue = jobs.get_queue('test')
    job = queue.enqueue_call(func=fn, args=args)
    fulltext_jobs.start_worker('test', burst=True)
    
    return job

def job_exception():
    raise Exception('boom')

def job_solr_exception(id):
    raise SearchIndexError('bang')

def test_exception():
    queue = jobs.get_queue('test')
    job = run_job(job_exception)

    registry = queue.failed_job_registry
    for job_id in registry.get_job_ids():
        job = queue.fetch_job(job_id)
        if 'boom' in job.exc_info:
            assert True
            break
    else:
        assert False
    
    
@patch('ckan.common.config')
def test_solr_exception(config):
    queue = 'test_retry'
    def mockGet(key, d):
        if key == 'fulltext.index.retry.queue':
            return queue
        return d
    config.get = mockGet

    guid = str(uuid.uuid4())
    pkg = factories.Dataset(id=guid, name=guid)
    guid_res = str(uuid.uuid4())
    resource = factories.Resource(package_id=guid, id=guid_res, name=guid_res, fulltext='fulltext')

    job = run_job(job_solr_exception, [pkg['id']])
    q = jobs.get_queue(queue)

    failed = q.fetch_job(q.get_job_ids()[0])

    assert_equal(failed.args[0], pkg['id'])
    assert_equal(failed.kwargs['retry'], 1)

    fulltext_jobs.start_worker(queue, burst=True)

    ipkg = get_package_from_index(guid)
    assert_equal(ipkg['resources'][0]['fulltext'], 'fulltext')

def test_requeue_with_failed():
    pass

def test_requeue_witout_failed():
    pass

def test_fetch_with_job():
    pass

def test_fetcht_with_no_job():
    pass
