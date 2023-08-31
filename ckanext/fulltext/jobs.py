import rq
import logging
import ckan.common

from ckan.plugins.toolkit import config
from ckan.lib.search.index import PackageSearchIndex
from ckan.lib.search.common import SearchIndexError
from ckan.lib import jobs as ckan_jobs
from ckan.lib.jobs import Worker

from ckan import model
from ckan.logic import get_action

log = logging.getLogger(__name__)


REPAIR_LOGGER_NAME = 'repair_fulltext_logger'
#Queue
DEFAULT_QUEUE_NAME = 'fulltext'
#Job
DEFAULT_JOB_TIMEOUT = 600
DEFAULT_JOB_RETRIES = 0


def add(fn, args=None, kwargs=None, title=None, queue=''):
    timeout = config.get('rq.job.timeout', DEFAULT_JOB_TIMEOUT)
    job = ckan_jobs.get_queue(queue).enqueue_call(func=fn, args=args, kwargs=kwargs, timeout=timeout)
    job.meta['title'] = title
    job.save()

    return job


def get_failed_ids(queue_name=DEFAULT_QUEUE_NAME) -> None:
    queue = ckan_jobs.get_queue(queue_name)
    ids = queue.failed_job_registry.get_job_ids()
    
    return ids

def get_number_of_failed(queue_name: str=DEFAULT_QUEUE_NAME) -> int:  
    queue = ckan_jobs.get_queue(queue_name)
    registry = queue.failed_job_registry

    return len(registry)

def requeue_all_failed(queue_name=DEFAULT_QUEUE_NAME) -> None:
    queue = ckan_jobs.get_queue(queue_name)
    registry = queue.failed_job_registry

    for job_id in get_failed_ids(queue_name):
        registry.requeue(job_id)
    

def fetch(job_id, queue_name: str=DEFAULT_QUEUE_NAME) -> rq.job.Job:
    queue = ckan_jobs.get_queue(queue_name)
    
    return queue.fetch_job(job_id)


def index_package(pid, retry: int) -> None:
    logger = logging.getLogger(REPAIR_LOGGER_NAME)
    logger.info(f'{retry}. retry of solr index on package {pid}')
    context = {'model': model, 
               'ignore_auth': True,
               'validate': False, 
               'use_cache': False}
    package_index = PackageSearchIndex()
    package_dict = get_action('package_show')(context, {'id': pid})
    package_index.index_package(package_dict, defer_commit=True)

def clear_all(queue_name: str=DEFAULT_QUEUE_NAME):
    queue = ckan_jobs.get_queue(queue_name)
    queue.empty()
class LogStream(object):
    def __init__(self):
        self.logs = ''

    def write(self, msg):
        self.logs += msg
  
    def flush(self):
        pass

    def __str__(self):
        return self.logs


def exc_handler(job, *exc_info):
    if exc_info[0] == SearchIndexError:
        queue = ckan.common.config.get('fulltext.index.retry.queue', DEFAULT_QUEUE_NAME)
        pid = job.args[0]
        title = f'retry index for package {pid}'
        retry = job.kwargs.get('retry', DEFAULT_JOB_RETRIES)
        if retry < 5:
            add(index_package, 
                args=[pid], 
                kwargs={'retry': retry+1}, 
                title=title, 
                queue=queue)
            return False
    return True


def start_worker(queue=DEFAULT_QUEUE_NAME, burst=False):
    redis_conn = ckan_jobs._connect()
    logger = logging.getLogger(REPAIR_LOGGER_NAME)
    stream = LogStream()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    Worker(queue, exception_handlers=[exc_handler]).work(burst=burst)
