#!/usr/bin/python

#------------------------------------------------------------------
# Program to calculate lamps needed for space
# based on IES procedure
#------------------------------------------------------------------
import os
import sys
import math
import ConfigParser

from hvac_database import get_db_filename, do_query
from hvac_math     import interpolate_val, extrapolate_val, mean

#------------------------------------------------------------------------------
# calc the cavity ratio 
#------------------------------------------------------------------------------
def calc_cavity_ratio(r_perimeter, r_area, cav_height):
    cr = 2.5 * cav_height * (r_perimeter)/(r_area)
    cr = float('{0:.2f}'.format(cr))
    return cr
#enddef                                            

#------------------------------------------------------------------------------
# lookup table 9-11
#settings, reflectance base, reflectance walls, base cavity ratio
#------------------------------------------------------------------------------
def get_effective_base_refl(settings, pB, pW, BCR):
    print "Using: pB:" + str(pB) + " pW:" + str(pW) + " BCR:"+ str(BCR) 
    peff = interpolate_three(settings,'eff_base_refl','eff_base_refl','base',pB,'wall',pW,'cavity_ratio',BCR)
    peff = float('{0:.2f}'.format(peff))
#    print peff   
    return peff
#enddef

#------------------------------------------------------------------------------
# lookup table 9-12
#------------------------------------------------------------------------------
def get_coeff_util(settings, luminaire_id, eff_ceil, refl_wall, room_CR):
    cu = interpolate_three(settings, 'coef_util','cu','eff_ceil',eff_ceil,'wall',refl_wall,'cavity_ratio',room_CR,'luminaire_id',luminaire_id)
    cu = float('{0:.2f}'.format(cu))
    return cu
#enddef

#------------------------------------------------------------------------------
# get type of lighting (direct, semi-direct, general-diffuse, direct-indirect, semi-indirect, indirect)
#------------------------------------------------------------------------------
def get_lighting_type(settings, luminaire_id):
    SQL = """SELECT percent_lumens_up,percent_lumens_down FROM luminaire_info WHERE luminaire_id = ?"""    
    SQL_vars = (luminaire_id,)
    results  = do_query(settings, SQL, SQL_vars)

    if len(results) < 1:
        msg = "ERROR - description not found for " + luminaire_id
        exit()
    else:
        (up,down,) = results[0]
    #endif

    if up + down != 100:
        both = (up + down)
        up   = 100 * up/both
        down = 100 * down/both
    #endif

    lighting_type = ""
    if(90 <= down <= 100 or 0 <= up <= 10):
        lighting_type = "direct"
    elif(60 <= down <= 90 or 10 <= up <= 40):
        lighting_type = "semi-direct"
    elif(40 <= down <= 60 or 40 <= up <= 60):
        lighting_type = "general-diffuse"
#    elif(40 <= down <= 60 or 40 <= up <= 60): #special (non-CIE) cat within the classification see 10-12
#        lighting_type = "direct-indirect"
    elif(10 <= down <= 40 or 60 <= up <= 90):
        lighting_type = "semi-indirect"
    elif(0 <= down <= 10 or 90 <= up <= 100):
        lighting_type = "indirect"
    
    return lighting_type
#enddef

#------------------------------------------------------------------------------
# get the description of the luminaire (found in the IES Lighting Handbook Fig. 9-12
# this code may be able to be combined with get_max_s_h or templated...
#------------------------------------------------------------------------------
def get_luminaire_description(settings, luminaire_id):
    SQL = """SELECT description FROM luminaire_info WHERE luminaire_id = ?"""    
    SQL_vars = (luminaire_id,)
    results  = do_query(settings, SQL, SQL_vars)                

    description = ""
    if len(results) < 1:
        msg = "ERROR - description not found for " + luminaire_id
        exit()
    else:
        (description,) = results[0]
    #endif
    
    return description
#enddef
    

