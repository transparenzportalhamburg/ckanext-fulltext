import logging
from ckan.model import Session
from ckan.model import Package
from ckanext.fulltext.parser.hmbtg_utils import Hmbtg_Utils 
import ckanext.fulltext.hmbtg_config as hmbtg_config 


from ckan import logic, model
from ckan.lib.search.index import PackageSearchIndex

from ckanext.fulltext.postprocess.moving_window import ClearText

from ckanext.fulltext.postprocess.resource_fulltext_helper import get_fulltext_url_for_resource
from ckanext.fulltext.parser.tikaparser import ResourceNotFound, UnprocessableEntity
from ckanext.harvest.model import HarvestObject
import ckanext.fulltext.jobs as jobs
from urllib.error import ContentTooShortError

from hmbtg_utils.environment import activate
from hmbtg_utils.collections import chunked
import hmbtg_utils.logging.events as events
import hmbtg_utils.daos.package as package_dao
import hmbtg_utils.daos.fulltext as fulltext_dao
from hmbtg_utils.daos.fulltext import UNPROCESSED_FULLTEXT, FULLTEXT_UNAVAILABLE, FULLTEXT_ERROR 

logger = logging.getLogger('repair_fulltext_logger')

args = None
db_engine = None


def _get_package_ids(min_date=None):
    # get resource ids where state is active

    if min_date is None:
        ids = Session.query(Package.id).all()
    else:
        ids = Session.query(Package.id).filter(Package.metadata_modified > min_date).all()
    ids = [id.id for id in ids]
    return ids


def _set_fulltext_for_package(id, csession, do_clean=False, retry=False, silent_fail=True):
    hmbtg_utils = Hmbtg_Utils()
    package = package_dao.get_package(id)
    title = package.title
    resources = package.resources
    number_of_resources = len(resources)
    for resource in resources:
        resource_id = resource.id
        fulltext_obj = fulltext_dao.find_fulltext_object_delete_other(csession, resource_id)
        fulltext_obj.text = FULLTEXT_ERROR
        fulltext_obj.text_clear = FULLTEXT_ERROR
        csession.commit()

        res_url = resource.url
        res_name = resource.name
        url = get_fulltext_url_for_resource(id, title, res_url, res_name)
        filesize = resource.extras.get('file_size', None)

        logger.info('getting fulltext for resource id: {0}, size: {1}, url: {2}'.format(resource_id, filesize, url))
        js_redirect = resource.extras.get('js_redirect', False)

        fulltext_clean = None
        if "alkis_liegenschaftskarte" in url:
            logger.info('ALKIS Liegenschaftskarte, es wird kein Volltext ermittelt. URL : %s' % url)
            fulltext_obj.text = FULLTEXT_UNAVAILABLE
        else:
            try:
                fulltext = hmbtg_utils.handleURLandFulltext(url,title,id, httpsProxy=True ,jsredirect=js_redirect, filesize=filesize ,number_of_resources=number_of_resources, force_get=True)
            except (ResourceNotFound, UnprocessableEntity, ContentTooShortError) as e:
                logger.error(f"url not found or unprocessable: {e}" )
                fulltext = FULLTEXT_ERROR

            if fulltext.strip() == "":
                fulltext = FULLTEXT_UNAVAILABLE
                fulltext_clean = ""
            else:
                if do_clean:
                    r = res_url.lower()
                    if r.endswith('rar') or r.endswith('zip') or r.endswith('pdf'):
                        logger.info('start clean fulltext')
                        clearText = ClearText()
                        fulltext_clean = clearText.clear_text(fulltext)

        max_fulltext_chars = int(hmbtg_config.get('max_chars_fulltext', 0)) 
        if max_fulltext_chars > 0:
            fulltext = fulltext[:max_fulltext_chars]
        logger.info('setting fulltext: %s' % fulltext.strip()[:50])
        fulltext_obj.text = fulltext
        if do_clean:
            if max_fulltext_chars > 0 and len(fulltext) > max_fulltext_chars:
                fulltext_obj.text_clear = fulltext_clean[:max_fulltext_chars]
            else:
                fulltext_obj.text_clear = fulltext_clean
        else:
            fulltext_obj.text_clear = None

def get_harvest_source(session, id):
    harvest_object = session.query(HarvestObject) \
        .filter(HarvestObject.package_id==id) \
        .filter(HarvestObject.current==True) \
        .first()

    try:
        return harvest_object.source.title
    except:
        return None
)

