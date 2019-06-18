
import pytest

import ConfigParser
import os

from .. import ies_light_calc

def get_settings():
    #read the system settings file (maybe should be in own module - along w/ get_database name)
    settings      = ConfigParser.SafeConfigParser()
    settings_file = os.path.abspath('../system_settings.txt')    
    settings.read(settings_file)    
    return settings

def test_calc_cavity_ratio():
    #                                       perim, area, height
    assert ies_light_calc.calc_cavity_ratio(   4,     1,    1) == 10
    assert ies_light_calc.calc_cavity_ratio(  40,   100,   10) == 10
    assert ies_light_calc.calc_cavity_ratio(  32,    64,    1) == 1.25
    assert ies_light_calc.calc_cavity_ratio(  32,    64,   10) == 12.5
    assert ies_light_calc.calc_cavity_ratio( 2000,250000,  30) == 0.6
    lroom = 25.5
    wroom = 26.5
    area  = lroom * wroom     #675.5
    perim = lroom*2 + wroom*2 #104.0
    assert ies_light_calc.calc_cavity_ratio( perim, area, 0.25) == 0.10
    assert ies_light_calc.calc_cavity_ratio( perim, area, 5.25) == 2.02
    assert ies_light_calc.calc_cavity_ratio( perim, area, 2.50) == 0.96
    
def test_get_effective_base_refl():
    settings = get_settings()
    #                                                      surf,wall,surfCR
    assert ies_light_calc.get_effective_base_refl(settings, 80, 40, 10)   == 18 #ceiling
    assert ies_light_calc.get_effective_base_refl(settings, 20, 40, 10)   == 10 #floor

    #limits
    assert ies_light_calc.get_effective_base_refl(settings, 40, 90,0.2)   == 40
    assert ies_light_calc.get_effective_base_refl(settings, 22, 54, 2.1)  == 20 #made up
    assert ies_light_calc.get_effective_base_refl(settings,  0,  0, 10)   == 0 
    assert ies_light_calc.get_effective_base_refl(settings, 90, 90,0.2)   == 89
    assert ies_light_calc.get_effective_base_refl(settings, 72, 54, 2.2)  == 50.48 #made up
    assert ies_light_calc.get_effective_base_refl(settings, 50,  0, 10)   == 2 

    #some examples
    assert ies_light_calc.get_effective_base_refl(settings, 50,  93, 0)  == 49.7 #ceil light color paint/wall fundamental white lrv93
    assert ies_light_calc.get_effective_base_refl(settings, 50,  89, 0)  == 50.1 #ceil light color paint/wall white gallery lrv89
    assert ies_light_calc.get_effective_base_refl(settings, 50,  86, 0)  == 50.4 #ceil light color paint/wall oxford white lrv86
    assert ies_light_calc.get_effective_base_refl(settings, 50,  47, 0)  == 49.3 #ceil light color paint/wall familiar beige lrv47
    assert ies_light_calc.get_effective_base_refl(settings, 50,  32, 0)  == 49.2 #ceil light color paint/wall nor'eastert lrv32
    assert ies_light_calc.get_effective_base_refl(settings, 50,   3, 0)  == 46.6 #ceil light color paint/wall tricorn black lrv3

    assert ies_light_calc.get_effective_base_refl(settings, 50,  93, 1)  == 50.6 #ceil light color paint/wall fundamental white lrv93
    assert ies_light_calc.get_effective_base_refl(settings, 50,  89, 1)  == 49.8 #ceil light color paint/wall white gallery lrv89
    assert ies_light_calc.get_effective_base_refl(settings, 50,  86, 1)  == 49.2 #ceil light color paint/wall oxford white lrv86
    assert ies_light_calc.get_effective_base_refl(settings, 50,  47, 1)  == 42.4 #ceil light color paint/wall familiar beige lrv47
    assert ies_light_calc.get_effective_base_refl(settings, 50,  32, 1)  == 38.6 #ceil light color paint/wall nor'eastert lrv32
    assert ies_light_calc.get_effective_base_refl(settings, 50,   3, 1)  == 34.6 #ceil light color paint/wall tricorn black lrv3

    assert ies_light_calc.get_effective_base_refl(settings, 50,  93, 10) == 50.0 #ceil light color paint/wall fundamental white lrv93
    assert ies_light_calc.get_effective_base_refl(settings, 50,  89, 10) == 46.0 #ceil light color paint/wall white gallery lrv89
    assert ies_light_calc.get_effective_base_refl(settings, 50,  86, 10) == 43.0 #ceil light color paint/wall oxford white lrv86
    assert ies_light_calc.get_effective_base_refl(settings, 50,  47, 10) == 16.1 #ceil light color paint/wall familiar beige lrv47
    assert ies_light_calc.get_effective_base_refl(settings, 50,  32, 10) == 10.8 #ceil light color paint/wall nor'eastert lrv32
    assert ies_light_calc.get_effective_base_refl(settings, 50,   3, 10) == 3.2 #ceil light color paint/wall tricorn black lrv3

    assert ies_light_calc.get_effective_base_refl(settings, 93,  47, 10) == 21.4 #ceil fundamental white lrv 93 /wall familiar beige lrv47 
    assert ies_light_calc.get_effective_base_refl(settings, 89,  47, 10) == 21.0 #ceil white gallery lrv 89 /wall familiar beige lrv47 
    assert ies_light_calc.get_effective_base_refl(settings, 93,  47,  1) == 76.41 #ceil fundamental white lrv 93 /wall familiar beige lrv47 
    assert ies_light_calc.get_effective_base_refl(settings, 89,  47,  1) == 73.33 #ceil white gallery lrv 89 /wall familiar beige lrv47 
    assert ies_light_calc.get_effective_base_refl(settings, 93,  47,  0) == 90.1 #ceil fundamental white lrv 93 /wall familiar beige lrv47 
    assert ies_light_calc.get_effective_base_refl(settings, 89,  47,  0) == 86.9 #ceil white gallery lrv 89 /wall familiar beige lrv47 

    #example
    assert ies_light_calc.get_effective_base_refl(settings, 70, 50, 0.1)  == 68 #ceil
    assert ies_light_calc.get_effective_base_refl(settings, 50, 50,    0) == 49  #wall - this should probably be 50
    assert ies_light_calc.get_effective_base_refl(settings,  0, 50, 0.96) == 4  #floor

