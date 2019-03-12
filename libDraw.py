# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:10:42 2017

@author: breteau
"""

import numpy as np
from fractions import Fraction
from skimage.draw import polygon
# from skimage.draw import polygon_perimeter

from libGeometry import get_view

from multiprocessing import Pool, Array, Lock

from functools import partial
import ctypes


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def draw_polygon(los, I_shape, view_coords, dims_pix, view_width, return_contour=False):

    p0 = view_coords[0]
    width, height = dims_pix
    view_ratio = Fraction(width, height)
    cc = np.array([pt.coords for pt in los]).T
#    if return_contour:
#        return [polygon((cc[1] - p0[1]) * height * view_ratio / view_width,
#                        (cc[0] - p0[0]) * width / view_width,
#                        shape = I_shape[-2:]),
#                polygon_perimeter((cc[1] - p0[1]) * height * view_ratio / view_width,
#                                  (cc[0] - p0[0]) * width / view_width,
#                                   shape = I_shape[-2:])]
#    else:
    return polygon((cc[1] - p0[1]) * height * view_ratio / view_width,
                   (cc[0] - p0[0]) * width / view_width,
                   shape=I_shape[-2:])


def draw_all(I_ref, dims_pix, view_center, view_width, rendu, llist):

    I_shape = I_ref.shape

    view_coords = get_view(dims_pix, view_center, view_width, as_shapely_polygon=False)
    
    I = I_ref.astype(np.float)

    col = hex_to_rgb(rendu["color"])
    for los in llist:

        poly = draw_polygon(los, I_shape[-2:], view_coords, dims_pix, view_width)
            
        for can, cc in zip(I, col):
            can[poly] = cc
            if rendu["teinte_aleatoire"]:
                can[poly] += rendu["ect_teinte"] * np.random.standard_normal()
            if rendu["texturer"]:
                can[poly] += rendu["ect_texture"] * np.random.standard_normal(poly[0].size)
        
#        if rendu["contours"]:
#            cc1 = hex_to_rgb(rendu["color_contours"])
#            for can, cc in zip(I, cc1):
#                can[contour] = cc

    I[I < 0] = 0
    I[I > 255] = 255
    I_ref[:] = I.astype(I.dtype)[:]


def _single_draw_process(rendu, col, view_coords, dims_pix, view_width, los):
    
    try:
        I_shape = shared_arr.shape
        
    #    if rendu["contours"]:
    #        poly, contour = draw_polygon(los, I_shape[-2:], view_coords, True)
    #    else:
    #        print "ici0"
        poly = draw_polygon(los, I_shape[-2:], view_coords, dims_pix, view_width)
        
        for can, cc in zip(shared_arr, col):
            can[poly] = cc
            if rendu["teinte_aleatoire"]:
                ecart_aleatoire = rendu["ect_teinte"] * np.random.standard_normal()
            else:
                ecart_aleatoire = 0
    
            if rendu["texturer"]:
                bruit = rendu["ect_texture"] * np.random.standard_normal(poly[0].size)
            else:
                bruit = 0
        
            lock.acquire()    
            can[poly] += ecart_aleatoire + bruit
            lock.release()
    except KeyboardInterrupt:
        return
        
   
#    if rendu["contours"]:
#        cc1 = hex_to_rgb(rendu["color_contours"])
#        for can, cc in zip(I, cc1):
#            can[contour] = cc


def _initProcess(shared, lck):
    global shared_arr
    global lock
    
    shared_arr = shared
    lock = lck
    
def draw_all_mapped(I_ref, dims_pix, view_center, view_width, rendu, llist):
    
#    I_shape = I_ref.shape

    view_coords = get_view(dims_pix, view_center, view_width, as_shapely_polygon=False)
    
    I = I_ref.astype(np.float)
    
#    GL -> llist
#    c1 -> col
#    gl -> los
#    rendu1 -> rendu
    
    shared_I = Array(ctypes.c_float, I.flatten())
    shared_I = np.ctypeslib.as_array(shared_I.get_obj()).reshape(I.shape)
    
    lock = Lock() # todo : retirer lock et lock = False?
    p = Pool(1, initializer=_initProcess, initargs=(shared_I, lock))
    
    col = hex_to_rgb(rendu["color"])
    p.map(partial(_single_draw_process, rendu, col, view_coords, dims_pix, view_width), llist)

    shared_I[shared_I < 0] = 0
    shared_I[shared_I > 255] = 255
    I_ref[:] = shared_I.astype(I_ref.dtype)[:]

