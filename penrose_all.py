# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 13:36:09 2017

@author: breteau
"""


# from shapely.affinity import affine_transform
import numpy as np
from matplotlib import pyplot as plt
from math import pi

from sys import float_info

from fractions import Fraction
import fractions
import Image
from functools import partial

from multiprocessing import Pool, Process, Array, Lock, Queue, Pipe

import time
# import sympy

from libFlechesCerfsVolants import soleil_start, etoile_start, cut_fl, cut_cv
from libLosanges import figure_start, cut_GL, cut_pL
from libGeometry import get_view, subset_view, match_demis
from libDraw import draw_all, draw_all_mapped

itmax = 12
    
width = 1920 
height = 1080
offset = (height/2, width/2)

rotation = Fraction(pi / 3.0)

penrose_type = 3 #"fleches_cerfs-volants"
figure_depart = "soleil"

#rendu1 = {
#          "color": "7fbeff", # "#007fff"
#          "texturer": True,
#          "ect_texture": 20.0,
#          "teinte_aleatoire" : True,
#          "ect_teinte": 20.0,
##          "contours" : False,
##          "color_contours" : "003f77", # "#007fff"
#          }
#        
#rendu2 = {
#          "color" : "ffbf7f", # "#ff8000"
#          "texturer" : True,
#          "ect_texture": 10.0,
#          "teinte_aleatoire" : False,
#          "ect_teinte": None,
##          "contours" : False,
##          "color_contours" : "773f00", # "#007fff"
#          }

rendu1 = {
          "color": "0090fe", # "#007fff"
          "texturer": True,
          "ect_texture": 10.0,
          "teinte_aleatoire" : True,
          "ect_teinte": 20.0,
#          "contours" : False,
#          "color_contours" : "003f77", # "#007fff"
          }
        
rendu2 = {
          "color" : "7fbeff", # "#ff8000"
          "texturer" : True,
          "ect_texture": 10.0,
          "teinte_aleatoire" : True,
          "ect_teinte": 5.0,
#          "contours" : False,
#          "color_contours" : "773f00", # "#007fff"
          }
          
export_file = "./los.tif"


view_center = (Fraction(0.25), Fraction(0))
view_width = Fraction(0.5)

#view_center = (Fraction(0), Fraction(0))
#view_width = Fraction(20)
    

# tester test_match & concatenate_demiP OK
# rectangle view! OK
# selection des losanges dans la view uniquement OK
# tester les limites de l'égalité entre 2 pts OK (avec Fraction)
# rotation OK
# view_debug OK
# texturer la couleur, teintes differentes OK
# optimiser OK
# multiprocesser OK
# librairies OK

# bug : enregistrer image selon la view : BUG si centre non (0,0) ?

# todo : dessiner contours (retire)
# todo : valeurs réelles de alpha et phi sous forme de fraction

# todo : killer proprement les Process et Pool


if __name__ == "__main__":

    if penrose_type == 3: # "losanges":
        type1 = "gl"
        dtype1 = "dgl"
        type2 = "pl"
        dtype2 = "dpl"
                
    #    GL, pL = soleil_start(rotation)
        polys_1, polys_2 = figure_start(rotation) # Gros et petits losanges

    elif penrose_type == 2: #"fleches_cerfs-volants":
        type1 = "cv"
        dtype1 = "dcv"
        type2 = "fl"
        dtype2 = "dfl"
        
        cut_1 = cut_cv
        cut_2 = cut_fl
        
    #    GL, pL = soleil_start(rotation)
        if figure_depart == "soleil":
            polys_1, polys_2 = soleil_start(rotation) # cerfs-volants et fleches
        elif figure_depart == "etoile":
            polys_1, polys_2 = etoile_start(rotation) # cerfs-volants et fleches
        else:
            raise Exception("figure de départ invalide")
    
    else:
        raise Exception("penrose supportés de type 2 (fleches et cerfs volants) ou 3 (losanges)")
    
    view = get_view((width, height), view_center, view_width)

    I_shape = (3, height, width)
    I = np.zeros(I_shape, dtype=np.uint8)    

    draw_all_mapped(I, (width, height), view_center, view_width, rendu1, polys_1)
    draw_all_mapped(I, (width, height), view_center, view_width, rendu2, polys_2)

    im = Image.fromarray(I.swapaxes(0,1).swapaxes(1,2)).save("%s_start.tif" % (export_file))
        
    pool_cut = Pool(7)

#    global flag_reverse
    for it in xrange(1, itmax+1):
        print "iteration %d" % it
        if it%2 == 1:
            flag_reverse=False
        else:
            flag_reverse=True
        
        t0_it = time.time()
        
#        cutted_gl = [cut_GL(pp) for pp in GL]
#        cutted_pl = [cut_pL(pp) for pp in pL]
        
        if penrose_type == 3: # "losanges":
            cut_1 = partial(cut_GL, flag_reverse)
            cut_2 = partial(cut_pL, flag_reverse)

        try:
            cutted_1 = pool_cut.map(cut_1, polys_1)
            cutted_2 = pool_cut.map(cut_2, polys_2)
        
        except KeyboardInterrupt, e:
#            cutted_gl.terminate()
            pool_cut.terminate()
            import sys
            print e
            sys.exit(0)

        print "...cut : ", time.time() - t0_it
        
        t0 = time.time()

        try:
            news_1 = np.vstack([item[type1] for item in cutted_1 + cutted_2 if type1 in item.keys()])
        except ValueError: # tous vides
            news_1 = np.array([])
        
        try:
            news_2 = np.vstack([item[type2] for item in cutted_1 + cutted_2 if type2 in item.keys()])
        except ValueError: # tous vides
            news_2 = np.array([])

        try:
            news_demis_1 = np.vstack([item[dtype1] for item in cutted_1 + cutted_2 if dtype1 in item.keys()])
        except ValueError: # tous vides
            news_demis_1 = np.array([])

        try:
            news_demis_2 = np.vstack([item[dtype2] for item in cutted_1 + cutted_2 if dtype2 in item.keys()])
        except ValueError: # tous vides
            news_demis_2 = np.array([])

        print "...concatenate : ", time.time() - t0
        t0 = time.time()
        
        ### 2 PROCESS
#        p_conn_1, c_conn_1 = Pipe()
#        p_conn_2, c_conn_2 = Pipe()
#        p1 = Process(target=match_demis, args=(new_dpl, "pL", c_conn_1))
#        p1.start()
#        p2 = Process(target=match_demis, args=(new_dgl, "GL", c_conn_2))
#        p2.start()
#        pL = p_conn_1.recv()
#        p1.join()
#        GL = p_conn_2.recv()
#        p2.join()
        
        ### 1 PROCESS
        polys_1 = match_demis(news_demis_1)
        polys_2 = match_demis(news_demis_2)
        ###
        
        if len(news_1) == 0:
            news_1 = np.array(news_1).reshape((0, 4))
        if len(news_2) == 0:
            news_2 = np.array(news_2).reshape((0, 4))

        if len(polys_1) == 0:
            polys_1 = np.array(polys_1).reshape((0, 4))
        if len(polys_2) == 0:
            polys_2 = np.array(polys_2).reshape((0, 4))

        polys_1 = np.concatenate((news_1, polys_1))
        polys_2 = np.concatenate((news_2, polys_2))

#        import pdb; pdb.set_trace()

#        try:
#            GL = np.concatenate((new_gl, GL))
#        except ValueError, e:
#            if len(new_gl) == 0:
#                GL = GL
#            elif len(GL) == 0:
#                GL = new_gl
#            else:
#                raise e
               
        print "...match : ", time.time() - t0
        t0 = time.time()
        
        print float((polys_1[0][0] - polys_1[0][2]).sqr_norm()), float((polys_2[0][0] - polys_2[0][2]).sqr_norm()), float((polys_2[0][1] - polys_2[0][3]).sqr_norm())
        
        if penrose_type == 3: # "losanges":
            buffered_view = view.buffer(fractions.math.sqrt((polys_1[0][0] - polys_1[0][2]).sqr_norm())) # ajout d'un buffer pour pouvoir matcher les losanges en bordure
        elif penrose_type == 2: # "fleches_cerfs-volants":
            buffered_view = view.buffer(fractions.math.sqrt((polys_2[0][1] - polys_2[0][3]).sqr_norm())) # ajout d'un buffer pour pouvoir matcher les losanges en bordure
        else:
            raise Exception("penrose supportés de type 2 (fleches et cerfs volants) ou 3 (losanges)")
            
        
#            try:
#                buffered_view = view.buffer(fractions.math.sqrt((polys_1[0][0] - polys_1[0][2]).sqr_norm())) # ajout d'un buffer pour pouvoir matcher les losanges en bordure
#            except IndexError:
#                buffered_view = view.buffer(fractions.math.sqrt((polys_2[0][1] - polys_2[0][3]).sqr_norm())) # ajout d'un buffer pour pouvoir matcher les losanges en bordure

#        pL = subset_view(pL, buffered_view)
#        GL = subset_view(GL, buffered_view)
        
        p_conn_1, c_conn_1 = Pipe()
        p_conn_2, c_conn_2 = Pipe()
        try:
            p1 = Process(target=subset_view, args=(polys_1, buffered_view, c_conn_1))
            p1.start()
            p2 = Process(target=subset_view, args=(polys_2, buffered_view, c_conn_2))
            p2.start()
        except KeyboardInterrupt, e:
            p1.terminate()
            p2.terminate()
            print e
            import sys
            sys.exit(0)

        polys_1 = p_conn_1.recv()
        polys_2 = p_conn_2.recv()
        p1.join()
        p2.join()

        print "...subset : ", time.time() - t0
        t0 = time.time()

        I = np.zeros(I_shape, dtype=np.uint8)

        draw_all_mapped(I, (width, height), view_center, view_width, rendu1, polys_1)
        draw_all_mapped(I, (width, height), view_center, view_width, rendu2, polys_2)

        im = Image.fromarray(I.swapaxes(0,1).swapaxes(1,2)).save("%s_%d.tif" % (export_file, it))

        print "...draw : ", time.time() - t0
        
        print "total it %d : %f\n" % (it, time.time() - t0_it)
        