def test_get_luminaire_dirt_dep():
    settings = get_settings()
    #                                                      id, time,   dirt
    assert ies_light_calc.get_luminaire_dirt_dep(settings,  1,   3, 'very_clean')  == 0.87
    assert ies_light_calc.get_luminaire_dirt_dep(settings,  1,   3,      'clean')  == 0.80
    assert ies_light_calc.get_luminaire_dirt_dep(settings,  1,   3,     'medium')  == 0.71
    assert ies_light_calc.get_luminaire_dirt_dep(settings,  1,   3,      'dirty')  == 0.64
    assert ies_light_calc.get_luminaire_dirt_dep(settings,  1,   3, 'very_dirty')  == 0.56
    assert ies_light_calc.get_luminaire_dirt_dep(settings, 38, 2.0,     'medium')  == 0.76 #0.77 reported, 0.76 is correct

def test_get_rsdd():
    settings = get_settings()
    #                                        id, time,    dirt,   RCR
    assert ies_light_calc.get_rsdd(settings,  1, 0.5,      'clean', 10.00) == 0.97
    assert ies_light_calc.get_rsdd(settings, 38, 2.0, 'very_clean',  2.02) == 0.98
    assert ies_light_calc.get_rsdd(settings, 38, 2.0,      'clean',  2.02) == 0.97
    assert ies_light_calc.get_rsdd(settings, 38, 2.0,     'medium',  2.02) == 0.95 #this is the example
    assert ies_light_calc.get_rsdd(settings, 38, 2.0,      'dirty',  2.02) == 0.94
    assert ies_light_calc.get_rsdd(settings, 38, 2.0, 'very_dirty',  2.02) == 0.93


def test_get_floor_mf():
    settings = get_settings()
                                     #(settings, ceil_ref, floor_ref, wall, RCR):
    assert ies_light_calc.get_floor_mf(settings, 80, 20, 70,  1.00) == 1.000
    assert ies_light_calc.get_floor_mf(settings, 10, 20, 10, 10.00) == 1.000
    assert ies_light_calc.get_floor_mf(settings, 80, 30, 70,  1.00) == 1.092
    assert ies_light_calc.get_floor_mf(settings, 10, 30, 10, 10.00) == 1.002
    assert ies_light_calc.get_floor_mf(settings, 80, 10, 70,  1.00) == 0.923
    assert ies_light_calc.get_floor_mf(settings, 10, 10, 10, 10.00) == 0.999
    assert ies_light_calc.get_floor_mf(settings, 80,  0, 70,  1.00) == 0.859
    assert ies_light_calc.get_floor_mf(settings, 10,  0, 10, 10.00) == 0.999
    assert ies_light_calc.get_floor_mf(settings, 80, 20, 50, 10.00) == 1.000
    assert ies_light_calc.get_floor_mf(settings, 68,  4, 50,  2.02) == 0.923 #example says 0.90    

    assert ies_light_calc.get_floor_mf(settings, 50,  11, 70,  5.09) == 0.970    

def test_get_coeff_util():
    settings = get_settings()
    assert ies_light_calc.get_coeff_util(settings, 1, 68, 50, 2.02) == 0.55  #example says 0.56

    
def test_get_num_luminaires():
    settings = get_settings()
    assert ies_light_calc.get_num_luminaires(settings, 50, 25.5, 26.5, 4*3150, 0.56, 0.9, 0.85, 0.77, 0.95) == 9  #example is wrong 8.3=8 (we calc 8.6=9)
    
def test_get_max_spacing():
    settings = get_settings()    
    assert ies_light_calc.get_max_spacing(settings, 1, 2.02) == [3,0]
