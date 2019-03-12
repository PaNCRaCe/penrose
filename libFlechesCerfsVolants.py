# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:08:35 2017

@author: breteau
"""

from fractions import Fraction  
from math import cos, sin, pi
from libGeometry import Pt
import numpy as np
from multiprocessing import Pool, Array, Lock
import ctypes
from functools import partial

alpha = Fraction(pi / 5.0)
phi = Fraction(2.0 * cos(alpha))
coeff_reduc = phi / (1 + phi)

def soleil_start(rotation):
    
#    if (depart == "soleil"):
#        n_cv = 5
#        n_f  = 0
#        dirs = np.arange(0, n_cv)
#        S_cv = np.zeros((2, n_cv))
#        C_cv = np.zeros((2, n_cv))
#        C_cv[0] = np.cos(angle * (1 + 2 * dirs))
#        C_cv[1] = np.sin(angle * (1 + 2 * dirs))
#        S_f = C_f = np.zeros((2, 0))
    
    P0 = Pt((Fraction(0), Fraction(0)))

    Points = [Pt((Fraction(phi * sin(i * alpha + rotation)), Fraction(phi * cos(i * alpha + rotation)))) for i in xrange(10)]

    CV = []
    fl = []
    for i in xrange(5):
            CV.append( [P0, Points[2*i+1], Points[2*i], Points[2*i-1]]  )

    return CV, fl


def etoile_start(rotation):
    
#    elif (depart == "etoile"):
#        n_cv = 0
#        n_f  = 5
#        dirs = np.arange(0, n_f)
#        S_f = C_f = np.zeros((2, n_cv))
#        C_f[0] = np.cos(angle * (1 + 2 * dirs))
#        C_f[1] = np.sin(angle * (1 + 2 * dirs))
#        S_cv = C_cv = np.zeros((2, 0))
    
    P0 = Pt((Fraction(0), Fraction(0)))

    Points = [Pt((Fraction(phi * sin(i * alpha + rotation)), Fraction(phi * cos(i * alpha + rotation)))) for i in xrange(10)]
    Points2 = [Pt((Fraction(sin(i * alpha + rotation)), Fraction(cos(i * alpha + rotation)))) for i in xrange(10)]

    CV = []
    fl = []
    for i in xrange(5):
            fl.append( [P0, Points[2*i+1], Points2[2*i], Points[2*i-1]]  )

    return CV, fl


def soleil_start_demis(rotation):
    CV, _ = soleil_start(rotation)
    dcv = np.vstack([[[item[0], item[1], item[2]], [item[0], item[3], item[2]]] for item in CV])
#    dfl = np.vstack([[[item[0], item[1], item[2]], [item[0], item[3], item[2]]] for item in fl])
    dfl = []
    return dcv, dfl


def etoile_start_demis(rotation):
    _, fl = etoile_start(rotation)
    dcv = [] # np.vstack([[[item[0], item[1], item[2]], [item[0], item[3], item[2]]] for item in CV])
    dfl = np.vstack([[[item[0], item[1], item[2]], [item[0], item[3], item[2]]] for item in fl])
    return dcv, dfl
    
    
def cut_fl(Points): #reverse, 


    assert len(Points) == 4
    
    x1 = coeff_reduc * (Points[1]-Points[0]) + Points[0]
    x3 = coeff_reduc * (Points[3]-Points[0]) + Points[0]
    
    
    return {"cv" :  [[Points[0], x1, Points[2], x3]],
            "dfl" : [[Points[1], Points[2], x1],
                     [Points[3], Points[2], x3]]
            }


def cut_dfl(Points):
    
    assert len(Points) == 3
    
    x1 = coeff_reduc * (Points[1]-Points[0]) + Points[0]
    
    
    return {"dcv" :  [[Points[0], x1, Points[2]]],
            "dfl" : [[Points[1], Points[2], x1]]
            }


def cut_cv(Points): # reverse, 


    assert len(Points) == 4

    x1 = coeff_reduc * (Points[0] - Points[1]) + Points[1]
    x2 = coeff_reduc * (Points[2] - Points[0]) + Points[0]
    x3 = coeff_reduc * (Points[0] - Points[3]) + Points[3]

    return {"cv" :  [[Points[1], Points[2], x2, x1],
                     [Points[3], x3, x2, Points[2]]],
            "dfl" : [[Points[0], x2, x1],
                     [Points[0], x2, x3]]
            }

def cut_dcv(Points):
    
    assert len(Points) == 3

    x1 = coeff_reduc * (Points[0] - Points[1]) + Points[1]
    x2 = coeff_reduc * (Points[2] - Points[0]) + Points[0]
#    x3 = coeff_reduc * (Points[0] - Points[3]) + Points[3]

    return {"dcv" :  [[Points[1], Points[2], x2],
                      [Points[1], x1, x2]],
            "dfl" : [[Points[0], x2, x1]]
            }


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


def match_demis(llist, p_type):
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