#------------------------------------------------------------------------------
# lamp spacing
#------------------------------------------------------------------------------
def get_max_s_h(settings, luminaire_id):
    SQL = """SELECT max_s_mh FROM luminaire_info WHERE luminaire_id = ?"""
    SQL_vars = (luminaire_id,)
    results  = do_query(settings, SQL, SQL_vars)                

    max_s_mh = 1    
    if len(results) < 1:
        msg = "ERROR - max_s_mh not found for " + luminaire_id
        exit()
    else:
        (max_s_mh,) = results[0]
    #endif
    
    return max_s_mh
#enddef

#------------------------------------------------------------------------------
# calc LDD, from fig 9-6 data 1981 ies lighting handbook
#------------------------------------------------------------------------------
def get_ldd_consts(settings, luminaire_id, dirtiness):
    SQL      = """SELECT a, b FROM luminaire_info INNER JOIN ldd ON luminaire_info.maint_cat = ldd.maint_cat WHERE luminaire_id = ? AND dirtiness = ?"""
    SQL_vars = (luminaire_id, dirtiness,)
    results  = do_query(settings, SQL, SQL_vars)                

    A = 1
    B = 1

    if len(results) < 1:
        msg = "ERROR - ldd constants not found for luminaire id" + luminaire_id
        exit()
    else:
        (A,B) = results[0]
    #endif

    return [A,B]
#enddef

#------------------------------------------------------------------------------
# calc LDD - an exponential decay describing how fast dirt deposits on surface of luminaire
#------------------------------------------------------------------------------
def get_luminaire_dirt_dep(settings, luminaire_id, time, dirtiness):
    [A, B] = get_ldd_consts(settings, luminaire_id, dirtiness)
    LDD = math.exp(-A * time**B)
    LDD = float('{0:.2f}'.format(LDD))

    debug = settings.getboolean('system','debug')
    if debug == True:
        print "LDD constant A: " + str(A)
        print "LDD constant B: " + str(B)
        print "LDD:            " + str(LDD)
    #endif
       
    return LDD
#enddef

#------------------------------------------------------------------------------
# parse the results of the query, return crazy numbers if no result is found
#------------------------------------------------------------------------------
def get_n_results(results, numres):    
    result   = 999999
    nresults = []
    if not results:
        nresults = [result]*numres
    else:
        tnresults = results[:numres]
        while len(tnresults) < numres:
            tnresults.append((result,)) #format so same as incoming
        #endwhile
        for r in tnresults: #fix so output is single list
            (res,) = r
            nresults.append(res)
        #endfor
    #endif

    return nresults
#enddef
def get_result(results, sub):    
    if not results:
        result = 999999
        
        #if sub == "get_rsdd_aux":
        #    result = 1
        #else:
        #    result = 999
        #endif
    else:
        (result,) = results[0]
    #endif

    return result
#enddef

#what happens if col_val > max col or col_val < min col?
#it should get the two previous ones
def get_ends(settings, table, col, col_val, col2='', col2_val=''):
    SQL_vars = (col_val,)
    #get hi
    if col2 == '':
        SQL = """SELECT DISTINCT {col} FROM {table} WHERE {col} >= ? ORDER BY {col} ASC;"""
        SQL = SQL.format(col=col,table=table)
    else:
        SQL = """SELECT DISTINCT {col} FROM {table} WHERE {col} >= ? AND {col2} = {col2_val} ORDER BY {col} ASC;"""
        SQL = SQL.format(col=col,table=table,col2=col2,col2_val=col2_val)        
    #endif

    results  = do_query(settings, SQL, SQL_vars)
    #print "*" * 22

    #print col_val
    #print SQL
    #print results

    [hi_col1, hi_col2]  = get_n_results(results,2)
    hi_col = hi_col1

    #get low
    if col2 == '':
        SQL = """SELECT DISTINCT {col} FROM {table} WHERE {col} <= ? ORDER BY {col} DESC;"""
        SQL = SQL.format(col=col,table=table)
    else:
        SQL = """SELECT DISTINCT {col} FROM {table} WHERE {col} <= ? AND {col2} = {col2_val} ORDER BY {col} DESC;"""
        SQL = SQL.format(col=col,table=table,col2=col2,col2_val=col2_val)        
    #endif
    results = do_query(settings, SQL, SQL_vars)
    #print results
    [low_col1, low_col2] = get_n_results(results,2)
    low_col = low_col1

    #print hi_col2, hi_col1, col_val, low_col1, low_col2
    #print "*" * 22
    
    if hi_col1 == 999999:
        hi_col  = low_col1
        low_col = low_col2
    elif low_col1 == 999999:
        hi_col  = hi_col2
        low_col = hi_col1
    #endif    
    return [hi_col, low_col]
