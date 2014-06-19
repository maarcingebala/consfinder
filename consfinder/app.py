# coding: utf-8

import sys
import time
import copy
import datetime
import argparse
from functools import wraps
from operator import itemgetter

from clint.textui import colored, columns, puts, indent

from consfinder.profiles import BinaryProfile
from consfinder.experiments_manager import ExperimentsManager, EuclideanExperimetsManager
from consfinder.experiments_manager import MANAGERS_MAP
from consfinder.functions import ConsensusO1, ConsensusO2, OptimalAlgorithm, CONSENSUS_ALGORITHMS


COLUMN_WIDTH = 20
CONSISTENCY_FUNCTIONS = ['c1', 'c2', 'c3', 'c4', 'c5']


def _add_to_all(subparsers, *args, **kwargs):
    for parser in subparsers.choices.values():
        parser.add_argument(*args, **kwargs)


def _format_value(x):
    if isinstance(x, float):
        return '%.4f' % x
    else:
        return str(x)

def _str_dict(d):
    str_ = ''
    for k, v in d.iteritems():
        str_ += ' %s:%s' % (k.upper(), v)
    return str_


def _get_csv_results_filename(**kwargs):
    t = int(time.time())
    _str = '%s' % t
    for k,v in kwargs.iteritems():
        _str += '_%s%s' % (k, v)
    _str += '.csv'
    return _str


def _confirm_action(text):
    puts(colored.yellow("%s [y/n]" % text))
    answer = raw_input()
    return answer.lower() in ['y', '']


def length_validator(args):
    length = getattr(args, 'length')
    if length and length > 15:
        return False, 'Profile length > 15 can eat your whole memory!'
    return True, ''


def functions_validator(args):
    functions = getattr(args, 'functions')
    if functions:
        for f in functions:
            if not f in CONSISTENCY_FUNCTIONS:
                return False, 'Function %s is not one of %s' % (f, CONSISTENCY_FUNCTIONS)
    return True, ''


def algorithms_validator(args):
    algorithms = getattr(args, 'algorithms')
    if algorithms:
        all_ = CONSENSUS_ALGORITHMS.keys()
        for a in algorithms:
            if not a in all_:
                return False, 'Algorithm %s is not one of %s' % (a, all_)
    return True, ''


def validate(*validators):
    def __outer(f):
        def __inner(args):
            for v in validators:
                res, msg = v(args)
                if not res:
                    puts(colored.red(msg))
                    sys.exit(-1)
            return f(args)
        return __inner
    return __outer


def process_onetest(profile):
    puts(colored.green(
        '==Processing profile with %s elements' % len(profile.elements)))
    with indent(2, ''):
        for element in profile.elements:
            puts(str(element))

    puts(colored.green('\n==Matrix of distances:'))
    with indent(2, ''):
        puts(str(profile.get_matrix()))

    puts(colored.green('\n==Distance measures:'))
    with indent(2, ''):
        puts("Profile diameter: %.3f" % profile.profile_diameter())
        puts("Vector diameter:  %.3f" % profile.vector_diameter())
        puts("The average distance: %.3f" % profile.d_mean())
        puts("The total average distance: %.3f" % profile.d_t_mean())
        puts("Minimal average distance: %.3f" % profile.minimal_avg_distance())

    puts(colored.green('\n==Consistency measures: '))
    with indent(2, ''):
        puts("c1: %.3f" % profile.c1())
        puts("c2: %.3f" % profile.c2())
        puts("c3: %.3f" % profile.c3())
        puts("c4: %.3f" % profile.c4())
        puts("c5: %.3f" % profile.c5())

    puts(colored.green('\n==optimal consensus (quality): '))
    consensus = OptimalAlgorithm.run(profile)
    with indent(2, ''):
        for con in consensus:
            puts("%s (%s)" % (con, profile.quality(con)))

    puts(colored.green('\n==o1 consensus (quality): '))
    consensus = ConsensusO1.run(profile)
    with indent(2, ''):
        for con in consensus:
            puts("%s (%s)" % (con, profile.quality(con)))

    puts(colored.green('\n==o2 consensus (quality): '))
    consensus_o2 = ConsensusO2.run(profile)
    with indent(2, ''):
        for con in consensus_o2:
            puts("%s (%s)" % (con, profile.quality(con)))


