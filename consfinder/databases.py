# coding: utf-8

import json
import couchdb
from clint.textui import colored, puts
from consfinder.config import COUCH_DB_HOST, COUCH_DB_PORT, VIEWS_DIR


def get_db(db_name):
    couch = couchdb.Server(url='http://%s:%s' % (COUCH_DB_HOST, COUCH_DB_PORT))
    try:
        db = couch[db_name]
    except:
        try:
            db = couch.create(db_name)
        except:
            puts(colored.red('No CouchDB connection'))
            db = None
    return db


def load_view(filename):
    with open('%s/%s' % (VIEWS_DIR, filename), 'r') as f:
        return f.read()