#enddef

#interpolate 3 variables (A, B, C, looking for D)
def interpolate_three_get_d(settings, SQL,col1_val,col2_val,col3_val,col4_val):
    if col4_val == '':
        SQL_vars = (col1_val, col2_val, col3_val)
    else:
        SQL_vars = (col1_val,col2_val,col3_val,col4_val)
    #endif
    results  = do_query(settings, SQL, SQL_vars)
    [d] = get_n_results(results,1)
    return d
#enddef

def interpolate_three(settings,table,res_col,col1,col1_val,col2,col2_val,col3,col3_val,col4='',col4_val=''):
    #A
    [hi_col1, low_col1] = get_ends(settings, table, col1, col1_val)
    #B
    [hi_col2, low_col2] = get_ends(settings, table, col2, col2_val)
    #C
    [hi_col3, low_col3] = get_ends(settings, table, col3, col3_val)
    #E
    #[hi_col4, low_col4] = get_ends(settings, table, col4, col4_val)
    
    debug = settings.getboolean('system','debug')
    if debug == True:
        print table
        print hi_col1, low_col1
        print hi_col2, low_col2
        print hi_col3, low_col3
#        print hi_col4, low_col4
    #endif
    
    #get Ds to interpolate
    if col4 == '':
        SQL = """SELECT {res_col} FROM {table} WHERE {col1} = ? AND {col2} = ? AND {col3} = ?"""
        SQL = SQL.format(res_col=res_col,table=table,col1=col1,col2=col2,col3=col3)
    else:
        SQL = """SELECT {res_col} FROM {table} WHERE {col1} = ? AND {col2} = ? AND {col3} = ? AND {col4} = ?"""
        SQL = SQL.format(res_col=res_col,table=table,col1=col1,col2=col2,col3=col3,col4=col4)        
    #endif

    hihihi   = interpolate_three_get_d(settings, SQL,hi_col1,hi_col2,hi_col3,col4_val)
    hihilow  = interpolate_three_get_d(settings, SQL,hi_col1,hi_col2,low_col3,col4_val)
    hilowhi  = interpolate_three_get_d(settings, SQL,hi_col1,low_col2,hi_col3,col4_val)
    hilowlow = interpolate_three_get_d(settings, SQL,hi_col1,low_col2,low_col3,col4_val)
    hilowhi  = interpolate_three_get_d(settings, SQL,hi_col1,low_col2,hi_col3,col4_val)
    lowhihi  = interpolate_three_get_d(settings, SQL,low_col1,hi_col2,hi_col3,col4_val)
    lowhilow = interpolate_three_get_d(settings, SQL,low_col1,hi_col2,low_col3,col4_val)
    lowlowhi = interpolate_three_get_d(settings, SQL,low_col1,low_col2,hi_col3,col4_val)
    lowlowlow= interpolate_three_get_d(settings, SQL,low_col1,low_col2,low_col3,col4_val)

    if debug == True:
        print hihihi
        print hihilow
        print hilowhi
        print hilowlow
        print lowhihi
        print lowhilow
        print lowlowhi
        print lowlowlow
        print "-" * 11
    
    #use C to interpolate D's
    hi_hi_c   = extrapolate_val(hihihi,hihilow,hi_col3,low_col3,col3_val)
    hi_low_c  = extrapolate_val(hilowhi,hilowlow,hi_col3,low_col3,col3_val)
    low_hi_c  = extrapolate_val(lowhihi,lowhilow,hi_col3,low_col3,col3_val)
    low_low_c = extrapolate_val(lowlowhi,lowlowlow,hi_col3,low_col3,col3_val)

    if debug == True:
        print hi_hi_c
        print hi_low_c
        print low_hi_c
        print low_low_c
        print "-" * 11
    
    #use B to interpolate interpolated D's
    hi_b  = extrapolate_val(hi_hi_c,hi_low_c,hi_col2,low_col2,col2_val)
    low_b = extrapolate_val(low_hi_c,low_low_c,hi_col2,low_col2,col2_val)

    if debug == True:
        print hi_b
        print low_b
        print "-" * 11
    
    #use A to interpolate interpolated interpolated D's
    interpolated_d = extrapolate_val(hi_b,low_b,hi_col1,low_col1,col1_val)
    if debug == True:
        print interpolated_d
    return interpolated_d