def process_experiments_results(results):
    exclude = []
    header = [[key, COLUMN_WIDTH] for key in results['data'][0].keys() if not key in exclude]
    puts(columns(*header))
    for res in results['data']:
        row = []
        for k, v in res.iteritems():
            if not k in exclude:
                row.append([_format_value(v), COLUMN_WIDTH])
        puts(columns(*row))


def process_results_from_db(results):
    for res in results:
        t = res.pop('timestamp')
        params = res.pop('params')
        puts(colored.green('\n==%s (%s)' % (_str_dict(params), datetime.datetime.fromtimestamp(t))))
        fields = sorted(res.keys())
        header = [['No', COLUMN_WIDTH]]
        header.extend([[k, COLUMN_WIDTH] for k in fields])
        puts(columns(*header))
        results_num = len(res[fields[0]])
        for i in range(results_num):
            row = [[str(i + 1), COLUMN_WIDTH]]
            row.extend([[_format_value(res[name][i]), COLUMN_WIDTH] for name in fields])
            puts(columns(*row))


def process_correlations(results):
    width = COLUMN_WIDTH + 2
    header = [[name, width] for name in ['Length', 'N', 'Spearman', 'Pearson']]
    puts(columns(*header))
    for res in sorted(results):
        row = [[str(v), width] for v in [res[0][1], res[0][0], res[1], res[2]]]
        puts(columns(*row))


def process_shapiro(results):
    width = COLUMN_WIDTH + 2
    header = [[name, width] for name in ['Length', 'N', 'Statistic W', 'p-value']]
    puts(columns(*header))
    for res in sorted(results):
        row = [[str(v), width] for v in [res[0][1], res[0][0], res[1][0], res[1][1]]]
        puts(columns(*row))


@validate(length_validator)
def handle_onetest(args):
    profile = BinaryProfile(args.number, args.length, hide_progress=False)
    if args.load:
        profile.load(args.load)
    else:
        profile.generate()
    process_onetest(profile)


@validate(length_validator, functions_validator, algorithms_validator)
def handle_binary_experiments(args):
    manager = ExperimentsManager()
    results = manager.get_results(args.length, args.number)
    if results and _confirm_action('Results for this test available. [y] to show results, [n] to run new experiments.'):
        process_results_from_db(copy.deepcopy(results))
        if args.csv:
            params = results[0]['params']
            filename = getattr(args, 'filename', '') or _get_csv_results_filename(n=params['n'], l=params['length'])
            manager.write_to_csv_from_db(results, filename)
    else:
        results = manager.run_experiment(*args._get_args(), **dict(args._get_kwargs()))
        process_experiments_results(results)
        if args.csv:
            params = results['params']
            filename = getattr(args, 'filename', '') or _get_csv_results_filename(n=params['n'], l=params['length'])
            res = manager.write_to_csv(results, filename)


def handle_euclidean_experiments(args):
    manager = EuclideanExperimetsManager()
    results = manager.get_results(args.number)
    if results and _confirm_action('Results for this test available. [y] to show results, [n] to run new experiments.'):
        process_results_from_db(copy.deepcopy(results))
        if args.csv:
            params = results[0]['params']
            filename = getattr(args, 'filename', '') or _get_csv_results_filename(n=params['n'])
            manager.write_to_csv_from_db(results, filename)
    else:
        results = manager.run_experiment(*args._get_args(), **dict(args._get_kwargs()))
        process_experiments_results(results)
        if args.csv:
            params = results['params']
            filename = getattr(args, 'filename', '') or _get_csv_results_filename(n=params['n'])
            res = manager.write_to_csv(results, filename)


