# coding: utf-8

import os
import csv
import time
from collections import OrderedDict
from functools import wraps

import couchdb
from clint.textui import progress, puts, colored

from consfinder.profiles import BinaryProfile
from consfinder.functions import ConsensusO1, ConsensusO2, OptimalAlgorithm, CONSENSUS_ALGORITHMS
from consfinder.config import (CSV_DST, EXPERIMENTS_DB_NAME, HYPOTHESIS_DB_NAME, ARTICLE_EXPERIMENTS_DB)
from consfinder.databases import get_db, load_view
from consfinder.scripts.hypothesis import (EuclideanProfile, get_rand_radius,
    euclidean_distance, REAL_STATE)


CONSISTENCY_FUNCTIONS = ['c1', 'c2', 'c3', 'c4', 'c5']


def with_db(f):
    @wraps(f)
    def __inner(*args, **kwargs):
        if args:
            manager = args[0]
            if not getattr(manager, 'db', None):
                puts(colored.yellow("DB needed for this operation: %s" % f))
                return
        return f(*args, **kwargs)
    return __inner


class ExperimentsManager(object):

    def __init__(self):
        self.db = get_db(EXPERIMENTS_DB_NAME)

    def run_experiment(self, count, number, length, functions=CONSISTENCY_FUNCTIONS, algorithms=CONSENSUS_ALGORITHMS, no_db=False, *args, **kwargs):
        results = {'params': {'n': number, 'length': length}, 'data':[]}
        for no in progress.bar(range(1, count + 1)):
            single_res = OrderedDict()
            single_res['no'] = no

            profile = BinaryProfile(n=number, length=length)
            profile.generate()
            
            for func_name in functions:
                func = getattr(profile, func_name)
                single_res[func_name] = func()

            for alg_name in algorithms:
                alg = CONSENSUS_ALGORITHMS[alg_name]
                single_res[alg_name] = max([profile.quality(con) for con in alg.run(profile)])

            results['data'].append(single_res)

        if not no_db:
            self.save_results(results, functions, algorithms)

        return results

    @with_db
    def save_results(self, results, functions, algorithms):
        doc = {'params': results['params']}
        doc['timestamp'] = int(time.time())
        doc['consistency'] = {}
        doc['consensus'] = {}
        for f in functions:
            doc['consistency'][f] = map(lambda single_res: single_res[f], results['data'])
        for q in algorithms:
            doc['consensus'][q] = map(lambda single_res: single_res[q], results['data'])
        self.db.save(doc)
        print "Saved in DB"

    def write_to_csv_from_db(self, results, filename):
        filepath = os.path.join(CSV_DST, filename)
        with open(filepath, 'ar') as f:
            writer = csv.writer(f, delimiter=';')
            for single_res in results:
                del single_res['timestamp']
                params = single_res.pop('params')
                writer.writerow(['%s: %s' % (k,v) for k,v in params.iteritems()])

                fields = sorted(single_res.keys())
                results_num = len(single_res[fields[0]])

                writer.writerow([k for k in fields])
                for i in range(results_num):
                    row = [str(single_res[field][i]).replace('.', ',') for field in fields]
                    # row = [str(single_res[field][i]) for field in fields]
                    writer.writerow(row)
                writer.writerow('\n')

    def write_to_csv(self, results, filename):
        filepath = os.path.join(CSV_DST, filename)
        with open(filepath, 'ar') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['%s: %s' % (k,v) for k,v in results['params'].iteritems()])
            writer.writerow([k for k in results['data'][0].iterkeys()])
            for single_res in results['data']:
                row = [str(value).replace('.', ',') for value in single_res.itervalues()]
                # row = [str(value) for value in single_res.itervalues()]
                writer.writerow(row)
            writer.writerow('\n')

    @with_db
    def get_correlations(self, x, y):
        from scipy.stats.stats import spearmanr, pearsonr
        correlations = []
        rows = self.db.view('results/all').rows
        for row in rows:
            x_values = row['value'].get(x)
            y_values = row['value'].get(y)
            correlations.append((row.key, spearmanr(x_values, y_values), pearsonr(x_values, y_values)))
        return correlations

    def _get_single_param_values(self, param):
        results = []
        rows = self.db.view('results/all').rows
        for row in rows:
            values = row['value'].get(param)
            results.append((row.key, values))
        return results

    @with_db
    def shapiro_test(self, param):
        from scipy.stats import shapiro
        all_values = self._get_single_param_values(param)
        results = []
        for key, values in all_values:
            results.append((key, shapiro(sorted(values))))
        return results

    def _get_results(self, startkey, endkey):
        results = []
        try:
            try:
                results = self.db.view('results/all', startkey=startkey, endkey=endkey)
            except couchdb.http.ResourceNotFound:
                view = load_view('results_all.js')
                results = self.db.query(view, startkey=startkey, endkey=endkey)
            finally:
                if results:
                    results = [row.value for row in results]
        except IndexError:
            pass
        return results

    @with_db
    def get_results(self, length, n):
        startkey = endkey = [length, n]
        return self._get_results(startkey, endkey)


class EuclideanExperimetsManager(ExperimentsManager):

    def __init__(self, *args, **kwargs):
        super(EuclideanExperimetsManager, self).__init__(*args, **kwargs)
        self.db = get_db(HYPOTHESIS_DB_NAME)

    def run_experiment(self, count, number, functions=['c1', 'c2', 'c3', 'c4', 'c5'], no_db=False, with_images=False, no_equal=False, *args, **kwargs):
        shared_universe = []
        shared_perimeter = []

        def get_o2_consensus(profile):
            o2 = ConsensusO2.run(profile)
            best_i, best_q = max([(i, profile.quality(con)) for i, con in enumerate(o2)], key=lambda x:x[1])
            best_el = o2[best_i]
            dist = euclidean_distance(best_el, REAL_STATE)
            return best_q, dist, best_el

        radius = 1
        results = {'params': {'n': number, 'radius': radius}, 'data':[]}

        for no in progress.bar(range(1, count + 1)):
            single_res = OrderedDict()
            single_res['no'] = no

            profile = EuclideanProfile(n=number, universe=shared_universe, perimeter=shared_perimeter)
            profile.generate(equal_dist=not no_equal)

            if not (shared_universe and shared_perimeter):
                shared_universe = profile.universe
                shared_perimeter = profile.perimeter
            
            for func_name in functions:
                func = getattr(profile, func_name)
                single_res[func_name] = func()
            best_q, dist, best_el = get_o2_consensus(profile)
            single_res[ConsensusO2.name] = best_q
            single_res['dist_from_real'] = dist
            results['data'].append(single_res)
            if with_images:
                profile.save_fig(extra=[best_el], name_suffix=str(no))

        if not no_db:
            self.save_results(results, functions, algorithms=[ConsensusO2.name])
        return results

    @with_db
    def save_results(self, results, functions, algorithms):
        doc = {'params': results['params']}
        doc['timestamp'] = int(time.time())
        doc['consistency'] = {}
        doc['consensus'] = {}
        for f in functions:
            doc['consistency'][f] = map(lambda single_res: single_res[f], results['data'])
        for q in algorithms:
            doc['consensus'][q] = map(lambda single_res: single_res[q], results['data'])
        doc['distances'] = map(lambda single_res: single_res['dist_from_real'], results['data'])
        self.db.save(doc)
        print "Saved in DB"

    @with_db
    def get_results(self, n):
        startkey = endkey = [n]
        return self._get_results(startkey, endkey)


MANAGERS_MAP = {
    'binary': ExperimentsManager,
    'euclidean': EuclideanExperimetsManager
}