#enddef

#------------------------------------------------------------------------------
# calc RSDD - room surface dirt depreciation
# need to get ltype_d from luminaire info
#------------------------------------------------------------------------------
def get_rsdd(settings, luminaire_id, time, dirtiness, room_CR):
    ltype = get_lighting_type(settings,luminaire_id)
    
    x = get_luminaire_dirt_dep(settings, luminaire_id, time, dirtiness) #x is LDD for maint_cat V, which is same func and parameters for calc RSDD
    dirtiness_per = 100 - (x * 100)                                     #convert x into percent

    RSDD = interpolate_three(settings,'rsdd','rsdd','ltype','direct','expect_dirt_depr',dirtiness_per,'rcr',room_CR)
    RSDD = float('{0:.2f}'.format(RSDD))
    
    debug = settings.getboolean('system','debug')
    if debug == True:
        print "Light Type : " + ltype
        print "% dirt depr: " + str(dirtiness_per)
        print "RSDD       : " + str(RSDD)
    #endif
    
    return RSDD
#enddef

#TODO make this work
def interpolate_four(settings, table, peff_ceil, peff_floor, peff_wall, RCR): #TODO make this generic
    [hi_floor, low_floor] = get_ends(settings, table, 'eff_floor', peff_floor)

    val1 = interpolate_three(settings, table, 'mf','ceil',peff_ceil,'wall',peff_wall,'cavity_ratio',RCR,'eff_floor',hi_floor) 
    val2 = interpolate_three(settings, table, 'mf','ceil',peff_ceil,'wall',peff_wall,'cavity_ratio',RCR,'eff_floor',low_floor) 

    val3 = extrapolate_val(val1,val2,hi_floor,low_floor,peff_floor)
    

    debug = settings.getboolean('system','debug')
    if debug == True:
        print "Debug interpolate four:"
        print "hi_floor :" + str(hi_floor)
        print "low_floor:" + str(low_floor)
        print "peff_ceil:" + str(peff_ceil)
        print "peff_wall:" + str(peff_wall)
        print "RCR      :" + str(RCR)
        print "val1     :" + str(val1)
        print "val2     :" + str(val2)
        print "val3     :" + str(val3)
    #endif

    return val3
        
#enddef

#TODO almost the same as interpolate 3
def get_floor_mf_aux(settings,table,res_col,col1,col1_val,col2,col2_val,col3,col3_val,col4='',col4_val=''):
    #A
    [hi_col1, low_col1] = get_ends(settings, table, col1, col1_val)
    #B
    [hi_col2, low_col2] = get_ends(settings, table, col2, col2_val, col1, low_col1)
    #C
    [hi_col3, low_col3] = get_ends(settings, table, col3, col3_val)
    #E
    #[hi_col4, low_col4] = get_ends(settings, table, col4, col4_val)
    
    debug = settings.getboolean('system','debug')
    if debug == True:
        print table
        print hi_col1, low_col1
        print hi_col2, low_col2
        print hi_col3, low_col3
