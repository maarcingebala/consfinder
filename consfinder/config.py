# coding: utf-8

import os

try:
	import matplotlib
	matplotlib.rcParams['backend'] = "TkAgg"
except:
	pass

current_path = os.path.dirname(os.path.abspath(__name__))


FLOAT_PRECISION = 5


RESULTS_DIR = os.path.expanduser('~/consfinder_results')
if not os.path.exists(RESULTS_DIR):
	os.makedirs(RESULTS_DIR)


CSV_DST = RESULTS_DIR
VIEWS_DIR = 'db_views'


COUCH_DB_HOST = 'localhost'
COUCH_DB_PORT = '5984'


db_rev = '2'
hypothesis_db_rev = '3'

EXPERIMENTS_DB_NAME = 'experiments_%s' % db_rev
HYPOTHESIS_DB_NAME = 'hypothesis_%s' % hypothesis_db_rev
ARTICLE_EXPERIMENTS_DB = 'article_experiments_%s' % db_rev