def _handle_correlations(manager, var_x, var_y, names):
    col_width = COLUMN_WIDTH + 2
    results = manager.get_correlations(var_x, var_y)
    header = [[col, col_width] for col in names]
    puts(columns(*header))
    for r in results:
        values = [v for v in r[0]]
        values.extend([r[1][0], r[1][1], r[2][0], r[2][1]])
        row = [[str(x), col_width] for x in values]
        puts(columns(*row))


def handle_binary_correlations(args):
    e = ExperimentsManager()
    names = ['length' ,'n' , 'spearman', 'p-value', 'pearson', 'p-value']
    _handle_correlations(e, args.var_x, args.var_y, names)


def handle_euclidean_correlations(args):
    e = EuclideanExperimetsManager()
    names = ['n' , 'spearman', 'p-value', 'pearson', 'p-value']
    _handle_correlations(e, args.var_x, args.var_y, names)


def main():
    import config

    app = argparse.ArgumentParser()
    subparsers = app.add_subparsers()

    onetest = subparsers.add_parser('onetest',
        help='Generate binary profile and show results for all measures, functions and algorithms.')
    onetest.add_argument('-n', '--number', type=int,
        help='size of collective')
    onetest.add_argument('-l', '--length', type=int,
        help='length of single vector')
    onetest.add_argument('--load',
        help='process profile from given file')
    onetest.set_defaults(func=handle_onetest)


    experiments = subparsers.add_parser('experiments', help='Run multiple experiments.')
    experiements_types = experiments.add_subparsers()
    binary = experiements_types.add_parser('binary', help='Experiments for binary structure')
    euclidean = experiements_types.add_parser('euclidean', help='Experiments for euclidean structure')

    _add_to_all(experiements_types, 'count', type=int, help='number of experiments')
    _add_to_all(experiements_types, '-n', '--number', type=int, help='size of collective')

    binary.add_argument('-l', '--length', type=int, help='length of single vector')
    binary.add_argument('-f', '--functions', nargs='*', default=CONSISTENCY_FUNCTIONS,
        help='specify which consistency functions to test (default: all, possible values: %s)' % CONSISTENCY_FUNCTIONS)
    binary.add_argument('-a', '--algorithms', nargs='*', default=CONSENSUS_ALGORITHMS.keys(),
        help='specify which consensus algorithms to use (default: all, possible values: %s)' % CONSENSUS_ALGORITHMS.keys())
    binary.set_defaults(func=handle_binary_experiments)

    euclidean.add_argument('--with_images', action='store_true',
        help='save images with visualization of generated profiles')
    euclidean.add_argument('--no_equal', action='store_true',
        help='elements in profile have different distances to real state')
    euclidean.set_defaults(func=handle_euclidean_experiments)

    _add_to_all(experiements_types,'--no-db', action='store_true', help='do not save experiments results in db')
    _add_to_all(experiements_types,'--csv', action='store_true', help='write results to CSV file')
    _add_to_all(experiements_types, '--filename', help='specify custom name for output file (works with --csv)')

    correlations = subparsers.add_parser('correlations', help='get correlations')
    corr_types = correlations.add_subparsers()
    binary = corr_types.add_parser('binary', help='Correlations for binary structure')
    euclidean = corr_types.add_parser('euclidean', help='Correlations for euclidean structure')
    _add_to_all(corr_types, 'var_x', help='name of the first variable')
    _add_to_all(corr_types, 'var_y', help='name of the second variable')
    binary.set_defaults(func=handle_binary_correlations)
    euclidean.set_defaults(func=handle_euclidean_correlations)

    args = app.parse_args()
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print "Program interrupted"
        sys.exit(0)


if __name__ == '__main__':
    main()
