# coding: utf-8

from math import sqrt
from clint.textui import progress
from consfinder.config import FLOAT_PRECISION


def minmax(x, min_, max_):
    return (x - min_) / (max_ - min_)


def manhattan_dist(vector_x, vector_y):
    if len(vector_x) != len(vector_y):
        raise ValueError('Cannot calculate distance for vectors of different length')
    return sum([abs(x - y) for x,y in zip(vector_x, vector_y)]) / float(len(vector_x))


def euclidean_distance(vector_x, vector_y):
    return sqrt(sum([pow(abs(x - y), 2) for x, y in zip(vector_x, vector_y)]))


def euclidean_distance_norm(vector_x, vector_y, min_, max_):
    dist = euclidean_distance(vector_x, vector_y)
    return minmax(dist, min_, max_)


class ConsensusAlgorithm(object):

    @classmethod
    def run(cls, profile):
        raise NotImplementedError()


class NOptimalityAlgorithm(ConsensusAlgorithm):

    @classmethod
    def _run(cls, profile, n):
        consensus = []
        best_distance = float("inf") # best = some max value
        universe = profile.get_universe()
        for x in progress.bar(universe, hide=profile.hide_progress):
            d_x_X = round(profile.sum_of_distances_for_element(x, n), FLOAT_PRECISION)
            if d_x_X == best_distance:
                consensus.append(x)
            elif d_x_X < best_distance:
                best_distance = d_x_X
                consensus = [x]
        return consensus


class ConsensusO1(NOptimalityAlgorithm):
    name = 'ConsensusO1'

    @classmethod
    def run(cls, profile):
        return cls._run(profile, 1)


class ConsensusO2(NOptimalityAlgorithm):
    name = 'ConsensusO2'

    @classmethod
    def run(cls, profile):
        return cls._run(profile, 2)


class OptimalAlgorithm(ConsensusAlgorithm):
    name = 'OptimalAlgorithm'

    @classmethod
    def run(cls, profile):
        consensus = []
        for i in progress.bar(range(profile.length), hide=profile.hide_progress):
            col = map(lambda member: member[i], profile.elements)
            consensus.append(int(col.count(1) >= col.count(0)))
        return [consensus]  # result in list for compatibility with other algorithms


CONSENSUS_ALGORITHMS = {
    ConsensusO1.name: ConsensusO1,
    ConsensusO2.name: ConsensusO2,
    OptimalAlgorithm.name: OptimalAlgorithm
}