#        print hi_col4, low_col4
    #endif
    
    #get Ds to interpolate
    if col4 == '':
        SQL = """SELECT {res_col} FROM {table} WHERE {col1} = ? AND {col2} = ? AND {col3} = ?"""
        SQL = SQL.format(res_col=res_col,table=table,col1=col1,col2=col2,col3=col3)
    else:
        SQL = """SELECT {res_col} FROM {table} WHERE {col1} = ? AND {col2} = ? AND {col3} = ? AND {col4} = ?"""
        SQL = SQL.format(res_col=res_col,table=table,col1=col1,col2=col2,col3=col3,col4=col4)        
    #endif

    hihihi   = interpolate_three_get_d(settings, SQL,hi_col1,hi_col2,hi_col3,col4_val)
    hihilow  = interpolate_three_get_d(settings, SQL,hi_col1,hi_col2,low_col3,col4_val)
    hilowhi  = interpolate_three_get_d(settings, SQL,hi_col1,low_col2,hi_col3,col4_val)
    hilowlow = interpolate_three_get_d(settings, SQL,hi_col1,low_col2,low_col3,col4_val)
    hilowhi  = interpolate_three_get_d(settings, SQL,hi_col1,low_col2,hi_col3,col4_val)
    lowhihi  = interpolate_three_get_d(settings, SQL,low_col1,hi_col2,hi_col3,col4_val)
    lowhilow = interpolate_three_get_d(settings, SQL,low_col1,hi_col2,low_col3,col4_val)
    lowlowhi = interpolate_three_get_d(settings, SQL,low_col1,low_col2,hi_col3,col4_val)
    lowlowlow= interpolate_three_get_d(settings, SQL,low_col1,low_col2,low_col3,col4_val)

    if debug == True:
        print hihihi
        print hihilow
        print hilowhi
        print hilowlow
        print lowhihi
        print lowhilow
        print lowlowhi
        print lowlowlow
        print "-" * 11
    
    #use C to interpolate D's
    hi_hi_c   = extrapolate_val(hihihi,hihilow,hi_col3,low_col3,col3_val)
    hi_low_c  = extrapolate_val(hilowhi,hilowlow,hi_col3,low_col3,col3_val)
    low_hi_c  = extrapolate_val(lowhihi,lowhilow,hi_col3,low_col3,col3_val)
    low_low_c = extrapolate_val(lowlowhi,lowlowlow,hi_col3,low_col3,col3_val)

    if debug == True:
        print hi_hi_c
        print hi_low_c
        print low_hi_c
        print low_low_c
        print "-" * 11
    
    #use B to interpolate interpolated D's
    hi_b  = extrapolate_val(hi_hi_c,hi_low_c,hi_col2,low_col2,col2_val)
    low_b = extrapolate_val(low_hi_c,low_low_c,hi_col2,low_col2,col2_val)

    if debug == True:
        print hi_b
        print low_b
        print "-" * 11
    
    #use A to interpolate interpolated interpolated D's
    interpolated_d = extrapolate_val(hi_b,low_b,hi_col1,low_col1,col1_val)
    if debug == True:
        print interpolated_d
    return interpolated_d
#end


def get_floor_mf(settings, peff_ceil, peff_floor, peff_wall, RCR):
    table = 'floor_mf'
    [hi_floor, low_floor] = get_ends(settings, table, 'eff_floor', peff_floor)

    val1 = get_floor_mf_aux(settings, table, 'mf','ceil',peff_ceil,'wall',peff_wall,'cavity_ratio',RCR,'eff_floor',hi_floor) 
    val2 = get_floor_mf_aux(settings, table, 'mf','ceil',peff_ceil,'wall',peff_wall,'cavity_ratio',RCR,'eff_floor',low_floor) 

    MF = extrapolate_val(val1,val2,hi_floor,low_floor,peff_floor)

    debug = settings.getboolean('system','debug')
    if debug == True:
        print "Debug floor_mf:"
        print "hi_floor :" + str(hi_floor)
        print "low_floor:" + str(low_floor)
        print "peff_ceil:" + str(peff_ceil)
        print "peff_wall:" + str(peff_wall)
        print "RCR      :" + str(RCR)
        print "val1     :" + str(val1)
        print "val2     :" + str(val2)
        print "MF       :" + str(MF)
    #endif

    MF = float('{0:.3f}'.format(MF))

    debug = settings.getboolean('system','debug')
    if debug == True:
        print "eff_ceil : " + str(peff_ceil)
        print "wall     : " + str(peff_wall)
        print "RCR      : " + str(RCR)
        print "eff_floor: " + str(peff_floor)
        print "MF       : " + str(MF)
    #endif
       
    return MF
