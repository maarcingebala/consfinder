# coding: utf-8

import os
import sys
import random
import numpy
import time
from itertools import product
from clint.textui import colored, puts, indent
from clint.textui import progress

from consfinder.profiles import Profile
from consfinder.functions import ConsensusO2, euclidean_distance, euclidean_distance_norm
from consfinder.config import RESULTS_DIR

try:
    from matplotlib import pyplot as plt
    HAS_PYPLOT = True
except:
    raise
    HAS_PYPLOT = False


FLOAT_PRECISION = 2
REAL_STATE = (0, 0)

MAX_DISTANCE = 2
MAX_RADIUS = 1


_euclidean_distance_norm = euclidean_distance_norm
def euclidean_distance_norm(vector_x, vector_y):
    result = _euclidean_distance_norm(vector_x, vector_y, 0, MAX_DISTANCE)
    return result


def get_rand_radius():
    # max_radius = 0.5 # normalized
    while True:
        r = round(random.uniform(0, MAX_RADIUS), FLOAT_PRECISION)
        if r > 0.25 * MAX_RADIUS:     # ensure not to small distance
            print "RADIUS ", r
            return r


class EuclideanProfile(Profile):
    
    def __init__(self, n, universe=[], perimeter=[], **kwargs):
        '''Creates a profile of (x,y) pairs where both x and y belong to [-1, 1]
        and each element have identical distance to real state (0,0)'''
        super(EuclideanProfile, self).__init__(n, length=2, distance_func=euclidean_distance_norm, **kwargs)
        self.real_state = REAL_STATE
        self.radius = MAX_RADIUS
        if universe and perimeter:
            self.universe = universe
            self.perimeter = perimeter
        else:
            self.perimeter = []
            self.universe = []
            self._init_universe()

    def _init_universe(self, radius=1):
        step = 1.0 / pow(10, FLOAT_PRECISION)
        elements = numpy.arange(-1, 1 + step, step).tolist()
        rounded = [round(x, FLOAT_PRECISION) for x in elements]
        
        r_squared = radius ** 2
        delta = pow(10, FLOAT_PRECISION)

        for x in progress.bar(list(product(rounded, repeat=2)), hide=self.hide_progress):
            _sum_squared = x[0] ** 2 + x[1] ** 2
            if round(_sum_squared, FLOAT_PRECISION) == round(r_squared, FLOAT_PRECISION):
                self.perimeter.append(x)
                self.universe.append(x)
            elif round(_sum_squared, FLOAT_PRECISION) < round(r_squared, FLOAT_PRECISION):
                self.universe.append(x)

    def generate(self, equal_dist=True, **kwargs):
        self.equal_dist = equal_dist
        if self.equal_dist:
            self.elements = [random.choice(self.perimeter) for _ in range(self.n)]
        else:
            self.elements = [random.choice(self.universe) for _ in range(self.n)]

    def quality(self, x):
        return 1 - euclidean_distance(x, REAL_STATE)

    def _draw_fig(self, extra):
        if not HAS_PYPLOT:
            print "Module matplotlib.pyplot is not installed"
            return False

        fig = plt.gcf()
        fig.set_size_inches((8,8))

        # if self.equal_dist:
        elements_circle = plt.Circle(REAL_STATE, self.radius, color='r', fill=False)
        fig.gca().add_artist(elements_circle)

        plt.scatter(*REAL_STATE, c='r')
        plt.scatter(*zip(*self.elements))
        if extra:
            plt.scatter(*zip(*extra), c='g')
        plt.xlim(-MAX_DISTANCE / 2, MAX_DISTANCE / 2)
        plt.ylim(-MAX_DISTANCE / 2, MAX_DISTANCE / 2)
        return True
        
    def show_fig(self, extra=[]):
        if self._draw_fig(extra):
            plt.show()
    
    def save_fig(self, extra=[], name_suffix=''):
        if self._draw_fig(extra):
            filename = 'fig_%s_%s' % (int(time.time()), name_suffix)
            path = os.path.join(RESULTS_DIR, filename)
            plt.savefig(path)
            plt.clf()


def process_hypothesis(profile, show_profile=True, radius=None):
    print profile.get_matrix()
    print

    puts(colored.green('\n==Profile elements (quality): '))
    for element in profile.elements:
        puts("%s" % str(element))
    
    puts(colored.green('\n==Consistency measures: '))
    with indent(2, ''):
        puts("c1: %.3f" % profile.c1())
        puts("c2: %.3f" % profile.c2())
        puts("c3: %.3f" % profile.c3())
        puts("c4: %.3f" % profile.c4())
        puts("c5: %.3f" % profile.c5())

    puts(colored.green('\n==o2 consensus (quality)'))
    consensus_o2 = ConsensusO2.run(profile)
    with indent(2, ''):
        for con in consensus_o2:
            puts("%s (%s)" % (con, profile.quality(con)))

    if show_profile:
        profile.show_fig(extra=consensus_o2)


if __name__ == '__main__':
    try:
        n = int(sys.argv[1])
    except:
        n = 5

    profile = EuclideanProfile(n)
    profile.generate(equal_dist=False)
    process_hypothesis(profile)
