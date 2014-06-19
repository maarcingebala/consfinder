# coding: utf-8

import random
import time
from itertools import product

from numpy import matrix
from clint.textui import progress

from consfinder.functions import manhattan_dist, euclidean_distance


class NoUniverse(Exception):
    pass


class Profile(object):

    def __init__(self, n, length, distance_func, hide_progress=True, **kwargs):
        self.n = n
        self.length = length
        self.distance_func = distance_func
        self.hide_progress = hide_progress
        self.init_empty()

    def init_empty(self):
        self.universe = []
        self.elements = []
        self.matrix = None
        self.vector = []

    def get_universe(self):
        if not self.universe:
            raise NoUniverse()
        return self.universe

    def get_matrix(self):
        '''Returns the matrix of distances between profile elements'''
        if self.matrix is None:
            t = time.time()
            matrix_ = []
            for i in progress.bar(self.elements, hide=self.hide_progress):
                matrix_.append([self.distance_func(i, j) for j in self.elements])
            self.matrix = matrix(matrix_)
            if not self.hide_progress:
                print "Matrix of distances generated in %s secs" % (int(time.time() - t))
        return self.matrix

    def get_vector(self):
        if self.vector:
            return self.vector
        else:
            m = self.get_matrix()
            avg_in_column = lambda m, i: m.sum(0).item(i) / float(len(m)-1)
            self.vector = [avg_in_column(m, i) for i in range(len(m))]
            return self.vector

    def profile_diameter(self):
        '''Diameter of profile - max value in matrix of distances'''
        return self.get_matrix().max()

    def vector_diameter(self):
        '''Diameter of vector of average distances - max value in vector'''
        return max(self.get_vector())

    def d_mean(self):
        '''The average distance in profile'''
        m = len(self.get_matrix())
        total = 0.0
        for i in xrange(m):
            for j in xrange(m):
                total += self.get_matrix()[i].item(j)
        result = total / (m * (m - 1))
        return result

    def d_t_mean(self):
        '''The total average distance in profile'''
        m = len(self.elements)
        total = 0.0
        for x in self.elements:
            for y in self.elements:
                total += self.distance_func(x, y)
        result = total / (m * (m + 1))
        return result

    def sum_of_distances_for_element(self, x, n=1):
        '''d(x,X) - returns the sum of distances between an element x of universe U
        and the elements of profile.'''
        return sum([pow(self.distance_func(x,y), n) for y in self.elements])

    def sums_profile_to_universe(self):
        '''Returns set of all sums of distances between profile elements 
        and elements from the universe'''
        return set([self.sum_of_distances_for_element(x)
            for x in self.get_universe()])

    def minimal_avg_distance(self):
        return (1.0/len(self.elements)) * min(self.sums_profile_to_universe())

    def c1(self):
        return 1 - self.profile_diameter()

    def c2(self):
        return 1 - self.vector_diameter()

    def c3(self):
        return 1 - self.d_mean()

    def c4(self):
        return 1 - self.d_t_mean()

    def c5(self):
        return 1 - self.minimal_avg_distance()

    def quality(self, x):
        return 1 - self.sum_of_distances_for_element(x) / len(self.elements)

    def load(self, *args, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        _str = ''
        for x in self.elements:
            _str += '%s\n' % x
        return _str


class BinaryProfile(Profile):

    def __init__(self, n, length, **kwargs):
        super(BinaryProfile, self).__init__(n, length, distance_func=manhattan_dist, **kwargs)

    def _init_universe(self):
        t = time.time()
        self.universe = [x for x in product([0,1], repeat=self.length)]
        if not self.hide_progress:
            print "Space of %s vectors have been generated in %s secs" % (len(self.universe), (int(time.time() - t)))

    def generate(self, **kwargs):
        self.init_empty()
        for i in xrange(self.n):
            self.elements.append([random.randint(0,1) for _ in xrange(self.length)])
        if not self.universe:
            self._init_universe()
        return self.elements

    def load(self, filename):
        self.init_empty()
        with open(filename) as f:
            lines = filter(lambda l: not l.startswith('#'), f.readlines())
            lines = [l.strip() for l in lines]
            for line in lines:
                if line:
                    self.elements.append([int(x) for x in line.split(',')])
        self.length = len(self.elements[0])
        self._init_universe()
        return self.elements

