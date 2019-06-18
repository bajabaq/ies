
import pytest

import ConfigParser
import os

from .. import hvac_math

def test_round_val():
    assert hvac_math.round_val(0,5) == 0
    assert hvac_math.round_val(1,5) == 0
    assert hvac_math.round_val(2,5) == 0
    assert hvac_math.round_val(3,5) == 5
    assert hvac_math.round_val(4,5) == 5
    assert hvac_math.round_val(5,5) == 5
    

#------------------------------------------------------------------------------
# round ctd down if diff between ctd and low_val <=1
#           up   if diff > 1
#------------------------------------------------------------------------------
def test_round_ctd():
    assert hvac_math.round_ctd(20) == 20
    assert hvac_math.round_ctd(21) == 20
    assert hvac_math.round_ctd(22) == 25
    assert hvac_math.round_ctd(23) == 25
    assert hvac_math.round_ctd(24) == 25
    assert hvac_math.round_ctd(25) == 25


def test_interpolate_val():
    assert hvac_math.interpolate_val(2, 0, 2, 0, 1) == 1.0
    assert hvac_math.interpolate_val(0, 2, 0, 2, 1) == 1.0
    
def test_extrapolate_val():          #y2,y1,x2,x1,x
    assert hvac_math.extrapolate_val(2,1,2,1,0) == 0.0
    assert hvac_math.extrapolate_val(2,1,2,1,3) == 3.0
    assert hvac_math.extrapolate_val(1,2,2,1,3) == 0.0
    assert hvac_math.extrapolate_val(1,2,2,1,0) == 3.0
    assert hvac_math.extrapolate_val(0.9,1,1000,0,-500) == 1.05