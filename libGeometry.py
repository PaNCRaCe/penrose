# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:04:46 2017

@author: breteau
"""

import numpy as np
from fractions import Fraction
from shapely.geometry import Polygon as shapely_Polygon

from multiprocessing import Pool, Array, Lock
import ctypes
from functools import partial

# from shapely.geometry import Point as shapely_Point

class Vect(object):
    
    def __init__(self, coords):
        assert len(coords) == 2
        assert isinstance(coords[0], Fraction)
        assert isinstance(coords[1], Fraction)
        self.coords = coords
    
    def __str__(self):
        return "Vect(%.3f, %.3f)" % self.coords
        
    def __repr__(self):
        return self.__str__()

    def x(self):
        return self.coords[0]
        
    def y(self):
        return self.coords[1]
    
    def __mul__(self, coeff):
        
        assert isinstance(coeff, (int, Fraction))
        return Vect((coeff * self.x(),
                     coeff * self.y()))
                     
    def __rmul__(self, coeff):
        return self.__mul__(coeff)

    def __div__(self, num):
        
        assert isinstance(num, (int, Fraction))
        return Vect((self.x() / num,
                     self.y() / num))
        
    def __rdiv__(self, num):
        return self.__mul__(num)
    
    def sqr_norm(self):
        return np.power(self.coords, 2).sum()


class Pt(object):

    def __init__(self, coords):
        assert len(coords) == 2
        assert isinstance(coords[0], Fraction)
        assert isinstance(coords[1], Fraction)
        self.coords = coords

    def __str__(self):
        return "Pt(%.3f, %.3f)" % self.coords

    def __repr__(self):
        return self.__str__()

    def x(self):
        return self.coords[0]

    def y(self):
        return self.coords[1]

    def __add__(self, vec):
        """
        additionne un vecteur au point
        """
        
        assert type(vec) is Vect
            
        return Pt((self.x() + vec.x(),
                   self.y() + vec.y()))

    def __radd__(self, vec):
        """
        additionne un vecteur au point
        """
        
        return self.__add__(vec)

    def __sub__(self, opt):
        """
        retourne le vecteur pt - opt
        """
        assert type(opt) is Pt
        
        return Vect((self.x() - opt.x(),
                     self.y() - opt.y()))
                     
    def __rsub__(self, opt):
        """
        retourne le vecteur opt - pt
        """
        
        assert type(opt) is Pt
            
        return Vect((opt.x() - self.x(),
                     opt.y() - self.y()))

    def __eq__(self, other):
        return (self - other).sqr_norm() == 0
#        return (self - other).sqr_norm() < 1000.0 * float_info.epsilon

    def centre(self, other):
        return Pt([(x1+x2) / 2 for x1, x2 in zip(self.coords, other.coords)]) # division entiere car objets Fraction


def get_view(dims_pix, view_center, view_width, as_shapely_polygon=True):
    
    width, height = dims_pix
    dx = Fraction(view_width) / 2
    view_ratio = Fraction(width, height)
    dy = Fraction(view_width) / (2 * view_ratio)
    
    p0 = (Fraction(view_center[0]) - dx, Fraction(view_center[1]) - dy)
    p1 = (Fraction(view_center[0]) + dx, Fraction(view_center[1]) - dy)
    p2 = (Fraction(view_center[0]) + dx, Fraction(view_center[1]) + dy)
    p3 = (Fraction(view_center[0]) - dx, Fraction(view_center[1]) + dy)
    
    if as_shapely_polygon is True:
        return shapely_Polygon((p0, p1, p2, p3))
    else:
        return [p0, p1, p2, p3]


def subset_view(llist, view, pipe):

    pipe.send([los for los in llist if view.intersects(shapely_Polygon([pt.coords for pt in los]))])
    pipe.close()
    
#    return [los for los in llist if view.intersects(shapely_Polygon([pt.coords for pt in los]))] # 0.0838229656219 s a it 8
#    return [los for los in llist if np.any([view.contains(shapely_Point(pt.coords)) for pt in los])] # 0.163830041885 s a it 8
#    return [los for los in llist if np.any([shapely_Point(pt.coords).within(view)for pt in los])] # 0.173815011978 s a it 8


def test_match(dl1, dl2):
    return dl1[0] == dl2[0] and dl1[2] == dl2[2]


def concatenate_demiP(dl1, dl2):
    return [dl1[0], dl1[1], dl1[2], dl2[1]]
    
def _appariement_process(llist, N, i):
    try:
        if shared_arr[i] > -2: # shared_matched
            return
        for j in xrange(i+1, N):
            if shared_arr[j] > -2:
                continue
            if test_match(llist[i], llist[j]):
                lock.acquire()
                shared_arr[i] = j
                shared_arr[j] = -1
                lock.release()
                return
    except KeyboardInterrupt:
        return


def _initProcess(shared, lck):
    global shared_arr
    global lock
    
    shared_arr = shared
    lock = lck


def match_demis(llist):
    # it 5 : 0.364182949066
    # it 10 : 42.1131920815
    # it 12 : 1261.248471

    # avec 2 process it  5 : 0.341376066208
    #                it 10 : 43.2017059326
    #                it 12 : 1306.8952601
    
#    -2 : non traite / non apparie
#    -1 : apparie (esclave)
#    x >=0 : maitre apparie avec escalve x 
        
    N = llist.shape[0]

    shared_matched = Array(ctypes.c_int, [-2] * N)
    shared_matched = np.ctypeslib.as_array(shared_matched.get_obj())

    lock = Lock() # todo : retirer lock et lock = False?
    p = Pool(7, initializer=_initProcess, initargs=(shared_matched, lock))
    
    try:
        p.map(partial(_appariement_process, llist, N), xrange(N))
    except KeyboardInterrupt, e:
        p.terminate()
        import sys
        print e
        sys.exit(0)

    return [concatenate_demiP(llist[i], llist[j]) for i, j in enumerate(shared_matched) if j >= 0] # apparie les maitres avec les esclaves