#enddef

#------------------------------------------------------------------------------
# How many luminaires we need
#------------------------------------------------------------------------------
def get_num_luminaires(settings,avg_illum_fc, r_length, r_width, total_lumens_per_luminaire, coeff_util, MF, LLD, LDD, RSDD):
    org_num_luminaires = (avg_illum_fc * r_length * r_width)/(total_lumens_per_luminaire * coeff_util * MF * LLD * LDD * RSDD)
    num_luminaires     = int(round(org_num_luminaires))
    debug = settings.getboolean('system','debug')
    if debug == True:
        print org_num_luminaires
        print num_luminaires
    #endif

    return num_luminaires

#------------------------------------------------------------------------------
# how far apart these lamps can be spaced (in feet)
#------------------------------------------------------------------------------
def get_max_spacing(settings, ltype, h_room_cav):
    max_s_mh = get_max_s_h(settings, ltype)
    max_s    = max_s_mh * h_room_cav
    max_s    = float('{0:.2f}'.format(max_s))
    max_s_ft = int(max_s)
    max_s_in = int((max_s - max_s_ft) * 12) 
    return [max_s_ft,max_s_in]
#enddef


#------------------------------------------------------------------------------
# here is the main calculation routine
#------------------------------------------------------------------------------
def lighting_calc(settings, project):    
    print "=" * 80
    print "    ROOM DESCRIPTION"
    print "=" * 80

    #room name describes the type/usage which determines the needed illumination in (ft cd)
    room_name   = project.get('Location', 'room_name')
    avg_illum_fc= project.getfloat('Location', 'avg_illum_fc')
    print room_name + ", needs " + str(avg_illum_fc) + " ft candles"

    #dimensions of the room
    r_shape     = project.get('Dimensions', 'shape')
    if r_shape == 'rect':
        r_length    = project.getfloat('Dimensions', 'length')
        r_width     = project.getfloat('Dimensions', 'width')
        r_height    = project.getfloat('Dimensions', 'height')
        print "Dimensions:   L:" + str(r_length)   + "  W:"   + str(r_width)    + "  H:"   + str(r_height)
        r_perimeter = 2 * (r_length + r_width)
        r_area      = r_length * r_width

    #add an elsif and calculate the perimeter and area for this shape room
    else:
        print "Calculations for Room shape " + r_shape + " not done yet...quitting."
        sys.exit()
    #endif


    #ceil cavity is distance above lights to ceiling
    #floor cavity is distance below work plane to floor
    #room cavity is what is left over
    h_ceil_cav  = project.getfloat('Cavities', 'h_ceil_cav')
    h_floor_cav = project.getfloat('Cavities', 'h_floor_cav')
    h_room_cav  = r_height - (h_ceil_cav + h_floor_cav)
    print "Cavity Ratio: HCC:" + str(h_ceil_cav) + " HRC:" + str(h_room_cav) + " HFC:" + str(h_floor_cav)

    #reflectances are either measured or determined from paint cards (Lowes Sherien-Williams)
    #some other options are described in Table A on GSA sheet
    refl_ceil   = project.getfloat('Reflectance', 'r_ceiling')
    refl_wall   = project.getfloat('Reflectance', 'r_wall')
    refl_floor  = project.getfloat('Reflectance', 'r_floor')
    print "Relectance:   pC:" + str(refl_ceil) + " pW:" + str(refl_wall) + " pF:" + str(refl_floor)

    #calculate the cavity ratio (how square or rectangular the room is)
    ceil_CR  = calc_cavity_ratio(r_perimeter, r_area, h_ceil_cav)
    room_CR  = calc_cavity_ratio(r_perimeter, r_area, h_room_cav)
    floor_CR = calc_cavity_ratio(r_perimeter, r_area, h_floor_cav)
    print "CCR: " + str(ceil_CR)
    print "RCR: " + str(room_CR)
    print "FCR: " + str(floor_CR)

    #describe the luminaire information and output
    luminaire_id      = project.get('Luminaire', 'luminaire_id')
    luminaire_mfg     = project.get('Luminaire', 'mfg')
    luminaire_cat_num = project.get('Luminaire', 'cat_num')
    luminaire_descr = get_luminaire_description(settings, luminaire_id)
    num_lamps       = project.getfloat('Luminaire', 'num_lamps')   
    lumens_per_lamp = project.getfloat('Lamp', 'lumens_per_lamp')
    LLD             = project.getfloat('Lamp', 'lamp_lumens_deprecation')
    total_lumens_per_luminaire = num_lamps * lumens_per_lamp    
    print "Luminaire Description:  " + luminaire_descr + ", " + str(num_lamps) + " lamps"
    print "Lumens/lamp:            " + str(lumens_per_lamp)
    print "Total Lumens/Luminaire: " + str(total_lumens_per_luminaire)
    print ""

    print "=" * 80
    
    print "----- Doing calcs ----"    
    eff_ceil_cav_ref  = get_effective_base_refl(settings, refl_ceil,  refl_wall, ceil_CR)
    eff_floor_cav_ref = get_effective_base_refl(settings, refl_floor, refl_wall, floor_CR)
    print "Eff Ceil Cav Refl:  " + str(eff_ceil_cav_ref)
    print "Eff Floor Cav Refl: " + str(eff_floor_cav_ref)
    print "-" * 20
    print ""

    print "Getting Coeff Util using (" + luminaire_id + ", " + str(eff_ceil_cav_ref) + ", " + str(refl_wall) + ", " + str(room_CR) +")"
    coeff_util = get_coeff_util(settings, luminaire_id, eff_ceil_cav_ref, refl_wall, room_CR)
    print "CU: " + str(coeff_util)

    print "Got Lamp Lumen Depreciation from reading project file:"
    print "LLD: " + str(LLD)

    print "Getting Luminaries Dirt Depreciation"
    dirtiness = project.get('Location', 'dirtiness')
    time      = project.getfloat('Location','years_before_clean')
    LDD       = get_luminaire_dirt_dep(settings, luminaire_id, time, dirtiness)
    print "LDD: " + str(LDD)

    print "Getting Floor Multiplying Factor"
    MF   = get_floor_mf(settings, eff_ceil_cav_ref, eff_floor_cav_ref, refl_wall, room_CR)
    print "MF: " + str(MF)
    
    print "Getting Room Surface Dirt Depreciation"
    RSDD = get_rsdd(settings, luminaire_id, time, dirtiness, room_CR)
    print "RSDD: " + str(RSDD)

    #-----------------------------------------------------
    #This output is the whole reason for doing these calcs
    #-----------------------------------------------------
    print "=" * 80    
    num_luminaires = get_num_luminaires(settings,avg_illum_fc, r_length, r_width, total_lumens_per_luminaire, coeff_util, MF, LLD, LDD, RSDD)
                                        
    print "Need " + str(num_luminaires) + " Mfg:" + str(luminaire_mfg) + " CatNum:" + str(luminaire_cat_num) + " luminaires in the " + room_name

    [max_s_ft, max_s_in] = get_max_spacing(settings, luminaire_id, h_room_cav) #in ft
    print "These should be spaced NO FURTHER THAN " + str(max_s_ft) + "ft " + str(max_s_in) + "in APART"    
    print "=" * 80
    return
