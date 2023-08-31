# -*- coding: utf-8 -*-
import os
import argparse
import traceback
import multiprocessing
import sys

from configparser import SafeConfigParser

from ckan.model import Session, init_model

from ckanext.fulltext.postprocess.utils import _flatten 
from ckanext.fulltext.postprocess.moving_window import ClearText
from ckanext.fulltext.model.setup_fulltext_table import PackageFulltext, setup

from joblib import Parallel, delayed

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

import logging
logging.basicConfig()
log_path = "/home/ckanuser/ckanLogs"
filename = os.path.join(log_path,  'fulltext_clean.log')
if not os.path.exists(log_path):
    os.makedirs(log_path)
fh = logging.FileHandler(filename)
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger = logging.getLogger()
logger.handlers = []
logger.addHandler(fh)
logger.setLevel(logging.INFO)

db_engine = None

def _setup_db():
    try:
        config_filepath = '/etc/ckan/default/development.ini'
        parser = SafeConfigParser()
        parser.read('/etc/ckan/default/development.ini')
        db = parser.get('app:main', "sqlalchemy.url")
        if len(sys.argv) > 2:
            db_name =  sys.argv[2]
            splited = db.split("/")
            print(splited)
            db.replace(splited[-1], db_name)
        global db_engine
        db_engine = create_engine(db)
        init_model(db_engine)
        setup()
    except:
        print(traceback.format_exc())
        sys.exit(1)


def _setup_argparse(): 
    parser = argparse.ArgumentParser(description='clean fulltext field.')
    parser.add_argument('-m', '--mode', default='all', help='defines which rows to clean [(all), empty, RESOURCE_ID]')
    return parser.parse_args()
    

def _get_all_resource_ids():
    ids = Session.query(PackageFulltext.resource_id).all()
    ids = [id.resource_id for id in ids]
    return ids


def _get_resource_ids_with_empty_package():
    ids = Session.query(PackageFulltext.resource_id).filter(PackageFulltext.text_clear == None).all()
    ids = [id.resource_id for id in ids]
    return ids


def _clean_text(pids):
    global db_engine
    ct = ClearText()
    csession = scoped_session(sessionmaker(bind=db_engine))
    for id in pids:
        try:
            ft = csession.query(PackageFulltext).filter(PackageFulltext.resource_id == id).first()
            #todo check if exists
            text_clear, wrong = ct.clear_text(ft.text)
            ft.text_clear = text_clear
        except Exception as e:
            logger.error('error cleaning, resource id: {0}, error: {1}'.format(id, str(e)))
    csession.commit()
    csession.close()
    csession.remove()


def _get_chunks(ids, n):
    chunks = [ids[i:i + n] for i in range(0, len(ids), n)]
    return chunks


def _process(ids):
    logger.info('processing {0} documents'.format(len(ids)))
    try:
        num_cores = multiprocessing.cpu_count()
        chunks = _get_chunks(ids, 100)
        logger.info('cores: {0}, chunks: {1}'.format(num_cores, len(chunks)))
        Parallel(n_jobs=num_cores)(delayed(_clean_text)(c) for c in chunks)
    except Exception as e:
        logger.error('error cleaning, process, error: {0}'.format(str(e)))


def main(mode):
    _setup_db()
    logger.info('-' * 50)
    logger.info('start cleaning')
    try:
        if mode == 'all':
            ids = _get_all_resource_ids()
            logger.info('cleaning all documents')
            logger.info('number of documents: {0}'.format(len(ids)))
            _process(ids)
        elif mode == 'empty':
            logger.info('cleaning documents with empty fulltext_clear')
            ids = _get_resource_ids_with_empty_package()
            logger.info('number of documents: {0}'.format(len(ids)))
            _process(ids)
        else: # id
            _process([mode])
    except Exception as e:
        logger.error(str(e))
        raise e
    Session.commit()
    Session.close()
    logger.info('finished cleaning')



if __name__ == "__main__":
    args = _setup_argparse()
    mode = args.mode.lower()
    main(mode)
