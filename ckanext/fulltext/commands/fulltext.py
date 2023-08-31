import click

import ckan.plugins as p
import ckanext.fulltext.jobs as jobs
from ckan import model
from ckan.logic import get_action
from ckan.lib.search.index import PackageSearchIndex
from ckanext.fulltext.postprocess import resource_fulltext_process as ftprocess
from ckan.common import asbool

def _get_admin_user():
    context = {'model': model, 
               'session': model.Session, 
               'ignore_auth': True}
    return get_action('get_site_user')(context, {})


@click.group(short_help=u"Perform fulltext related operations.")
def fulltext():
    pass


@fulltext.command()
@click.option("-d", "--date", default=None, help='min-date')
def init_fulltext_table(date):
    '''Creates a new table called package_fulltext 
        in the database or on a remote server.
        '''
    _init_fulltext_table(date)


def _init_fulltext_table(date):
    admin_user = _get_admin_user()
    context = {'model': model,
               'user': admin_user['name'], 
               'session': model.Session}

    ftprocess.init_fulltext_table(context, date)


@fulltext.command()
@click.argument('package_id', required=False, default=None)
@click.option('-i', '--index', default=False, help='index package after fulltext received')
@click.option('-n', '--clean', default=False, help='clean fulltext after it is received')
@click.option('-r', '--retry', default=False, help='retry ressources marked as ERROR_FULLTEXT')
@click.option('-a', '--all', default=False, help='force reprocess of all ressources')
@click.option('-j', '--job', default=False, help='process with jobs')
def process(package_id, index, clean, retry, all, job):
    _process(package_id, asbool(index), asbool(clean), asbool(retry), asbool(all), asbool(job))


def _process(package_id, index, clean, retry, all, job):
    admin_user = _get_admin_user()
    context = {'model': model,
               'user': admin_user['name'], 
               'session': model.Session}
    
    ftprocess.process(context, index, clean, retry, all, job, package_id)


@fulltext.command()
def list_errors():
    error_messages = _list_errors()

    for error_message in error_messages:
        print(error_message)


def _list_errors(queue_name=jobs.DEFAULT_QUEUE_NAME):
    failed_job_ids = jobs.get_failed_ids(queue_name)
    messages = []

    for id in failed_job_ids:
        job = jobs.fetch(id, queue_name)
        messages.append(f'Job with args {job.args} failed at {job.ended_at} with error:')
        messages.append(f'{job.exc_info}')
    if messages:
        return messages
    else:
        return 'No failed jobs found.'

@fulltext.command()
def requeue_failed_jobs():
    print(_requeue_failed_jobs())


def _requeue_failed_jobs(queue_name=jobs.DEFAULT_QUEUE_NAME):
    number_of_failed = jobs.get_number_of_failed(queue_name)
    jobs.requeue_all_failed(queue_name)
    return f'{number_of_failed} have been requeued.'


@fulltext.command()
def work():
    jobs.start_worker()


@fulltext.command()
def commit_index():
    _commit_index()


def _commit_index():
    package_index = PackageSearchIndex()
    package_index.commit()


class FulltextCommands(p.SingletonPlugin):
    p.implements(p.IClick)

    def get_commands(self):
        return [fulltext]