#endfunc

#-----------------------------------------------------
#Validate the project data to make sure it's all good
#-----------------------------------------------------
def validate_input(project):
    error = ''

    for section in project.sections():
        for (key, val) in project.items(section):
            if section == 'Location':
                if key == 'room_name':
                    #no test defined, anything is OK
                    #in future could have this get FC based on input
                    a = 1
                elif key == 'avg_illum_fc':
                    val = project.getfloat(section, key)
                    if val < 0 or 500 < val:
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                        
                elif key == 'dirtiness':
                    if (val == 'very_clean' or 
                        val == 'clean' or 
                        val == 'medium' or 
                        val == 'dirty' or 
                        val == 'very_dirty'):
                        a = 1
                    else:
                        error='val-' + val + ' is not a valid input for ' + key
                        break
                    #endif
                elif key == 'years_before_clean':
                    val = project.getfloat(section, key)
                    if val < 0.0 or 48.0 < val:
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                else:
                    error='key-' + key
                    break
                #endif
            elif section == 'Dimensions':
                if (key == 'length' or
                    key == 'width' or
                    key == 'height'):
                    val = project.getfloat(section, key)
                    if val < 0 :
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                elif key == 'shape':
                    if val != 'rect':
                        error='val-' + val + ' is not a valid input for ' + key
                        break
                    #endif
                else:
                    error='key-' + key
                    break
                #endif
            elif section == 'Cavities':
                if (key == 'h_ceil_cav' or
                    key == 'h_floor_cav'):
                    val = project.getfloat(section, key)
                    if val < 0 :
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                else:
                    error='key-' + key
                    break
                #endif
            elif section == 'Reflectance':
                if (key == 'r_ceiling' or
                    key == 'r_wall' or
                    key == 'r_floor'):
                    val = project.getfloat(section, key)
                    if val < 0 :
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                else:
                    error='key-' + key
                    break
                #endif
            elif section == 'Luminaire':
                if (key == 'luminaire_id'):
                    val = project.getint(section, key)
                    if val not in (1,3,5,38):
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                elif (key == 'mfg' or key =='cat_num'):
                    a = 1
                elif (key == 'num_lamps'):
                    val = project.getint(section, key)
                    if val < 0:
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                else:
                    error='key-' + key
                    break
                #endif
            elif section == 'Lamp':
                #this should be a table in the database at some point
                if (key == 'ltype'):
                    a = 1
                elif(key == 'color'):
                    a = 1
                elif(key == 'lumens_per_lamp'):
                    val = project.getfloat(section, key)
                    if val < 0:
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                elif(key == 'lamp_lumens_deprecation'):
                    val = project.getfloat(section, key)
                    if val < 0:
                        error='val-' + str(val) + ' is not a valid input for ' + key
                        break
                    #endif
                else:
                    error='key-' + key
                    break
                #endif
            else:
                error = 'section-'+section
                break
            #endif
        #endfor
        if error != '':
            break
        #endif
    #endfor

    if error != '':
        #aerror = key.split('-')
        #print 'Error: ' + aerror[0] + ' (' + aerror[1] + ') not defined, come edit project configuration.'
        print error
        sys.exit()
    #endif

#enddef

#ignore this for now
def call_calc(project_name):
    #read the system settings file (maybe should be in own module - along w/ get_database name)
    settings      = ConfigParser.SafeConfigParser()
    settings_file = os.path.abspath('system_settings.txt')    
    settings.read(settings_file)
    
    project = ConfigParser.SafeConfigParser()
    project_file = os.path.abspath(project_name)
    project.read(project_file)
    
    lighting_calc(settings, project)
        
    sys.exit()
#end call_calc    



#-------------------------------------------------------------
#   STANDALONE HERE 
#-------------------------------------------------------------
if __name__ == '__main__':
    print "doing this standalone"

    if len(sys.argv) != 2:
        print "provide project name: projects/office.txt"
        sys.exit()
    #endif
    project_name = sys.argv[1]   

    #read the system settings file (maybe should be in own module - along w/ get_database name)
    settings      = ConfigParser.SafeConfigParser()
    settings_file = os.path.abspath('system_settings.txt')    
    settings.read(settings_file)
    
    project      = ConfigParser.SafeConfigParser()
    project_file = os.path.abspath(project_name)
    project.read(project_file)

    #validate_input
    validate_input(project)

    #main code/work done in here
    lighting_calc(settings, project)
        
    sys.exit()
#endif