def _set_fulltext_for_resources(package_ids, context=None, do_index=False, do_clean=False, retry=False, silent_fail=True):
    csession = Session()
    cleanSources = hmbtg_config.get('fulltext.clean.sources', '').split(',')
    context = { 'model': model, 'ignore_auth': True, 'validate': False, 'use_cache': False }

    if do_index:
        package_index = PackageSearchIndex()

    id_chunks = chunked(package_ids, size=10)
    for id_chunk in id_chunks:
        for p_id in id_chunk:
            if do_clean and get_harvest_source(csession, p_id) in cleanSources:
                _set_fulltext_for_package(p_id, csession, True, retry, silent_fail)
            else:
                _set_fulltext_for_package(p_id, csession, False, retry, silent_fail)
            if do_clean:
                package_dict = logic.get_action('package_show')(context, {'id': p_id})
                package_index.index_package(package_dict, defer_commit=True)
            logger.debug('finished processing package {0}'.format(p_id))
        if do_index:
            package_index.commit()
        logger.info('commiting to database')
        csession.commit()
        

def _set_fulltext_to_unprocessed(session, package_ids, check_exist=False):
    for package_id in package_ids:
        try:
            package = session.query(Package).filter(Package.id == package_id).first()
            resources = package.resources  # only active resources
            for resource in resources:
                try:
                    resource_id = resource.id
                    fulltext = UNPROCESSED_FULLTEXT
                    if check_exist:
                        fulltext_obj = fulltext_dao.get_first_fulltext_obj(resource_id)
                        if fulltext_obj is not None:
                            # update
                            fulltext_obj.text = fulltext
                            fulltext_obj.text_clear = None
                            continue
                    # create resource fulltext object
                    fulltext_obj = fulltext_dao.create_fulltext_obj(package_id, resource_id, fulltext)
                except Exception as e:
                    logger.error('error processing resource with id: {0}, error: {1}'.format(resource_id, str(e)))

        except Exception as e:
            logger.error('error processing package with id: {0}, error: {1}'.format(package_id, str(e)))
    session.commit() # for updated ones...?


def process_run(context, index, clean, ids, retry, silent_fail=True):
    logger.info('index: {0}, clean: {1}'.format(index, clean))
    _set_fulltext_for_resources(ids, context, index, clean, retry, silent_fail)


def process_package_id(id, index, clean, retry, index_commit=False):
    try:
        events.newContext()
        events.log('start', zdata={'pkgid': id})
        logger.info('start processing {0} with index: {1}, clean: {2}'.format(id, index, clean))
        fulltext_dao.setup()
        activate()
        session = Session()
        _set_fulltext_for_package(id, session, clean, retry, silent_fail=False)
        session.commit()
        if index:
            context = { 'model': model, 'ignore_auth': True, 'validate': False, 'use_cache': False }
            package_index = PackageSearchIndex()
            package_dict = logic.get_action('package_show')(context, {'id': id})
            package_index.index_package(package_dict, defer_commit=True)
            if index_commit:
                package_index.commit()

    except Exception:
        events.error()
        logger.info('failed processing {0} with index: {1}, clean: {2}'.format(id, index, clean), exc_info=True)
        raise
    events.log('end')
    logger.info('done processing {0} with index: {1}, clean: {2}'.format(id, index, clean))

def init_fulltext_table(context, date=None):
    logger.info('-' * 50)
    logger.info('initialize resource fulltext table')
    fulltext_dao.setup()
    ids = _get_package_ids(date)
    check_exist = False if date is None else True
    logger.info('number of packages: %s, check existing: %s' % (len(ids), check_exist))
    session = context["session"]
    _set_fulltext_to_unprocessed(session, ids, check_exist)
    logger.info('initialize finished')

def get_pkg_ids(force_all=False, retry=True, max_size=None):
    if force_all:
        ids = fulltext_dao.all_fulltext_package_ids()
    else:
        if retry:
            ids = fulltext_dao.package_ids_with_error()
        else:
            ids = fulltext_dao.package_ids_with_fulltext(UNPROCESSED_FULLTEXT)
    if max_size:
        ids += fulltext_dao.package_ids_min_fulltext_size(max_size)
    return ids

def process(context, index, clean, retry=False, force_all=False, use_jobs=False, package_id=None):
    logger.info('-' * 50)
    fulltext_dao.setup()

    if use_jobs:
        if package_id:
            ids = [package_id]
        else:
            max_chars = int(hmbtg_config.get('max_chars_fulltext', 0)) 
            max_chars = max(max_chars, len(UNPROCESSED_FULLTEXT))
            ids = get_pkg_ids(force_all=force_all, retry=retry, max_size=max_chars)
        if len(ids):
            logger.info("put %s packages on job queue" %len(ids))
            events.log('start', msg='found pkgs to process', data={'count': len(ids)})
            for i, id in enumerate(ids):
                jobs.add(process_package_id, [id, index, clean, retry], {'index_commit':False}, queue='fulltext')
        return

    if package_id:
        process_run(context, index, clean, [package_id], retry, False)
        return

    if force_all:
        session = Session()
        ids = fulltext_dao.all_fulltext_package_ids()
        logger.info("processing all %s packages" %len(ids))
        process_run(context, index, clean, ids, True)
