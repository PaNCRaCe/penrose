# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:08:35 2017

@author: breteau
"""

from fractions import Fraction  
from math import cos, sin, pi
from libGeometry import Pt
import numpy as np

alpha = Fraction(pi / 5.0)
phi = Fraction(2.0 * cos(alpha))
coeff_reduc = phi / (1 + phi)


def figure_start(rotation):
    
    P0 = Pt((Fraction(0), Fraction(0)))

    Points = [Pt((Fraction(phi * sin(i * alpha + rotation)), Fraction(phi * cos(i * alpha + rotation)))) for i in xrange(10)]

    GL = []
    pL = []
    for i in xrange(10):
        if i % 2 == 0:
            pL.append( [Points[i-1], P0, Points[i], (Points[i-1] - P0) + Points[i]] )
        else:
            pL.append( [Points[i], (Points[i-1] - P0) + Points[i], Points[i-1], P0]  )

    return GL, pL
    
    
def figure_start_demis(rotation):
    _, pL = figure_start(rotation)
    dGL = []
    dpL = np.vstack([[[item[0], item[1], item[2]], [item[0], item[3], item[2]]] for item in pL])
    
    return dGL, dpL
    
    
def cut_GL(reverse, Points):
    
    # decoupage normal    
    # gl = [Points[0], x1, x0, x2]
    # dgl_1 = [Points[3], x0, Points[2]]
    # dgl_2 = [Points[1], x0, Points[2]]
    # dpl_1 = [Points[1], x0, x1]
    # dpl_2 = [Points[3], x0, x2]
        
    # decoupage inverse
    # gl = [x0, x1, Points[2], x2]
    # dgl_1 = [Points[0], x0, Points[1]]
    # dgl_2 = [Points[0], x0, Points[3]]
    # dpl_1 = [Points[1], x0, x1]
    # dpl_2 = [Points[3], x0, x2]

    assert len(Points) == 4
    
    if reverse is False:
        
        x0 = coeff_reduc * (Points[2]-Points[0]) + Points[0]
        x1 = coeff_reduc * (Points[1]-Points[0]) + Points[0]
        x2 = coeff_reduc * (Points[3]-Points[0]) + Points[0]
        
        
        return {"gl" : [[Points[0], x1, x0, x2]],
                "dgl" : [[Points[3], x0, Points[2]],
                         [Points[1], x0, Points[2]]],
                "dpl" : [[Points[1], x0, x1],
                         [Points[3], x0, x2]]
                }
    else:
    
        x0 = coeff_reduc * (Points[0]-Points[2]) + Points[2]
        x1 = coeff_reduc * (Points[1]-Points[2]) + Points[2]
        x2 = coeff_reduc * (Points[3]-Points[2]) + Points[2]
        
        return {"gl" : [[x0, x1, Points[2], x2]],
                "dgl" : [[Points[0], x0, Points[1]],
                         [Points[0], x0, Points[3]]],
                "dpl" : [[Points[1], x0, x1],
                         [Points[3], x0, x2]]
                }

def cut_dGL(reverse, Points):

    assert len(Points) == 3
    
    if reverse is False:
        
        x0 = coeff_reduc * (Points[2]-Points[0]) + Points[0]
        x1 = coeff_reduc * (Points[1]-Points[0]) + Points[0]
        
        
        return {"dgl" : [[Points[0], x1, x0],
                         [Points[1], x0, Points[2]]],
                "dpl" : [[Points[1], x0, x1]]
                }
    else:
    
        x0 = coeff_reduc * (Points[0]-Points[2]) + Points[2]
        x1 = coeff_reduc * (Points[1]-Points[2]) + Points[2]
        
        return {"dgl" : [[x0, x1, Points[2]],
                        [Points[0], x0, Points[1]]],
                "dpl" : [[Points[1], x0, x1]]
                }

def cut_pL(reverse, Points):

    # demi petits losanges
    #    dpl_1 = [Points[2], Points[0], x1]
    #    dpl_2 = [Points[2], Points[0], x2]
    # demi gros losanges, decoupage normal
    #    dgl_1 = [Points[1], x1, Points[0]]
    #    dgl_2 = [Points[3], x2, Points[0]]
    # demi gros losanges, decoupage inverse
    #    dgl_1 = [Points[0], x1, Points[1]]
    #    dgl_2 = [Points[0], x2, Points[3]]
    #    return {"dgl": [dgl_1, dgl_2], "dpl": [dpl_1, dpl_2]}

    assert len(Points) == 4

    x1 = coeff_reduc * (Points[2] - Points[1]) + Points[1]
    x2 = coeff_reduc * (Points[2] - Points[3]) + Points[3]
       
    if reverse is False:
        return {"dpl" : [[Points[2], Points[0], x1],
                         [Points[2], Points[0], x2]],
                "dgl" : [[Points[1], x1, Points[0]],
                         [Points[3], x2, Points[0]]]
                }
    else:
        return {"dpl" : [[Points[2], Points[0], x1],
                         [Points[2], Points[0], x2]],
                "dgl" : [[Points[0], x1, Points[1]],
                         [Points[0], x2, Points[3]]]
                }
    
def cut_dpL(reverse, Points):

    assert len(Points) == 3

    x1 = coeff_reduc * (Points[2] - Points[1]) + Points[1]
       
    if reverse is False:
        return {"dpl" : [[Points[2], Points[0], x1]],
                "dgl" : [[Points[1], x1, Points[0]]]
                }
    else:
        return {"dpl" : [[Points[2], Points[0], x1]],
                "dgl" : [[Points[0], x1, Points[1]]]
                }
