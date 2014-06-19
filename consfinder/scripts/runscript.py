# coding: utf-8

from consfinder.experiments_manager import ExperimentsManager, EuclideanExperimetsManager


def test_n():
	# def run_experiment(self, count, number, length, functions, algorithms, no_db=False, *args, **kwargs):
    em = ExperimentsManager()
    for n in range(200, 1000, 100):
        print "running test for n=%s" % n
        em.run_experiment(25, n, length=5)


def binary_run_bulk(params, count=25):
	em = ExperimentsManager()
	for (length, number) in params:
		print "Running case: ", number, length
		# em.run_experiment(count, number, length, algorithms=['OptimalAlgorithm', 'ConsensusO2'])
		em.run_experiment(count, number, length)

def euclidean_run_bulk(params, count=25):
	em = EuclideanExperimetsManager()
	for number in params:
		print "Running case: ", number
		em.run_experiment(count, number, no_equal=True)


if __name__ == '__main__':

	# tests_params = [
	# 	# (15, 200),
	# 	(5, 200),
	# 	(5, 300),
	# 	(5, 400),
	# 	(5, 500),
	# 	(5, 600),
	# 	(5, 700),
	# 	(5, 800),
	# 	(5, 900),
	# 	(5, 1000),
	# 	(5, 1500),
	# 	(5, 2000),
	# 	(15, 300),
	# 	(15, 400),
	# 	(15, 500),
	# 	(15, 600),
	# 	(15, 700),
	# 	(15, 800),
	# 	(15, 900),
	# 	(15, 1500),
	# 	(15, 2000),
	# ]

	# binary_run_bulk(tests_params)

	params = [100, 500, 1000, 200, 300, 400, 600, 700, 800, 900, 1500]
	euclidean_run_bulk(params)
    